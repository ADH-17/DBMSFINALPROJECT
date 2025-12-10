--Ayden Humphries
--321 Bowers
--Final Project

DROP TABLE IF EXISTS users, post, photo, comment

CREATE TABLE users
user_id INT NOT NULL,
username VARCHAR(40) NOT NULL,
email VARCHAR(40) NOT NULL,
password_hash VARCHAR(16) NOT NULL,
streak INT NOT NULL CHECK(streak >= 0),
profile_photo ,
PRIMARY KEY user_id

CREATE TABLE post
post_id INT NOT NULL CHECK(post_id >= 0),
username VARCHAR(40) NOT NULL,
created_at DATE,
is_published BOOLEAN NOT NULL,
likes INT NOT NULL CHECK(likes > 0),
PRIMARY KEY post_id
FOREIGN KEY username REFERENCES 

-- May have to be created before user so user can use it not sure
CREATE TABLE photo
photo_id INT NOT NULL CHECK(photo_id > 0),
image_path VARCHAR(60), -- Not sure the type yet, maybe char? NOT NULL
PRIMARY KEY photo_id

CREATE TABLE comment
user_id INT NOT NULL,
visible BOOLEAN NOT NULL,
created_at DATE NOT NULL,
comment_id INT NOT NULL,
post_id INT NOT NULL,
PRIMARY KEY comment_id
FOREIGN KEY username REFERENCES users(username), post_id REFERENCES post(post_id)

CREATE TABLE research
paper_id INT NOT NULL,
title VARCHAR(40) NOT NULL,
author VARCHAR(40) NOT NULL,
url VARCHAR(40) NOT NULL,
tag VARCHAR(10) NOT NULL,
PRIMARY KEY paper_id, author

CREATE TABLE friend
is_friend BOOLEAN NOT NULL,
usr2 VARCHAR(40) NOT NULL,
usr1 VARCHAR(40) NOT NULL -- Maybe not really sure how this one is going to work yet 
