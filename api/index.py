import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from supabase import create_client, Client
import smtplib
from email.message import EmailMessage

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = "avinash_bca_project_key"

# Supabase Config - Use Environment Variables in Vercel
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Email Config for Admin
EMAIL_ID = os.environ.get("EMAIL_ID")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

@app.route('/')
def index():
    events = supabase.table('events').select("*").execute()
    return render_template('index.html', events=events.data)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            auth_res = supabase.auth.sign_up({"email": email, "password": password})
            if auth_res.user:
                supabase.table('profiles').upsert({
                    "id": auth_res.user.id,
                    "full_name": request.form.get('name'),
                    "univ_roll": request.form.get('roll'),
                    "sec": request.form.get('sec'),
                    "course": request.form.get('course')
                }).execute()
                return redirect(url_for('login'))
        except Exception as e:
            flash("Signup Failed. Try again.")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if res.user:
                session['user_id'] = res.user.id
                session['user_email'] = email
                return redirect(url_for('index'))
        except:
            flash("Invalid Login Details")
    return render_template('login.html')

@app.route('/register_event/<int:event_id>')
def register_event(event_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    supabase.table('registrations').insert({"student_id": session['user_id'], "event_id": event_id}).execute()
    return render_template('success.html')

@app.route('/admin')
def admin():
    # Fetch registrations with Student and Event info
    res = supabase.table('registrations').select("id, status, profiles(full_name, univ_roll, course, id), events(title)").execute()
    return render_template('admin.html', registrations=res.data)

@app.route('/send_pass/<reg_id>')
def send_pass(reg_id):
    # Fetch specific registration data
    res = supabase.table('registrations').select("*, profiles(*), events(*)").eq("id", reg_id).single().execute()
    data = res.data
    
    # Send Email
    msg = EmailMessage()
    msg.set_content(f"Hi {data['profiles']['full_name']},\n\nYour pass for {data['events']['title']} is confirmed.\nRoll: {data['profiles']['univ_roll']}")
    msg['Subject'] = f"Event Pass: {data['events']['title']}"
    msg['From'] = EMAIL_ID
    msg['To'] = data['profiles']['id'] # Assuming ID is email or fetch email from profiles

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ID, EMAIL_PASS)
            smtp.send_message(msg)
        supabase.table('registrations').update({"status": "sent"}).eq("id", reg_id).execute()
        flash("Pass Sent Successfully!")
    except:
        flash("Email failed to send.")
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def handler(event, context):
    return app(event, context)
