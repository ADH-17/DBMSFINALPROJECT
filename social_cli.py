import argparse
import psycopg
import sys
import os 
from datetime import datetime
from dotenv import load_dotenv 

# Load environment variables from .env file FIRST
load_dotenv()

DB_NAME = os.getenv("DB_NAME", "social_db")
DB_USER = os.getenv("DB_USER", "ayden")
DB_PASSWORD = os.getenv("DB_PASSWORD") 
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_db_connection():
    """Establishes a connection to the PostgreSQL database using .env vars."""
    if not DB_PASSWORD:
        print("Error: DB_PASSWORD is not set. Check your .env file.")
        sys.exit(1)

    try:
        conn = psycopg.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        sys.exit(1)


def get_user_id_by_username(cursor, username):
    """Retrieves a user ID based on their username."""
    cursor.execute("SELECT user_id FROM user WHERE username = %s;", (username,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return None

def create_user_if_not_exists(cursor, username, email, password_hash="dummyhash"):
    """Helper to ensure a user exists for testing posts."""
    user_id = get_user_id_by_username(cursor, username)
    if not user_id:
        print(f"User '{username}' not found. Creating a new user.")
        try:
            cursor.execute(
                "INSERT INTO user (username, email, password_hash, streak) VALUES (%s, %s, %s, 0) RETURNING user_id;",
                (username, email, password_hash)
            )
            user_id = cursor.fetchone()[0]
        except psycopg.errors.UniqueViolation:
            print(f"Email {email} already in use. Cannot create user.")
            return None
    return user_id

def list_drafts(cursor, user_id):
    """Lists unpublished posts for a user."""
    print(f"\n--- Your Drafts ---")
    cursor.execute(
        "SELECT post_id, description, created_at FROM post WHERE user_id = %s AND is_published = FALSE ORDER BY created_at DESC;",
        (user_id,)
    )
    drafts = cursor.fetchall()
    if not drafts:
        print("You have no saved drafts.")
        return

    for post_id, description, created_at in drafts:
        snippet = description[:50] + ('...' if len(description) > 50 else '')
        print(f"ID: {post_id} | Created: {created_at.strftime('%Y-%m-%d %H:%M')} | Desc: '{snippet}'")

def create_or_save_draft(cursor, user_id, description, image_paths, is_published=False):
    """Inserts a new post as a draft or published post."""
    print(f"Saving new post {'as published' if is_published else ' as draft'}...")

    cursor.execute(
        "INSERT INTO post (user_id, description, is_published) VALUES (%s, %s, %s) RETURNING post_id;",
        (user_id, description, is_published)
    )
    post_id = cursor.fetchone()[0]

    # Handle photos 
    if image_paths:
        photo_records = [(post_id, path) for path in image_paths]
        cursor.executemany(
            "INSERT INTO photo (post_id, image_path) VALUES (%s, %s);",
            photo_records
        )
        print(f"Added {len(image_paths)} photos to post {post_id}.")
    
    status = "Published" if is_published else "Draft saved"
    print(f"{status}. Post ID: {post_id}")
    return post_id

def publish_draft(cursor, post_id, user_id):
    """Updates an existing draft to be published."""
    print(f"Attempting to publish draft ID: {post_id}...")
    cursor.execute(
        "UPDATE post SET is_published = TRUE, created_at = NOW() WHERE post_id = %s AND user_id = %s AND is_published = FALSE RETURNING post_id;",
        (post_id, user_id)
    )
    if cursor.fetchone():
        print(f"Successfully published draft ID {post_id}.")
    else:
        print(f"Error: Draft ID {post_id} not found, already published, or doesn't belong to you.")

def delete_draft(cursor, post_id, user_id):
    """Deletes an existing draft (which cascades to photos)."""
    print(f"Attempting to delete draft ID: {post_id}...")
    cursor.execute(
        "DELETE FROM post WHERE post_id = %s AND user_id = %s AND is_published = FALSE RETURNING post_id;",
        (post_id, user_id)
    )
    if cursor.fetchone():
        print(f"Successfully deleted draft ID {post_id} (and associated photos).")
    else:
        print(f"Error: Draft ID {post_id} not found, already published, or doesn't belong to you.")

def main():
    parser = argparse.ArgumentParser(description="Social Media CLI Tool for Ayden's DB.")
    
    parser.add_argument('--user', required=True, help="The username of the actor (e.g., 'ayden').")
    
    subparsers = parser.add_subparsers(dest='command', required=True)

    #  'post' command
    post_parser = subparsers.add_parser('post', help='Manage posts and drafts.')
    post_subparsers = post_parser.add_subparsers(dest='post_command', required=True)

    # post create
    create_parser = post_subparsers.add_parser('create', help='Create a new post or save a draft.')
    create_parser.add_argument('--description', type=str, required=True, help='The body text of the post.')
    create_parser.add_argument('--photos', nargs='*', help='List of image paths (space separated).')
    create_parser.add_argument('--publish', action='store_true', help='Immediately publish the post instead of saving as a draft.')

    # post list
    post_subparsers.add_parser('list-drafts', help='List all unpublished drafts for the user.')

    # post publish
    publish_parser = post_subparsers.add_parser('publish-draft', help='Publish an existing draft by ID.')
    publish_parser.add_argument('--post-id', type=int, required=True, help='The ID of the draft to publish.')
    
    # post delete
    delete_parser = post_subparsers.add_parser('delete-draft', help='Delete an existing draft by ID.')
    delete_parser.add_argument('--post-id', type=int, required=True, help='The ID of the draft to delete.')

    args = parser.parse_args()
    
    # Handle DB interaction
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Ensure user exists first. 
            acting_user_id = get_user_id_by_username(cur, args.user)
            if not acting_user_id:
                print(f"Error: User '{args.user}' not found. Please create the user first or check the username.")
                sys.exit(1)

            if args.command == 'post':
                if args.post_command == 'create':
                    create_or_save_draft(
                        cur,
                        acting_user_id,
                        args.description,
                        args.photos,
                        args.publish
                    )
                elif args.post_command == 'list-drafts':
                    list_drafts(cur, acting_user_id)
                elif args.post_command == 'publish-draft':
                    publish_draft(cur, args.post_id, acting_user_id)
                elif args.post_command == 'delete-draft':
                    delete_draft(cur, args.post_id, acting_user_id)
        
        # Commit 
        conn.commit()

if __name__ == "__main__":
    main()
