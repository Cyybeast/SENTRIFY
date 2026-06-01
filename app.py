from flask import Flask, render_template, request, session, redirect, url_for
from flask_mail import Mail, Message
import sqlite3
import uuid
import csv
import io
from database import init_db

app = Flask(__name__)
app.secret_key = 'sentrify-secret-2024'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sentrify.test@gmail.com'
app.config['MAIL_PASSWORD'] = 'uion ncth wfkt eukn'
app.config['MAIL_DEFAULT_SENDER'] = 'sentrify.test@gmail.com'

mail = Mail(app)

ADMIN_PASSWORD = 'admin123'

TEMPLATES = {
    'opay': {
        'name': 'OPay',
        'subject': 'Action Required: Your OPay Account Has Been Restricted',
        'color': '#3dd6b5',
        'template_file': 'simulations/opay.html'
    },
    'gtbank': {
        'name': 'GTBank',
        'subject': 'Urgent: Verify Your GTBank Internet Banking Account',
        'color': '#e00000',
        'template_file': 'simulations/gtbank.html'
    },
    'mtn': {
        'name': 'MTN Nigeria',
        'subject': 'Important: Your MTN Account Requires Verification',
        'color': '#ffcc00',
        'template_file': 'simulations/mtn.html'
    },
}

# Correct quiz answers
ANSWERS = {'q1': 'b', 'q2': 'b', 'q3': 'b', 'q4': 'c'}

init_db()

def create_campaign(company_name, campaign_name, template):
    code = str(uuid.uuid4())[:8]
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('INSERT INTO campaigns (company_name, campaign_name, unique_code, template) VALUES (?, ?, ?, ?)',
              (company_name, campaign_name, code, template))
    conn.commit()
    conn.close()
    return code

def log_result(campaign_id, email):
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('INSERT INTO results (campaign_id, email) VALUES (?, ?)', (campaign_id, email))
    conn.commit()
    conn.close()

def mark_training_complete(campaign_id, email):
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('UPDATE results SET training_completed = 1 WHERE campaign_id = ? AND email = ?',
              (campaign_id, email))
    conn.commit()
    conn.close()

def get_campaign_by_code(code):
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('SELECT id, company_name, campaign_name, template FROM campaigns WHERE unique_code = ?', (code,))
    row = c.fetchone()
    conn.close()
    return row

def get_all_campaigns():
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('''
        SELECT campaigns.id, campaigns.company_name, campaigns.campaign_name,
               campaigns.unique_code, COUNT(results.id) as clicks, campaigns.template
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
    c.execute('''SELECT email, clicked_at, training_completed
                 FROM results WHERE campaign_id = ?
                 ORDER BY clicked_at DESC''', (campaign_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def send_phishing_email(recipient_email, campaign_code, template_key):
    t = TEMPLATES.get(template_key, TEMPLATES['opay'])
    link = f"http://127.0.0.1:5000/sim/{campaign_code}"
    msg = Message(subject=t['subject'], recipients=[recipient_email])
    msg.html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto;">
        <div style="background: {t['color']}; padding: 30px; text-align: center;">
            <h1 style="color: white; font-size: 28px;">{t['name']}</h1>
        </div>
        <div style="background: white; padding: 30px;">
            <p style="color: #333;">Dear Customer,</p>
            <p style="color: #333;">We detected <strong>3 failed login attempts</strong> on your {t['name']} account. Your account has been temporarily restricted.</p>
            <p style="color: #333;">To restore access, please verify your identity immediately:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{link}" style="background: {t['color']}; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: bold;">Verify My Account</a>
            </div>
            <p style="color: #999; font-size: 12px;">If you did not request this, please ignore this email.</p>
        </div>
        <div style="background: #f5f5f5; padding: 15px; text-align: center;">
            <p style="color: #999; font-size: 11px;">{t['name']} Customer Support</p>
        </div>
    </div>
    """
    mail.send(msg)

@app.route('/sim/<code>')
def simulation(code):
    campaign = get_campaign_by_code(code)
    if not campaign:
        return 'Invalid link.', 404
    template_key = campaign[3]
    template_info = TEMPLATES.get(template_key, TEMPLATES['opay'])
    return render_template(template_info['template_file'], code=code)

@app.route('/capture/<code>', methods=['POST'])
def capture(code):
    campaign = get_campaign_by_code(code)
    if not campaign:
        return 'Invalid link.', 404
    email = request.form.get('email')
    log_result(campaign[0], email)
    session['caught_email'] = email
    session['caught_campaign_id'] = campaign[0]
    return render_template('busted.html', code=code)

@app.route('/training/<code>')
def training(code):
    campaign = get_campaign_by_code(code)
    if not campaign:
        return 'Invalid link.', 404
    return render_template('training.html', code=code)

@app.route('/quiz/<code>', methods=['GET', 'POST'])
def quiz(code):
    campaign = get_campaign_by_code(code)
    if not campaign:
        return 'Invalid link.', 404

    if request.method == 'POST':
        score = 0
        for q, correct in ANSWERS.items():
            if request.form.get(q) == correct:
                score += 1
        passed = score >= 3
        if passed:
            email = session.get('caught_email')
            campaign_id = session.get('caught_campaign_id')
            if email and campaign_id:
                mark_training_complete(campaign_id, email)
        return render_template('complete.html', passed=passed, score=score, code=code)

    return render_template('quiz.html', code=code)

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
    trained = sum(1 for r in results if r[2] == 1)
    return render_template('campaign_detail.html', results=results,
                           total=total, trained=trained, campaign_id=campaign_id)

@app.route('/dashboard/create', methods=['GET', 'POST'])
def create():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        company = request.form.get('company_name')
        campaign = request.form.get('campaign_name')
        template = request.form.get('template', 'opay')
        code = create_campaign(company, campaign, template)

        emails_sent = 0
        if 'staff_csv' in request.files:
            file = request.files['staff_csv']
            if file.filename != '':
                stream = io.StringIO(file.stream.read().decode('UTF-8'))
                reader = csv.reader(stream)
                for row in reader:
                    if row and '@' in row[0]:
                        try:
                            send_phishing_email(row[0].strip(), code, template)
                            emails_sent += 1
                        except Exception as e:
                            print(f"Failed to send to {row[0]}: {e}")

        link = f"http://127.0.0.1:5000/sim/{code}"
        return render_template('create.html', link=link, success=True,
                               emails_sent=emails_sent, templates=TEMPLATES)
    return render_template('create.html', success=False, emails_sent=0, templates=TEMPLATES)

app.jinja_env.globals['enumerate'] = enumerate
app.run(debug=True)
