from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
import datetime
import os

app = Flask(__name__)
DB_NAME = "orders.db"
app.secret_key = os.environ.get("APP_SECRET_KEY", "dev-key")

# تهيئة قاعدة البيانات
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  first_name TEXT,
                  last_name TEXT,
                  card_id TEXT,
                  phone TEXT,
                  order_type TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  is_read INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# محاكاة إرسال رسالة نصية
def send_sms_notification(name, phone):
    # في الواقع، هنا نستخدم API مثل Twilio
    # مثال: client.messages.create(to=owner_phone, from_=twilio_number, body=...)
    print(f"\n[SMS SENT] تنبيه لمدير المحل: طلبية جديدة من {name} (هاتف: {phone})")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_order():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        card_id = request.form['card_id']
        phone = request.form['phone']
        order_type = request.form['order_type']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO orders (first_name, last_name, card_id, phone, order_type) VALUES (?, ?, ?, ?, ?)",
                  (first_name, last_name, card_id, phone, order_type))
        conn.commit()
        conn.close()

        # إرسال التنبيه
        send_sms_notification(f"{first_name} {last_name}", phone)

        return redirect(url_for('index', success=1))

@app.route('/admin')
def admin():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # جلب الطلبات الأحدث أولاً
    c.execute("SELECT * FROM orders ORDER BY timestamp DESC")
    orders = c.fetchall()
    conn.close()
    return render_template('admin.html', orders=orders)

@app.route('/admin_login', methods=['GET', 'POST'])
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        pwd = request.form.get('password', '')
        expected = os.environ.get('ADMIN_PASSWORD', '198619')
        if pwd == expected:
            session['admin'] = True
            return redirect(url_for('admin'))
        return render_template('login.html', error="كلمة المرور غير صحيحة")
    return render_template('login.html', error=None)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/api/check_new', methods=['GET'])
def check_new():
    # هذه الدالة يمكن استخدامها للتحقق من وجود طلبات جديدة غير مقروءة
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders WHERE is_read = 0")
    count = c.fetchone()[0]
    conn.close()
    return jsonify({'new_orders': count})

@app.route('/api/mark_read', methods=['POST'])
def mark_read():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE orders SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.before_first_request
def _ensure_db():
    init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
