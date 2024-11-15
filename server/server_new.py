import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

users_file = 'users.json'
metadata_file = 'file_metadata.json'

def load_users():
    try:
        with open(users_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_users(users):
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=4)

def save_file_metadata(metadata):
    try:
        with open(metadata_file, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append(metadata)
    with open(metadata_file, 'w') as f:
        json.dump(data, f, indent=4)

def get_user_files(email):
    try:
        with open(metadata_file, 'r') as f:
            data = json.load(f)
        return [file for file in data if file["email"] == email]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

@app.route('/')
def home():
    if 'email' in session:
        return redirect(url_for('upload'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        if any(user['email'] == email for user in users):
            flash('Email already registered')
            return redirect(url_for('register'))
        users.append({'email': email, 'password': password})
        save_users(users)
        send_email(email)
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        user = next((u for u in users if u['email'] == email and u['password'] == password), None)
        if user:
            session['email'] = email
            flash('Login successful!')
            return redirect(url_for('upload'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'email' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file_name' not in request.form or 'file' not in request.files:
            flash('File name and file are required.')
            return redirect(request.url)

        file_name = request.form['file_name']
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        metadata = {
            "email": session['email'],
            "file_name": file_name,
            "file_path": file_path
        }
        save_file_metadata(metadata)

        flash('File uploaded successfully!')
        return redirect(url_for('upload'))

    user_files = get_user_files(session['email'])
    return render_template('upload.html', files=user_files)

@app.route('/retrieve', methods=['GET', 'POST'])
def retrieve():
    if 'email' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        file_name = request.form['file_name']
        user_files = get_user_files(session['email'])
        file = next((f for f in user_files if f['file_name'] == file_name), None)
        if file:
            flash('File retrieved successfully!')
            return redirect(url_for('upload'))
        else:
            flash('File not found or decryption error.')
    return render_template('retrieve.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('Logged out successfully.')
    return redirect(url_for('login'))

def send_email(recipient_email):
    sender_email = 'your_email@example.com'
    sender_password = 'your_password'
    subject = 'Registration Successful'
    body = 'Thank you for registering! You can now log in to your account.'

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.example.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print("Error sending email:", e)

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
