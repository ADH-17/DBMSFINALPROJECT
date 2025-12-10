import express from "express";
import dotenv from "dotenv";
import { q } from "./db.js";
import { hash, check, token, requireAuth } from "./auth.js";

dotenv.config();
const app = express();
app.use(express.json());

/* ------------------- AUTH ------------------- */
app.post("/register", async (req, res) => {
  const { username, email, password } = req.body;
  const ph = await hash(password);

  const result = await q(
    `INSERT INTO users (username, email, password_hash, streak)
     VALUES ($1,$2,$3,0)
     RETURNING user_id, username`,
    [username, email, ph]
  );

  res.json({ token: token(result.rows[0]) });
});

app.post("/login", async (req, res) => {
  const { email, password } = req.body;
  const r = await q("SELECT * FROM users WHERE email=$1", [email]);
  if (r.rowCount === 0) return res.status(400).json({ error: "No user" });

  const user = r.rows[0];
  const ok = await check(password, user.password_hash);
  if (!ok) return res.status(400).json({ error: "Bad password" });

  res.json({ token: token(user) });
});

/* ------------------- CREATE POST (DRAFT OR PUBLISH) ------------------- */
app.post("/post", requireAuth, async (req, res) => {
  const { description, is_published } = req.body;
  const r = await q(
    `INSERT INTO post (user_id, description, is_published)
     VALUES ($1,$2,$3)
     RETURNING *`,
    [req.user.user_id, description, is_published]
  );
  res.json(r.rows[0]);
});

/* ------------------- ADD PHOTO ------------------- */
app.post("/photo/:post_id", requireAuth, async (req, res) => {
  const { post_id } = req.params;
  const { image_path } = req.body;

  const r = await q(
    `INSERT INTO photo (post_id, image_path)
     VALUES ($1,$2) RETURNING *`,
    [post_id, image_path]
  );
  res.json(r.rows[0]);
});

/* ------------------- LIKE POST ------------------- */
app.post("/like/:post_id", requireAuth, async (req, res) => {
  const { post_id } = req.params;
  await q(
    `INSERT INTO likes (user_id, post_id)
     VALUES ($1,$2) ON CONFLICT DO NOTHING`,
    [req.user.user_id, post_id]
  );
  res.json({ liked: true });
});

/* ------------------- COMMENT ------------------- */
app.post("/comment/:post_id", requireAuth, async (req, res) => {
  const { post_id } = req.params;
  const { body } = req.body;

  const r = await q(
    `INSERT INTO comment (created_by, post_id, body)
     VALUES ($1,$2,$3) RETURNING *`,
    [req.user.user_id, post_id, body]
  );
  res.json(r.rows[0]);
});

/* ------------------- FRIEND REQUEST ------------------- */
app.post("/friend/request/:to_user", requireAuth, async (req, res) => {
  const { to_user } = req.params;

  await q(
    `INSERT INTO friend_requests (user_id_one, user_id_two)
     VALUES ($1,$2)
     ON CONFLICT DO NOTHING`,
    [req.user.user_id, to_user]
  );

  res.json({ sent: true });
});

/* ------------------- ACCEPT FRIEND ------------------- */
app.post("/friend/accept/:from_user", requireAuth, async (req, res) => {
  const { from_user } = req.params;

  // update request
  await q(
    `UPDATE friend_requests
     SET status = 'Accepted'
     WHERE user_id_one=$1 AND user_id_two=$2`,
    [from_user, req.user.user_id]
  );

  // add friendship
  await q(
    `INSERT INTO friend (user_id_1, user_id_2)
     VALUES ($1,$2)
     ON CONFLICT DO NOTHING`,
    [from_user, req.user.user_id]
  );

  res.json({ accepted: true });
});

/* ------------------- JOIN GROUP ------------------- */
app.post("/group/join/:group_id", requireAuth, async (req, res) => {
  const { group_id } = req.params;
  await q(
    `INSERT INTO group_membership (user_id, group_id)
     VALUES ($1,$2)
     ON CONFLICT DO NOTHING`,
    [req.user.user_id, group_id]
  );
  res.json({ joined: true });
});

/* ------------------- SEARCH ------------------- */
app.get("/search", async (req, res) => {
  const qstr = `%${req.query.q || ""}%`;

  const users = await q(
    "SELECT username FROM users WHERE username ILIKE $1",
    [qstr]
  );
  const posts = await q(
    "SELECT description FROM post WHERE description ILIKE $1 AND is_published=TRUE",
    [qstr]
  );
  const papers = await q(
    "SELECT title FROM research WHERE title ILIKE $1",
    [qstr]
  );

  res.json({ users: users.rows, posts: posts.rows, research: papers.rows });
});

/* ------------------- START ------------------- */
app.listen(process.env.PORT, () =>
  console.log("Server running on port", process.env.PORT)
);
