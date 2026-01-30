import streamlit as st
import sqlite3
import uuid
import smtplib
from email.message import EmailMessage
from passlib.hash import bcrypt
from datetime import datetime, timedelta

# ---------------- CONFIG ----------------
APP_URL = "http://localhost:8501"  # change after deploy
SMTP_EMAIL = "yourgmail@gmail.com"
SMTP_PASSWORD = "your_app_password"

# ---------------- PAGE ------------------
st.set_page_config(page_title="Simple Auth App", layout="centered")

# ---------------- DATABASE --------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS reset_tokens (
    email TEXT,
    token TEXT,
    expires DATETIME
)
""")

conn.commit()

# ---------------- HELPERS ----------------
def send_email(to, subject, body):
    msg = EmailMessage()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)

# ---------------- SESSION ----------------
if "page" not in st.session_state:
    st.session_state.page = "login"
if "reset_token" not in st.session_state:
    st.session_state.reset_token = None

# ---------------- LOGIN ------------------
if st.session_state.page == "login":
    st.title("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        cur.execute("SELECT password FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        if user and bcrypt.verify(password, user[0]):
            st.success("Logged in successfully 🎉")
        else:
            st.error("Invalid credentials")

    if st.button("Create Account"):
        st.session_state.page = "register"
        st.rerun()

    if st.button("Forgot Password"):
        st.session_state.page = "forgot"
        st.rerun()

# ---------------- REGISTER ----------------
elif st.session_state.page == "register":
    st.title("📝 Register")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if password != confirm:
            st.error("Passwords do not match")
        else:
            try:
                cur.execute(
                    "INSERT INTO users (email, password) VALUES (?,?)",
                    (email, bcrypt.hash(password))
                )
                conn.commit()
                st.success("Account created. Please login.")
                st.session_state.page = "login"
                st.rerun()
            except:
                st.error("Email already registered")

    if st.button("Back"):
        st.session_state.page = "login"
        st.rerun()

# ---------------- FORGOT ----------------
elif st.session_state.page == "forgot":
    st.title("📧 Password Recovery")

    email = st.text_input("Registered Email")

    if st.button("Send Reset Link"):
        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        if not cur.fetchone():
            st.error("Email not found")
        else:
            token = str(uuid.uuid4())
            expiry = datetime.now() + timedelta(minutes=15)

            cur.execute("DELETE FROM reset_tokens WHERE email=?", (email,))
            cur.execute(
                "INSERT INTO reset_tokens VALUES (?,?,?)",
                (email, token, expiry)
            )
            conn.commit()

            reset_link = f"{APP_URL}?token={token}"
            send_email(
                email,
                "Password Reset",
                f"Click the link to reset your password:\n{reset_link}"
            )

            st.success("Reset link sent to email")

    if st.button("Back"):
        st.session_state.page = "login"
        st.rerun()

# ---------------- RESET ----------------
query_params = st.query_params
if "token" in query_params:
    token = query_params["token"]
    st.session_state.page = "reset"
    st.session_state.reset_token = token

elif st.session_state.page == "reset":
    st.title("🔁 Reset Password")

    new_pass = st.text_input("New Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Reset Password"):
        if new_pass != confirm:
            st.error("Passwords do not match")
        else:
            cur.execute(
                "SELECT email, expires FROM reset_tokens WHERE token=?",
                (st.session_state.reset_token,)
            )
            row = cur.fetchone()

            if not row or datetime.fromisoformat(row[1]) < datetime.now():
                st.error("Invalid or expired token")
            else:
                cur.execute(
                    "UPDATE users SET password=? WHERE email=?",
                    (bcrypt.hash(new_pass), row[0])
                )
                cur.execute(
                    "DELETE FROM reset_tokens WHERE email=?",
                    (row[0],)
                )
                conn.commit()
                st.success("Password reset successfully")
                st.session_state.page = "login"
                st.query_params.clear()
                st.rerun()
