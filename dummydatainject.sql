-- USERS 
INSERT INTO users (username, email, password_hash, streak) VALUES
('ayden', 'ayden@example.com', 'hashed_pw_1', 5),
('bob', 'bob@example.com', 'hashed_pw_2', 3),
('alice', 'alice@example.com', 'hashed_pw_3', 1),
('mark', 'mark@example.com', 'hashed_pw_4', 0);

-- POSTS 
INSERT INTO post (user_id, description, created_at, is_published) VALUES
(1, 'My first post! Hello world!', NOW(), TRUE),
(1, 'Draft test post', NOW(), FALSE),
(2, 'Bob’s public post', NOW(), TRUE),
(3, 'Alice’s published post', NOW(), TRUE);

-- PHOTOS 
INSERT INTO photo (post_id, image_path) VALUES
(1, '/img/post1_pic1.jpg'),
(1, '/img/post1_pic2.jpg'),
(3, '/img/bobPhoto.png');

-- COMMENTS 
INSERT INTO comment (created_by, post_id, visible, body) VALUES
(2, 1, TRUE, 'Nice post Ayden!'),
(3, 1, TRUE, 'Cool!'),
(1, 3, TRUE, 'Awesome Bob!');

-- RESEARCH PAPERS 
INSERT INTO research (title, author, url, tag) VALUES
('Cognitive Load in UI Design', 'Dr. Smith', 'http://paper.com/ui', 'design'),
('Database Indexing Basics', 'Prof. Adams', 'http://paper.com/db', 'database'),
('Social Media Addiction Study', 'Dr. Barnes', 'http://paper.com/social', 'mental'),
('Effects of Screens on Sleep', 'Dr. Karl', 'http://paper.com/sleep', 'health');

-- FRIENDSHIPS 
INSERT INTO friend (user_id_1, user_id_2, is_friend) VALUES
(1, 2, TRUE), 
(1, 3, TRUE); 

-- FRIEND REQUESTS
INSERT INTO friend_requests (user_id_one, user_id_two, send_time, status) VALUES
(4, 1, NOW(), 'Pending');  

-- LIKES 
INSERT INTO likes (user_id, post_id) VALUES
(2, 1),  
(3, 1),  
(1, 3);

-- GROUPS
INSERT INTO groups (group_name) VALUES
('Recovery Group'),
('Study Group'),
('Fitness Group');

-- GROUP MEMBERSHIP 
INSERT INTO group_membership (user_id, group_id) VALUES
(1, 1),  -- Ayden joins Recovery Group
(2, 2),  -- Bob joins Study Group
(3, 3);  -- Alice joins Fitness Group
