import argparse
import psycopg
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file first
load_dotenv()

DB_NAME = os.getenv("DB_NAME", "ahumphries_db")
DB_USER = os.getenv("DB_USER", "ahumphries")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "cps-postgresql.gonzaga.edu")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_db_connection():
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
    cursor.execute("SELECT user_id FROM users WHERE username = %s;", (username,))
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
    print(f"Saving new post {'as published' if is_published else 'as draft'}...")

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


def list_posts_by_likes(cursor, limit=10):
    """
    Lists posts ranked by the number of likes using DENSE_RANK.
    :param cursor: psycopg cursor
    :param limit: number of top-ranked posts to return
    """
    query = """
        SELECT post_id, description, username, like_count, rank
        FROM (
            SELECT
                p.post_id,
                p.description,
                u.username,
                COUNT(l.user_id) AS like_count,
                DENSE_RANK() OVER (ORDER BY COUNT(l.user_id) DESC) AS rank
            FROM post p
            JOIN users u ON p.user_id = u.user_id
            LEFT JOIN likes l ON p.post_id = l.post_id
            WHERE p.is_published = TRUE
            GROUP BY p.post_id, u.username
        ) ranked_posts
        WHERE rank <= %s
        ORDER BY rank, post_id;
    """
    cursor.execute(query, (limit,))
    posts = cursor.fetchall()
    
    if not posts:
        print("No posts found.")
        return
    
    print(f"\n--- Top {limit} Posts by Likes (DENSE_RANK) ---")
    for post_id, description, username, like_count, rank in posts:
        snippet = description[:50] + ("..." if len(description) > 50 else "")
        print(f"Rank: {rank} | Post ID: {post_id} | User: {username} | Likes: {like_count} | Desc: '{snippet}'")

def list_users_by_post_count(cursor, limit=10):
    """Lists users ranked by number of posts (most to least)"""
    cursor.execute("""
        SELECT 
            username, 
            COUNT(p.post_id) AS post_count,
            RANK() OVER (ORDER BY COUNT(p.post_id) DESC) AS rank
        FROM users u
        LEFT JOIN post p ON u.user_id = p.user_id
        GROUP BY u.user_id, u.username
        ORDER BY rank
        LIMIT %s;
    """, (limit,))
    
    rows = cursor.fetchall()
    
    if not rows:
        print("No users found.")
        return

    print(f"\n--- Top {limit} Users by Post Count ---")
    for username, post_count, rank in rows:
        print(f"Rank {rank}: {username} with {post_count} posts")

def list_users_by_avg_likes(cursor, limit=10):
    """
    Lists users ranked by average likes per post.
    :param cursor: psycopg cursor
    :param limit: number of top users to display
    """
    query = """
        SELECT u.username,
               COALESCE(AVG(pl.likes_count), 0) AS avg_likes,
               RANK() OVER (ORDER BY COALESCE(AVG(pl.likes_count), 0) DESC) AS rank
        FROM users u
        LEFT JOIN (
            SELECT p.post_id, p.user_id, COUNT(l.user_id) AS likes_count
            FROM post p
            LEFT JOIN likes l ON p.post_id = l.post_id
            WHERE p.is_published = TRUE
            GROUP BY p.post_id
        ) pl ON u.user_id = pl.user_id
        GROUP BY u.user_id, u.username
        ORDER BY rank
        LIMIT %s;
    """
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    
    if not rows:
        print("No users found.")
        return

    print(f"\n--- Top {limit} Users by Average Likes per Post ---")
    for username, avg_likes, rank in rows:
        print(f"Rank {rank}: {username} with {avg_likes:.2f} average likes per post")

def users_who_like_their_own_posts(cursor):
    query = """
        SELECT u.username, COUNT(*) AS self_likes
        FROM likes l
        JOIN post p ON l.post_id = p.post_id
        JOIN users u ON l.user_id = u.user_id
        WHERE l.user_id = p.user_id
        GROUP BY u.username
        ORDER BY self_likes DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print("\n--- Users Who Like Their Own Posts ---")
    for username, self_likes in rows:
        print(f"{username} liked their own posts {self_likes} times")


def main():
    parser = argparse.ArgumentParser(description="Social Media CLI Tool for Ayden's DB.")
    parser.add_argument('--user', required=True, help="The username of the actor (e.g., 'ayden').")

    subparsers = parser.add_subparsers(dest='command', required=True)

    # 'post' command
    post_parser = subparsers.add_parser('post', help='Manage posts and drafts.')
    post_subparsers = post_parser.add_subparsers(dest='post_command', required=True)

    # post create
    create_parser = post_subparsers.add_parser('create', help='Create a new post or save a draft.')
    create_parser.add_argument('--description', type=str, required=True, help='The body text of the post.')
    create_parser.add_argument('--photos', nargs='*', help='List of image paths (space separated).')
    create_parser.add_argument('--publish', action='store_true', help='Immediately publish the post instead of saving as a draft.')

    # post list drafts
    post_subparsers.add_parser('list-drafts', help='List all unpublished drafts for the user.')

    # post publish
    publish_parser = post_subparsers.add_parser('publish-draft', help='Publish an existing draft by ID.')
    publish_parser.add_argument('--post-id', type=int, required=True, help='The ID of the draft to publish.')

    # post delete
    delete_parser = post_subparsers.add_parser('delete-draft', help='Delete an existing draft by ID.')
    delete_parser.add_argument('--post-id', type=int, required=True, help='The ID of the draft to delete.')

    # top liked posts
    top_liked_parser = post_subparsers.add_parser('top-liked', help='List top posts by likes.')
    top_liked_parser.add_argument('--limit', type=int, default=10, help='Number of top posts to display.')

    # top users by post count
    top_users_parser = post_subparsers.add_parser('top-users', help='List users ranked by number of posts.')
    top_users_parser.add_argument('--limit', type=int, default=10, help='Number of top users to display.')

    # average likes per user
    avg_likes_parser = post_subparsers.add_parser('avg-likes', help='List users ranked by average likes per post.')
    avg_likes_parser.add_argument('--limit', type=int, default=10, help='Number of top users to display.')

    # users who like their own posts
    self_like_parser = post_subparsers.add_parser('self-likes', help="List users who liked their own posts")

    args = parser.parse_args()

    # Handle DB interaction
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Ensure user exists first
            acting_user_id = get_user_id_by_username(cur, args.user)
            if not acting_user_id:
                print(f"Error: User '{args.user}' not found. Please create the user first or check the username.")
                sys.exit(1)

            if args.command == 'post':
                if args.post_command == 'create':
                    create_or_save_draft(cur, acting_user_id, args.description, args.photos, args.publish)
                elif args.post_command == 'list-drafts':
                    list_drafts(cur, acting_user_id)
                elif args.post_command == 'publish-draft':
                    publish_draft(cur, args.post_id, acting_user_id)
                elif args.post_command == 'delete-draft':
                    delete_draft(cur, args.post_id, acting_user_id)
                elif args.post_command == 'top-liked':
                    list_posts_by_likes(cur, args.limit)
                elif args.post_command == 'top-users':
                    list_users_by_post_count(cur, args.limit)
                elif args.post_command == 'avg-likes':
                    list_users_by_avg_likes(cur, args.limit)
                elif args.post_command == 'self-likes':
                    users_who_like_their_own_posts(cur)

        # Commit changes
        conn.commit()
if __name__ == "__main__":
    main()