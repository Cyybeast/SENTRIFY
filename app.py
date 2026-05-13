from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import uuid
from database import init_db

app = Flask(__name__)
app.secret_key = 'sentrify-secret-2024'

ADMIN_PASSWORD = 'admin123'

init_db()

def create_campaign(company_name, campaign_name):
    code = str(uuid.uuid4())[:8]
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('INSERT INTO campaigns (company_name, campaign_name, unique_code) VALUES (?, ?, ?)',
              (company_name, campaign_name, code))
    conn.commit()
    conn.close()
    return code

def log_result(campaign_id, email):
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('INSERT INTO results (campaign_id, email) VALUES (?, ?)', (campaign_id, email))
    conn.commit()
    conn.close()

def get_campaign_by_code(code):
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('SELECT id, company_name, campaign_name FROM campaigns WHERE unique_code = ?', (code,))
    row = c.fetchone()
    conn.close()
    return row

def get_all_campaigns():
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('''
        SELECT campaigns.id, campaigns.company_name, campaigns.campaign_name,
               campaigns.unique_code, COUNT(results.id) as clicks
        FROM campaigns
        LEFT JOIN results ON campaigns.id = results.campaign_id
        GROUP BY campaigns.id
        ORDER BY campaigns.created_at DESC
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

def get_results_by_campaign(campaign_id):
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('SELECT email, clicked_at FROM results WHERE campaign_id = ? ORDER BY clicked_at DESC', (campaign_id,))
    rows = c.fetchall()
    conn.close()
    return rows

@app.route('/sim/<code>')
def simulation(code):
    campaign = get_campaign_by_code(code)
    if not campaign:
        return 'Invalid link.', 404
    return render_template('index.html', code=code)

@app.route('/capture/<code>', methods=['POST'])
def capture(code):
    campaign = get_campaign_by_code(code)
    if not campaign:
        return 'Invalid link.', 404
    email = request.form.get('email')
    log_result(campaign[0], email)
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
    campaigns = get_all_campaigns()
    return render_template('dashboard.html', campaigns=campaigns)

@app.route('/dashboard/campaign/<int:campaign_id>')
def campaign_detail(campaign_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    results = get_results_by_campaign(campaign_id)
    total = len(results)
    return render_template('campaign_detail.html', results=results, total=total, campaign_id=campaign_id)

@app.route('/dashboard/create', methods=['GET', 'POST'])
def create():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        company = request.form.get('company_name')
        campaign = request.form.get('campaign_name')
        code = create_campaign(company, campaign)
        link = f"http://127.0.0.1:5000/sim/{code}"
        return render_template('create.html', link=link, success=True)
    return render_template('create.html', success=False)

app.jinja_env.globals['enumerate'] = enumerate
app.run(debug=True)
