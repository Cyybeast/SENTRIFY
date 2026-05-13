from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from database import init_db

app = Flask(__name__)
app.secret_key = 'sentrify-secret-2024'

ADMIN_PASSWORD = 'admin123'

init_db()

def log_result(email):
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('INSERT INTO results (campaign_id, email) VALUES (?, ?)', (1, email))
    conn.commit()
    conn.close()

def get_results():
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('SELECT email, clicked_at FROM results ORDER BY clicked_at DESC')
    rows = c.fetchall()
    conn.close()
    return rows

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/capture', methods=['POST'])
def capture():
    email = request.form.get('email')
    log_result(email)
    return render_template('busted.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('admin_login.html', error='Wrong password')
    return render_template('admin_login.html', error=None)

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    results = get_results()
    total = len(results)
    return render_template('dashboard.html', results=results, total=total)

app.jinja_env.globals['enumerate'] = enumerate
app.run(debug=True)
