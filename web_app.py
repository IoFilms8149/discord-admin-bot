from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

@app.route("/")
def home():
    try:
        con = sqlite3.connect("users.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM mod_logs")
        count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM mod_logs WHERE action = 'Warn'")
        warn_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM mod_logs WHERE action = 'Ban'")
        ban_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM mod_logs WHERE action = 'Kick'")
        kick_count = cur.fetchone()[0]
        cur.execute("SELECT name, latency, status, member_count, role_count, date_created FROM server_info WHERE id = 1")
        info = cur.fetchone()        
        guild_id = info["name"] if info else "Unknown Server"
        latency = info["latency"] if info else 0
        status = info["status"] if info else "Offline"
        member_count = info["member_count"] if info else 0
        role_count = info["role_count"] if info else 0
        date_created = info["date_created"] if info else "Error"
        con.close()
        status = "Offline"
        return render_template("index.html", 
                               count=count, 
                               warn_count=warn_count, 
                               kick_count=kick_count, 
                               ban_count=ban_count, 
                               guild_id=guild_id, 
                               latency=latency, 
                               status=status, 
                               member_count=member_count, 
                               role_count=role_count, 
                               date_created=date_created
                               )
    except Exception as e:
        return f"<h1>Error</h1><p>{e}</p>"
@app.route("/logs")
def logs():
    try:
        con = sqlite3.connect("users.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM mod_logs ORDER BY timestamp DESC LIMIT 20")
        logs = cur.fetchall()
        con.close()
        return render_template("logs.html", logs=logs)
    except Exception as e:
        return f"Error loading logs: {e}"
@app.route("/leaderboard")
def leaderboard():
    try:
        con = sqlite3.connect("users.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT username, user_id, level, xp FROM levels ORDER BY level DESC, xp DESC LIMIT 10")
        users = cur.fetchall()
        con.close
        return render_template("leaderboard.html",users=users)
    except Exception as e:
        return f"Error loading leaderboard: {e}"
@app.route("/search", methods =["POST"])
def search():
    user_id = request.form.get("target_id")
    if user_id and user_id.isdigit():
        return redirect(url_for("profile", user_id=user_id))
    return redirect(url_for("index"))
@app.route("/profile/<int:user_id>")
def profile(user_id):
    try:
        con = sqlite3.connect("users.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM levels WHERE user_id = ?", (user_id,))
        user_data = cur.fetchone()
        cur.execute("SELECT action, reason, timestamp FROM mod_logs WHERE user_id = ? ORDER BY rowid DESC LIMIT 5", (user_id,))
        user_logs = cur.fetchall()
        con.close()
        if user_data:
            return render_template("profile.html", 
                                   user_data=user_data, 
                                   user_logs=user_logs
                                   )
        else:
            return "User not found", 404
    except Exception as e:
        return f"Error loading profile: {e}"
if __name__ == '__main__':
    app.run(debug=True, port=5000)