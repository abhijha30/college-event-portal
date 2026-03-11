from flask import Flask, render_template, request, redirect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# --- CONFIGURATION ---
# 1. Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# You will upload your service_account.json to your project
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

# 2. Email Setup (Use App Passwords for Gmail)
EMAIL_ID = "your-email@gmail.com"
EMAIL_PASS = "your-app-password"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    event_name = request.form.get('event_name')

    # --- 1. Export to Google Sheet ---
    try:
        sheet = client.open("College_Events_Data").worksheet(event_name)
    except:
        # If worksheet doesn't exist, create it or use a default
        sheet = client.open("College_Events_Data").sheet1
    
    sheet.append_row([name, email, event_name])

    # --- 2. Send Confirmation Email ---
    msg = EmailMessage()
    msg.set_content(f"Hi {name},\n\nYour registration for {event_name} is successful!\nShow this email at the desk.")
    msg['Subject'] = f"Event Pass: {event_name}"
    msg['From'] = EMAIL_ID
    msg['To'] = email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ID, EMAIL_PASS)
        smtp.send_message(msg)

    return render_template('success.html', name=name)

# Important for Vercel
def handler(event, context):
    return app(event, context)
