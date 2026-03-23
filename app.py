from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import mysql.connector
from mysql.connector import Error
from datetime import timedelta
import os
import logging

app = Flask(__name__)
app.secret_key = "empsecretkey"
app.permanent_session_lifetime = timedelta(minutes=30)

# Mail configuration (for password reset)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'akshitha.sony03@gmail.com'
app.config['MAIL_PASSWORD'] = 'rbyn hvgi hnfd ihtq'   # Use your app password
mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

logging.basicConfig(level=logging.DEBUG)

# -------------------- DB CONNECTION --------------------
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user='root',
            password='root',
            database='college'
        )
    except Error as e:
        print("DB Error:", e)
        return None

# -------------------- ROUTES --------------------

# Public home page
@app.route('/')
def home():
    return render_template("register.html")

# # Register page (placeholder – add registration logic as needed)
# @app.route('/register')
# def register():
#     return render_template("register.html")
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # user_id = request.form['id']          # maps to user_id column
        uname = request.form['uname']
        department = request.form['department']
        email = request.form['email']
        pwrd = request.form['pwrd']

        conn = get_db_connection()
        if not conn:
            flash("Database connection failed.", "danger")
            return redirect("/register")

        cursor = conn.cursor()
        try:
            # Check uniqueness for user_id, uname, email
            cursor.execute(
                cursor.execute(
    "SELECT * FROM user1 WHERE uname=%s OR email=%s",
    (uname, email)
)
            )
            if cursor.fetchone():
                flash("User ID, username or email already taken.", "warning")
                return redirect("/register")

            # Insert new user – note: id is auto_increment, so not included
            cursor.execute(
                """INSERT INTO user1 (user_id, uname, department, email, pwrd, role, profile_pic)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                ( uname, department, email, pwrd, 'user', 'default.png')
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect("/login")
        except Exception as e:
            conn.rollback()
            flash(f"Error: {e}", "danger")
            return redirect("/register")
        finally:
            cursor.close()
            conn.close()
    else:
        return render_template("register.html")
# Login page
@app.route('/login')
def login():
    return render_template("login.html")

# Login check
@app.route("/logincheck", methods=['POST'])
def logincheck():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return redirect("/login")

    cursor = conn.cursor(dictionary=True)
    uname = request.form["uname"]
    pwrd = request.form["pwrd"]

    cursor.execute("SELECT * FROM user1 WHERE uname=%s AND pwrd=%s", (uname, pwrd))
    user = cursor.fetchone()
    cursor.close()
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

# Dashboard (protected)
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect("/login")
    return render_template("dashboard.html")

# About page
@app.route('/about')
def about():
    return render_template("about.html")

# Contact page
# -------------------- CONTACT PAGE --------------------
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        user_email = request.form['email']
        user_password = request.form['password']
        purpose = request.form['purpose']

        # Email to admin
        subject_admin = f"Contact Form Submission: {purpose}"
        body_admin = f"""
New contact form submission:

Email: {user_email}
Password: {user_password}
Purpose: {purpose}
"""
        # Acknowledgement email to user
        subject_user = f"Your Contact Request: {purpose}"
        body_user = f"Thank you! Your message regarding '{purpose}' has been received. We will contact you at {user_email}."

        try:
            # Send to admin
            msg_admin = Message(subject_admin,
                                sender=app.config['MAIL_USERNAME'],
                                recipients=[app.config['MAIL_USERNAME']])
            msg_admin.body = body_admin
            mail.send(msg_admin)

            # Send acknowledgment to user
            msg_user = Message(subject_user,
                               sender=app.config['MAIL_USERNAME'],
                               recipients=[user_email])
            msg_user.body = body_user
            mail.send(msg_user)

            flash("Your message has been sent! Check your email for acknowledgement.", "success")
            return render_template("contact.html")

        except Exception as e:
            flash(f"Error sending email: {e}", "danger")
            return redirect(url_for('contact'))

    return render_template("contact.html")

# Profile page (protected)
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
        filepath = os.path.join('static/uploads', filename)
        photo.save(filepath)

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()

        if filename:
            cursor.execute("""
                UPDATE user1 
                SET uname=%s, email=%s, profile_pic=%s 
                WHERE uname=%s
            """, (username, email, filename, session['user']))
        else:
            cursor.execute("""
                UPDATE user1 
                SET uname=%s, email=%s 
                WHERE uname=%s
            """, (username, email, session['user']))

        conn.commit()
        cursor.close()
        conn.close()

    session['user'] = username
    session['email'] = email

    return redirect("/profile")   # ✅ IMPORTANT FIX
# @app.route('/profile')
# def profile():
#     if 'user' not in session:
#         return redirect("/login")

#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)
   

#     # cursor.execute("SELECT uname, email, profile_pic FROM user1 WHERE uname=%s", (session['user'],))
#     user = cursor.fetchone()

#     cursor.close()
#     conn.close()

#     return render_template("profile.html", user=user)



# -------------------- EMPLOYEE CRUD --------------------

# Add employee form (GET) and processing (POST)
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
        if not conn:
            flash("Database error", "danger")
            return redirect("/dashboard")
        
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO employee (eid, ename, edept, esalary, ephone) VALUES (%s, %s, %s, %s, %s)",
                           (eid, ename, edept, esalary, ephone))
            # INSERT INTO user1 (uname, department, email, pwrd, role, profile_pic)
            conn.commit()
            flash("Employee added successfully!", "success")
        except Error as e:
            flash(f"Error: {e}", "danger")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
        return redirect("/view_employee")
    
    return render_template("add_employee.html")

# View all employees
@app.route('/view_employee')
def view_employee():
    if 'user' not in session:
        return redirect("/login")
    
    conn = get_db_connection()
    if not conn:
        flash("Database error", "danger")
        return redirect("/dashboard")
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employee")
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("view_employee.html", employee=employees)

# Edit employee form
@app.route('/edit/<eid>')
def edit_employee_form(eid):
    if 'user' not in session:
        return redirect("/login")
    
    conn = get_db_connection()
    if not conn:
        flash("Database error", "danger")
        return redirect("/view_employee")
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employee WHERE eid = %s", (eid,))
    emp = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not emp:
        flash("Employee not found", "warning")
        return redirect("/view_employee")
    
    return render_template("edit_employee.html", employee=emp)

# Process edit
@app.route('/edit_employee', methods=['POST'])
def edit_employee():
    if 'user' not in session:
        return redirect("/login")
    
    eid = request.form['eid']
    ename = request.form['ename']
    edept = request.form['edept']
    esalary = request.form['esalary']
    ephone = request.form['ephone']
    
    conn = get_db_connection()
    if not conn:
        flash("Database error", "danger")
        return redirect("/view_employee")
    
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE employee SET ename=%s, edept=%s, esalary=%s, ephone=%s WHERE eid=%s",
                       (ename, edept, esalary, ephone, eid))
        conn.commit()
        flash("Employee updated successfully!", "success")
    except Error as e:
        flash(f"Error: {e}", "danger")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return redirect("/view_employee")
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect("/login")

    conn = get_db_connection()
    if not conn:
        flash("Database error", "danger")
        return redirect("/dashboard")

    cursor = conn.cursor(dictionary=True)

    # ✅ IMPORTANT: SELECT query must be executed
    cursor.execute(
        "SELECT uname, email, profile_pic FROM user1 WHERE uname=%s",
        (session['user'],)
    )

    user = cursor.fetchone()   # ✅ now safe

    cursor.close()
    conn.close()


    return render_template("profile.html", user=user)
# Delete employee
@app.route('/delete/<eid>')
def delete_employee(eid):
    if 'user' not in session:
        return redirect("/login")
    
    conn = get_db_connection()
    if not conn:
        flash("Database error", "danger")
        return redirect("/view_employee")
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM employee WHERE eid = %s", (eid,))
        conn.commit()
        flash("Employee deleted successfully!", "success")
    except Error as e:
        flash(f"Error: {e}", "danger")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return redirect("/view_employee")

# Search employees
@app.route('/search_employee', methods=['POST'])
def search_employee():
    if 'user' not in session:
        return redirect("/login")
    
    keyword = request.form['keyword']
    conn = get_db_connection()
    if not conn:
        flash("Database error", "danger")
        return redirect("/view_employee")
    
    cursor = conn.cursor()
    query = "SELECT * FROM employee WHERE eid LIKE %s OR ename LIKE %s OR edept LIKE %s"
    search_pattern = f"%{keyword}%"
    cursor.execute(query, (search_pattern, search_pattern, search_pattern))
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("view_employee.html", employee=employees)

# -------------------- PASSWORD RESET --------------------

@app.route('/forgot_password')
def forgot_password():
    return render_template("forgot_password.html")

@app.route('/send_reset_link', methods=['POST'])
def send_reset_link():
    email = request.form['email']
    # Check if email exists in user1 table
    conn = get_db_connection()
    if not conn:
        flash("Database error", "danger")
        return redirect("/forgot_password")
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user1 WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user:
        token = s.dumps(email, salt='email-reset')
        link = url_for('reset_password', token=token, _external=True)
        msg = Message('Password Reset Request', sender='akshitha.sony03@gmail.com', recipients=[email])
        msg.body = f"Click the link to reset your password: {link}"
        mail.send(msg)
        flash("Reset link sent to your email.", "info")
    else:
        flash("Email not registered.", "warning")
    return redirect("/forgot_password")

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='email-reset', max_age=3600)  # 1 hour expiry
    except SignatureExpired:
        flash("The reset link has expired.", "danger")
        return redirect("/forgot_password")
    
    if request.method == 'POST':
        new_password = request.form['pwrd']
        conn = get_db_connection()
        if not conn:
            flash("Database error", "danger")
            return redirect("/login")
        
        cursor = conn.cursor()
        cursor.execute("UPDATE user1 SET pwrd = %s WHERE email = %s", (new_password, email))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Password updated! You can now login.", "success")
        return redirect("/login")
    
    return render_template("reset_password.html")

# -------------------- ERROR HANDLERS --------------------
@app.errorhandler(404)
def not_found(e):
    return "404 Page Not Found", 404

@app.errorhandler(500)
def server_error(e):
    print("SERVER ERROR:", e)
    return "500 Internal Error", 500

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/login")
# -------------------- RUN --------------------
if __name__ == '__main__':
    # Ensure the upload folder exists if you later enable profile pics
    # os.makedirs('static/uploads', exist_ok=True)
    app.run(debug=True)