from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
DB_PATH = os.getenv("DB_PATH", "orders.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_card TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            item TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'جديد',
            response TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def index():
    success = False
    if request.method == "POST":
        id_card = request.form.get("id_card", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        item = request.form.get("item", "").strip()
        if all([id_card, first_name, last_name, phone, address, item]):
            conn = get_conn()
            conn.execute(
                "INSERT INTO orders (id_card, first_name, last_name, phone, address, item, status, response, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (id_card, first_name, last_name, phone, address, item, "جديد", None, datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
            conn.close()
            success = True
        else:
            success = False
    return render_template("index.html", success=success)

@app.route("/admin", methods=["GET"])
def admin():
    conn = get_conn()
    cur = conn.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cur.fetchall()
    conn.close()
    return render_template("admin.html", orders=orders)

@app.route("/respond/<int:order_id>", methods=["POST"])
def respond(order_id):
    status = request.form.get("status", "قيد المعالجة")
    response = request.form.get("response", "").strip()
    conn = get_conn()
    conn.execute("UPDATE orders SET status = ?, response = ? WHERE id = ?", (status, response, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
