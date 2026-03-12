import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from supabase import create_client, Client

# This calculates the absolute path to the root of your project
base_dir = os.path.dirname(os.path.abspath(__file__))
# Moves up one level from 'api/' to find templates and static
template_dir = os.path.join(base_dir, '../templates')
static_dir = os.path.join(base_dir, '../static')

app = Flask(__name__, 
            template_folder=template_dir, 
            static_folder=static_dir)

app.secret_key = "avinash_bca_project_key"

# Always use Environment Variables for security
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
EMAIL_ID = os.environ.get("EMAIL_ID")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# -------------------------
# Home Page
# -------------------------

@app.route('/')
def index():
    try:
        events = supabase.table('events').select("*").execute()
        return render_template('index.html', events=events.data)
    except Exception as e:
        return f"Database Error: {str(e)}"


# -------------------------
# Signup
# -------------------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        try:

            auth_res = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            if auth_res.user:

                supabase.table('profiles').upsert({
                    "id": auth_res.user.id,
                    "full_name": request.form.get('name'),
                    "univ_roll": request.form.get('roll'),
                    "sec": request.form.get('sec'),
                    "course": request.form.get('course')
                }).execute()

                return redirect(url_for('login'))

        except Exception:
            flash("Signup Failed. Password must be at least 6 characters.")

    return render_template('signup.html')


# -------------------------
# Login
# -------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        try:

            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if res.user:
                session['user_id'] = res.user.id
                session['user_email'] = email

                return redirect(url_for('index'))

        except:
            flash("Invalid Login Details")

    return render_template('login.html')


# -------------------------
# Register Event
# -------------------------

@app.route('/register_event/<event_id>')
def register_event(event_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:

        supabase.table('registrations').insert({
            "student_id": session['user_id'],
            "event_id": event_id
        }).execute()

        return render_template('success.html')

    except Exception as e:
        return f"Registration Error: {str(e)}"


# -------------------------
# Admin Panel
# -------------------------

@app.route('/admin')
def admin():

    try:

        res = supabase.table('registrations').select(
            "id, status, profiles(full_name, univ_roll, course), events(title)"
        ).execute()

        return render_template('admin.html', registrations=res.data)

    except Exception as e:
        return f"Admin Panel Error: {str(e)}"


# -------------------------
# Send Event Pass
# -------------------------

@app.route('/send_pass/<reg_id>')
def send_pass(reg_id):

    try:

        res = supabase.table('registrations').select(
            "*, profiles(*), events(*)"
        ).eq("id", reg_id).single().execute()

        data = res.data

        msg = EmailMessage()

        msg.set_content(
            f"Hi {data['profiles']['full_name']},\n\n"
            f"Your pass for {data['events']['title']} is confirmed!\n"
            f"Roll: {data['profiles']['univ_roll']}"
        )

        msg['Subject'] = f"Event Pass: {data['events']['title']}"
        msg['From'] = EMAIL_ID
        msg['To'] = session.get('user_email')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ID, EMAIL_PASS)
            smtp.send_message(msg)

        supabase.table('registrations').update({
            "status": "sent"
        }).eq("id", reg_id).execute()

        flash("Pass Sent!")

    except Exception as e:
        flash(f"Error: {str(e)}")

    return redirect(url_for('admin'))


# -------------------------
# Logout
# -------------------------

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('index'))


# -------------------------
# Vercel Handler
# -------------------------
if __name__ == "__main__":
    app.run()
