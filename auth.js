import jwt from "jsonwebtoken";
import bcrypt from "bcryptjs";
import dotenv from "dotenv";
dotenv.config();

export const hash = (pw) => bcrypt.hash(pw, 10);
export const check = (pw, hash) => bcrypt.compare(pw, hash);

export function token(user) {
  return jwt.sign(
    { user_id: user.user_id, username: user.username },
    process.env.JWT_SECRET,
    { expiresIn: "7d" }
  );
}

export function requireAuth(req, res, next) {
  const header = req.headers.authorization || "";
  const t = header.startsWith("Bearer ") ? header.slice(7) : null;
  if (!t) return res.status(401).json({ error: "Missing token" });

  try {
    req.user = jwt.verify(t, process.env.JWT_SECRET);
    next();
  } catch {
    return res.status(401).json({ error: "Invalid token" });
  }
}
