from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

@app.route("/")
def home():
    try:
        con = sqlite3.connect("users.db")
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM warnings")
        count = cur.fetchone()[0]
        cur.execute("SELECT name FROM server_info WHERE id = 1")
        result = cur.fetchone()        
        guild_id = result[0] if result else "No Server Data"
        cur.execute("SELECT latency FROM server_info WHERE id = 1")
        latency = cur.fetchone()[0]
        con.close()
        return render_template("index.html", count=count, guild_id=guild_id, latency=latency)

        
    except Exception as e:
        return f"<h1>Error</h1><p>{e}</p>"

if __name__ == '__main__':
    app.run(debug=True, port=5000)