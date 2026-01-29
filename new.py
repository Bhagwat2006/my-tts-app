import os
import sqlite3
import hashlib
import uuid
import datetime
from datetime import datetime, timedelta
import streamlit as st
from elevenlabs.client import ElevenLabs

# --- CONFIGURATION & SECURITY ---
try:
    ELEVEN_KEY = st.secrets.get("ELEVEN_API_KEY", "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40")
except:
    ELEVEN_KEY = "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40"

client = ElevenLabs(api_key=ELEVEN_KEY)
DB_PATH = "studio_v4.db"
ADMIN_MOBILE = "8452095418"

# --- DATABASE ENGINE ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (username TEXT PRIMARY KEY, password TEXT, email TEXT, 
                     plan TEXT, expiry_date TEXT, usage_count INTEGER, receipt_id TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_voices 
                     (username TEXT, voice_name TEXT, voice_id TEXT)''')
        
        c.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in c.fetchall()]
        if "receipt_id" not in columns:
            c.execute("ALTER TABLE users ADD COLUMN receipt_id TEXT DEFAULT 'NONE'")
        conn.commit()

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def upgrade_plan(username, plan_type):
    receipt_id = f"REC-{uuid.uuid4().hex[:8].upper()}"
    expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE users SET plan=?, expiry_date=?, usage_count=0, receipt_id=? WHERE username=?", 
                     (plan_type, expiry, receipt_id, username))
        conn.commit()
    return receipt_id, expiry

# --- UI SETUP ---
st.set_page_config(page_title="Global AI Voice Studio Pro", layout="wide")
init_db()

# --- AUTO SIGN-IN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Check for existing credentials in query parameters (Auto-Login)
if not st.session_state.logged_in:
    params = st.query_params
    if "user" in params and "token" in params:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # We verify the user and their hashed password (used as a simple token)
            c.execute("SELECT username FROM users WHERE username=? AND password=?", (params["user"], params["token"]))
            auto_user = c.fetchone()
            if auto_user:
                st.session_state.logged_in = True
                st.session_state.user = auto_user[0]

# --- AUTHENTICATION INTERFACE ---
if not st.session_state.logged_in:
    st.title("🌐 Global AI Voice Studio")
    auth_action = st.sidebar.selectbox("Account Access", ["Login", "Sign Up"])
    
    if auth_action == "Sign Up":
        u = st.text_input("Choose Username").strip()
        e = st.text_input("Email Address").strip()
        p = st.text_input("Create Password (8 chars)", type="password", max_chars=8)
        if st.button("Create Account"):
            if len(p) == 8 and u and e:
                with sqlite3.connect(DB_PATH) as conn:
                    try:
                        hp = hash_pass(p)
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                                     (u, hp, e, "Free", "N/A", 0, "NONE"))
                        conn.commit()
                        # Set query params for future auto-login
                        st.query_params["user"] = u
                        st.query_params["token"] = hp
                        st.success("✅ Account created! You are now auto-enrolled.")
                        st.session_state.logged_in = True
                        st.session_state.user = u
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Username already exists!")
            else:
                st.warning("⚠️ All fields required.")
    
    else:
        u = st.text_input("Username").strip()
        p = st.text_input("Password", type="password", max_chars=8)
        if st.button("Secure Login"):
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                hp = hash_pass(p)
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hp))
                userData = c.fetchone()
                if userData:
                    # Save to query_params so user stays logged in after refresh
                    st.query_params["user"] = u
                    st.query_params["token"] = hp
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials!")

# --- MAIN DASHBOARD AREA ---
else:
    username = st.session_state.user
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        userData = c.fetchone()
        c.execute("SELECT voice_name, voice_id FROM user_voices WHERE username=?", (username,))
        cloned_voices = {row[0]: row[1] for row in c.fetchall()}
    
    if not userData: # Safety check if user was deleted
        st.session_state.logged_in = False
        st.rerun()

    _, _, email, plan, expiry, usage, receipt_id = userData

    st.sidebar.title(f"User: {username}")
    st.sidebar.info(f"Membership: {plan}")
    if st.sidebar.button("Logout & Clear Session"):
        st.session_state.logged_in = False
        st.query_params.clear() # Removes auto-login tokens
        st.rerun()

    # [Generator, Cloning, Subscription, Billing Tabs remain the same...]
    t1, t2, t3, t4 = st.tabs(["🔊 Generator", "🎙️ Cloning", "💳 Subscription", "📄 Billing"])

    with t1:
        st.header("Studio-Quality AI Generation")
        default_voices = {"Bella (Soft)": "21m00Tcm4TlvDq8ikWAM", "Adam (Deep)": "pNInz6obpgDQGcFmaJgB"}
        all_available_voices = {**default_voices, **cloned_voices}
        selected_v_name = st.selectbox("Select Voice Model", list(all_available_voices.keys()))
        selected_v_id = all_available_voices[selected_v_name]
        script_text = st.text_area("Input Script")
        
        if st.button("⚡ Generate Audio"):
            # ... generation logic ...
            with st.spinner("Processing..."):
                try:
                    audio_stream = client.text_to_speech.convert(
                        voice_id=selected_v_id,
                        text=script_text,
                        model_id="eleven_multilingual_v2"
                    )
                    st.audio(b"".join(audio_stream))
                    with sqlite3.connect(DB_PATH) as conn:
                        conn.execute("UPDATE users SET usage_count = usage_count + 1 WHERE username=?", (username,))
                        conn.commit()
                except Exception as e:
                    st.error(f"Error: {e}")
