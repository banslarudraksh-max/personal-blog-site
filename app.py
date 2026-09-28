import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "super_secure_blog_secret_key"
DATABASE = "blog.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM posts")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO posts (title, content, created_at)
                VALUES (?, ?, ?)
            """, (
                "Welcome to My Personal Blog",
                "This is the beginning of my personal blog. Here I document my journey, learnings, thoughts, and technical explorations. Stay tuned for exciting stories!",
                datetime.now().strftime("%B %d, %Y")
            ))
            conn.commit()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Kripya pehle Admin Login karein.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# 1. Home
@app.route("/")
def home():
    with get_db() as conn:
        posts = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    return render_template("index.html", posts=posts)

# 2. View Post
@app.route("/post/<int:post_id>")
def post_detail(post_id):
    with get_db() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        flash("Post nahi mili!", "error")
        return redirect(url_for("home"))
    return render_template("post.html", post=post, mode="view")

# 3. Create Post
@app.route("/create", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if title and content:
            created_at = datetime.now().strftime("%B %d, %Y")
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO posts (title, content, created_at) VALUES (?, ?, ?)",
                    (title, content, created_at)
                )
                conn.commit()
            flash("Post successfully publish ho gayi!", "success")
            return redirect(url_for("home"))
        else:
            flash("Title aur Content bharna zaroori hai.", "error")
    return render_template("post.html", mode="create", post=None)

# 4. Edit Post
@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    conn = get_db()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        flash("Post nahi mili!", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if title and content:
            conn.execute("UPDATE posts SET title = ?, content = ? WHERE id = ?", (title, content, post_id))
            conn.commit()
            conn.close()
            flash("Post update ho gayi!", "success")
            return redirect(url_for("post_detail", post_id=post_id))
        else:
            flash("Title aur Content khali nahi ho sakte.", "error")

    conn.close()
    return render_template("post.html", mode="edit", post=post)

# 5. Delete Post
@app.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    with get_db() as conn:
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
    flash("Post delete ho gayi!", "info")
    return redirect(url_for("home"))

# 6. Admin Login Route (Ye missing tha)
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if username == "admin" and password == "admin123":
            session["logged_in"] = True
            flash("Admin login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Galat ID ya Password! Use: admin / admin123", "error")
            
    return render_template("login.html")

# 7. Logout Route
@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("Aap logout ho chuke hain.", "info")
    return redirect(url_for("home"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
