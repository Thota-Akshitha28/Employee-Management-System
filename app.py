from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import sqlite3
from datetime import timedelta
import os
import logging

app = Flask(__name__)
app.secret_key = "empsecretkey"
app.permanent_session_lifetime = timedelta(minutes=30)

# -------------------- MAIL CONFIG --------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'akshitha.sony03@gmail.com'
app.config['MAIL_PASSWORD'] = 'rbyn hvgi hnfd ihtq'

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

logging.basicConfig(level=logging.DEBUG)

# -------------------- SQLITE CONNECTION --------------------
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# -------------------- CREATE TABLES --------------------
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uname TEXT UNIQUE,
            department TEXT,
            email TEXT UNIQUE,
            pwrd TEXT,
            role TEXT,
            profile_pic TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employee (
            eid TEXT PRIMARY KEY,
            ename TEXT,
            edept TEXT,
            esalary TEXT,
            ephone TEXT
        )
    ''')

    conn.commit()
    conn.close()

create_tables()

# -------------------- ROUTES --------------------

@app.route('/')
def home():
    return render_template("register.html")

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form['uname']
        department = request.form['department']
        email = request.form['email']
        pwrd = request.form['pwrd']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user1 WHERE uname=? OR email=?", (uname, email))
        if cursor.fetchone():
            flash("Username or email already exists", "warning")
            return redirect("/register")

        cursor.execute("""
            INSERT INTO user1 (uname, department, email, pwrd, role, profile_pic)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (uname, department, email, pwrd, 'user', 'default.png'))

        conn.commit()
        conn.close()

        flash("Registered successfully!", "success")
        return redirect("/login")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route('/login')
def login():
    return render_template("login.html")

@app.route("/logincheck", methods=['POST'])
def logincheck():
    uname = request.form["uname"]
    pwrd = request.form["pwrd"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user1 WHERE uname=? AND pwrd=?", (uname, pwrd))
    user = cursor.fetchone()

    conn.close()

    if user:
        session['user'] = user['uname']
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['email'] = user['email']
        flash("Login successful", "success")
        return redirect("/dashboard")
    else:
        flash("Invalid credentials", "danger")
        return redirect("/login")

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect("/login")
    return render_template("dashboard.html")

# ---------------- ABOUT ----------------
@app.route('/about')
def about():
    return render_template("about.html")

# ---------------- CONTACT ----------------
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        user_email = request.form['email']
        user_password = request.form['password']
        purpose = request.form['purpose']

        try:
            msg = Message(f"Contact: {purpose}",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[app.config['MAIL_USERNAME']])
            msg.body = f"Email: {user_email}\nPassword: {user_password}\nPurpose: {purpose}"
            mail.send(msg)

            flash("Message sent!", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template("contact.html")

# ---------------- PROFILE ----------------
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT uname, email, profile_pic FROM user1 WHERE uname=?", (session['user'],))
    user = cursor.fetchone()

    conn.close()

    return render_template("profile.html", user=user)

# ---------------- UPDATE PROFILE ----------------
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return redirect("/login")

    username = request.form['username']
    email = request.form['email']
    photo = request.files['photo']

    filename = None

    if photo and photo.filename != "":
        os.makedirs('static/uploads', exist_ok=True)
        filename = photo.filename
        photo.save(os.path.join('static/uploads', filename))

    conn = get_db_connection()
    cursor = conn.cursor()

    if filename:
        cursor.execute("UPDATE user1 SET uname=?, email=?, profile_pic=? WHERE uname=?",
                       (username, email, filename, session['user']))
    else:
        cursor.execute("UPDATE user1 SET uname=?, email=? WHERE uname=?",
                       (username, email, session['user']))

    conn.commit()
    conn.close()

    session['user'] = username
    session['email'] = email

    return redirect("/profile")

# ---------------- EMPLOYEE CRUD ----------------

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if 'user' not in session:
        return redirect("/login")

    if request.method == 'POST':
        eid = request.form['eid']
        ename = request.form['ename']
        edept = request.form['edept']
        esalary = request.form['esalary']
        ephone = request.form['ephone']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO employee VALUES (?, ?, ?, ?, ?)",
                       (eid, ename, edept, esalary, ephone))

        conn.commit()
        conn.close()

        flash("Employee added!", "success")
        return redirect("/view_employee")

    return render_template("add_employee.html")

@app.route('/view_employee')
def view_employee():
    if 'user' not in session:
        return redirect("/login")

    conn = get_db_connection()
    employees = conn.execute("SELECT * FROM employee").fetchall()
    conn.close()

    return render_template("view_employee.html", employee=employees)

@app.route('/edit/<eid>')
def edit_employee_form(eid):
    conn = get_db_connection()
    emp = conn.execute("SELECT * FROM employee WHERE eid=?", (eid,)).fetchone()
    conn.close()

    return render_template("edit_employee.html", employee=emp)

@app.route('/edit_employee', methods=['POST'])
def edit_employee():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE employee SET ename=?, edept=?, esalary=?, ephone=? WHERE eid=?
    """, (
        request.form['ename'],
        request.form['edept'],
        request.form['esalary'],
        request.form['ephone'],
        request.form['eid']
    ))

    conn.commit()
    conn.close()

    return redirect("/view_employee")

@app.route('/delete/<eid>')
def delete_employee(eid):
    conn = get_db_connection()
    conn.execute("DELETE FROM employee WHERE eid=?", (eid,))
    conn.commit()
    conn.close()

    return redirect("/view_employee")

@app.route('/search_employee', methods=['POST'])
def search_employee():
    keyword = f"%{request.form['keyword']}%"

    conn = get_db_connection()
    employees = conn.execute("""
        SELECT * FROM employee
        WHERE eid LIKE ? OR ename LIKE ? OR edept LIKE ?
    """, (keyword, keyword, keyword)).fetchall()

    conn.close()

    return render_template("view_employee.html", employee=employees)

# ---------------- PASSWORD RESET ----------------

@app.route('/forgot_password')
def forgot_password():
    return render_template("forgot_password.html")

@app.route('/send_reset_link', methods=['POST'])
def send_reset_link():
    email = request.form['email']

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM user1 WHERE email=?", (email,)).fetchone()
    conn.close()

    if user:
        token = s.dumps(email, salt='email-reset')
        link = url_for('reset_password', token=token, _external=True)

        msg = Message('Reset Password',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f"Click here: {link}"
        mail.send(msg)

        flash("Reset link sent", "info")
    else:
        flash("Email not found", "danger")

    return redirect("/forgot_password")

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='email-reset', max_age=3600)
    except SignatureExpired:
        flash("Link expired", "danger")
        return redirect("/forgot_password")

    if request.method == 'POST':
        new_pw = request.form['pwrd']

        conn = get_db_connection()
        conn.execute("UPDATE user1 SET pwrd=? WHERE email=?", (new_pw, email))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("reset_password.html")

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)