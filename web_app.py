from flask import Flask, render_template
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
        return render_template("index.html", count=count, guild_id=guild_id, latency=latency, status=status, member_count=member_count, role_count=role_count, date_created=date_created)
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)