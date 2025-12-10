DROP TABLE IF EXISTS 
  friend_requests,
  friend,
  likes,
  comment,
  photo,
  post,
  research,
  groups,
  users
CASCADE;

-- USERS
CREATE TABLE users (
  user_id        SERIAL PRIMARY KEY,
  username       VARCHAR(40) UNIQUE NOT NULL,
  email          VARCHAR(40) UNIQUE NOT NULL,
  password_hash  VARCHAR(255) NOT NULL,
  streak         INT NOT NULL CHECK(streak >= 0)
);

-- POSTS  (supports drafts via is_published)
CREATE TABLE post (
  post_id       SERIAL PRIMARY KEY,
  user_id       INT NOT NULL REFERENCES users(user_id),
  description   TEXT,
  created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
  is_published  BOOLEAN NOT NULL DEFAULT FALSE
);

-- PHOTOS for posts
CREATE TABLE photo (
  photo_id      SERIAL PRIMARY KEY,
  post_id       INT NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
  image_path    VARCHAR(255) NOT NULL
);

-- COMMENTS
CREATE TABLE comment (
  comment_id    SERIAL PRIMARY KEY,
  created_by    INT NOT NULL REFERENCES users(user_id),
  post_id       INT NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
  visible       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
  body          TEXT NOT NULL
);

-- RESEARCH PAPERS
CREATE TABLE research (
  paper_id  SERIAL,
  title     VARCHAR(100) NOT NULL,
  author    VARCHAR(40) NOT NULL,
  url       VARCHAR(255) NOT NULL,
  tag       VARCHAR(40) NOT NULL,
  PRIMARY KEY (paper_id)
);

-- FRIENDS (mutual connection)
CREATE TABLE friend (
  user_id_1 INT NOT NULL REFERENCES users(user_id),
  user_id_2 INT NOT NULL REFERENCES users(user_id),
  is_friend BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (user_id_1, user_id_2)
);

-- LIKES (junction between users and posts)
CREATE TABLE likes (
  user_id  INT NOT NULL REFERENCES users(user_id),
  post_id  INT NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
);

-- FRIEND REQUESTS

CREATE TABLE friend_requests (
  user_id_one INT NOT NULL REFERENCES users(user_id),
  user_id_two INT NOT NULL REFERENCES users(user_id),
  send_time   TIMESTAMP NOT NULL DEFAULT NOW(),
  status      VARCHAR(20) NOT NULL DEFAULT 'Pending',
  PRIMARY KEY (user_id_one, user_id_two)
);

-- SUPPORT GROUPS
CREATE TABLE groups (
  group_id    SERIAL PRIMARY KEY,
  group_name  VARCHAR(40) NOT NULL UNIQUE
);

CREATE TABLE group_membership (
  user_id   INT NOT NULL REFERENCES users(user_id),
  group_id  INT NOT NULL REFERENCES groups(group_id),
  PRIMARY KEY (user_id, group_id)
);
