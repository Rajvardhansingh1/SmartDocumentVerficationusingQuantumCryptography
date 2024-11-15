from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.utils import secure_filename
from utils import generate_key, encrypt_document, decrypt_document, hash_password
import os
import json
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Define paths for storing user and file data
USER_DATA_FILE = 'server/data/users.json'
FILE_DATA_FILE = 'server/data/files.json'
DECRYPTED_FILE_PATH = 'server/uploads/decrypted_file'

# Ensure required directories exist
os.makedirs('server/data', exist_ok=True)
os.makedirs('server/uploads', exist_ok=True)

# Helper functions to load and save JSON data
def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('upload'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        users = load_json(USER_DATA_FILE)
        
        if username in users:
            flash("User already exists. Please login.")
            return redirect(url_for('login'))
        
        if password != confirm_password:
            flash("Passwords do not match. Please try again.")
            return redirect(url_for('register'))
        
        encryption_key = generate_key()
        password_hash = hash_password(password)
        
        users[username] = {
            'password_hash': password_hash,
            'encryption_key': encryption_key.decode('utf-8'),
            'email': email
        }
        save_json(USER_DATA_FILE, users)
        
        flash("Registration successful. Please login.")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_json(USER_DATA_FILE)
        user = users.get(username)
        
        if not user or user['password_hash'] != hash_password(password):
            flash("Invalid username or password.")
            return redirect(url_for('login'))
        
        session['username'] = username
        return redirect(url_for('upload'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        file_name = request.form['file_name']
        file = request.files['file']
        
        if file_name == '' or file.filename == '':
            flash("Please provide both a file and a file name.")
            return redirect(url_for('upload'))
        
        username = session['username']
        users = load_json(USER_DATA_FILE)
        encryption_key = users[username]['encryption_key'].encode('utf-8')
        
        file_content = file.read()
        encrypted_content = encrypt_document(encryption_key, file_content)
        
        files = load_json(FILE_DATA_FILE)
        files[file_name] = {
            'username': username,
            'original_filename': secure_filename(file.filename),
            'encrypted_content': encrypted_content
        }
        save_json(FILE_DATA_FILE, files)
        
        flash("Document uploaded and encrypted successfully.")
    
    return render_template('upload.html')

@app.route('/retrieve', methods=['GET', 'POST'])
def retrieve():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        file_name = request.form['file_name']
        username = session['username']
        
        files = load_json(FILE_DATA_FILE)
        file_data = files.get(file_name)
        
        if not file_data or file_data['username'] != username:
            flash("Document not found.")
            return redirect(url_for('retrieve'))
        
        users = load_json(USER_DATA_FILE)
        encryption_key = users[username]['encryption_key'].encode('utf-8')
        encrypted_content = file_data['encrypted_content']

        try:
            decrypted_content = decrypt_document(encryption_key, encrypted_content)
            decrypted_file_path = f"{DECRYPTED_FILE_PATH}_{file_data['original_filename']}"
            with open(decrypted_file_path, 'wb') as decrypted_file:
                decrypted_file.write(decrypted_content)
            
            return send_file(decrypted_file_path, as_attachment=True)
        except Exception as e:
            flash("Error decrypting file.")
            print(f"Decryption error: {e}")
            return redirect(url_for('retrieve'))
    
    return render_template('retrieve.html')

if __name__ == '__main__':
    app.run(port=5000, debug=True)
