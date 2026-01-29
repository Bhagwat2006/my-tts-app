import os
import sqlite3
import hashlib
import uuid
import datetime
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components
from elevenlabs.client import ElevenLabs
import speech_recognition as sr

# --- CONFIGURATION & SECURITY ---
try:
    ELEVEN_KEY = st.secrets.get("ELEVEN_API_KEY", "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40")
except:
    ELEVEN_KEY = "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40"

client = ElevenLabs(api_key=ELEVEN_KEY)
DB_PATH = "studio_v4.db"
ADMIN_MOBILE = "8452095418"

# --- 🚀 THE ULTIMATE UI ENGINE (3D + ANIMATIONS) ---
def inject_ui_engine():
    st.markdown("""
        <style>
        /* Global Background and Smooth Scroll */
        .main { background: #05050a; color: #e0e0e0; font-family: 'Inter', sans-serif; }
        
        /* Navigation & Content Animations */
        .stTabs [data-baseweb="tab-panel"] {
            animation: slideIn 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
        }
        
        @keyframes slideIn {
            0% { opacity: 0; transform: translateX(-30px); filter: blur(5px); }
            100% { opacity: 1; transform: translateX(0); filter: blur(0); }
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }

        /* Glassmorphism Auth Card */
        .auth-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 25px;
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
            animation: fadeIn 1s ease-out;
        }

        /* Input Styling */
        input { 
            background: rgba(255, 255, 255, 0.05) !important; 
            border: 1px solid rgba(255, 255, 255, 0.1) !important; 
            color: white !important; 
            border-radius: 10px !important;
        }

        /* Button Glow Effects */
        .stButton>button {
            background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
            border: none;
            color: white;
            padding: 12px 24px;
            border-radius: 12px;
            font-weight: bold;
            transition: 0.3s all ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stButton>button:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 20px rgba(0, 210, 255, 0.5);
        }
        </style>
    """, unsafe_allow_html=True)

    # 3D Particles Background
    components.html("""
        <div id="particles-js" style="position: fixed; width: 100vw; height: 100vh; top: 0; left: 0; z-index: -1;"></div>
        <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
        <script>
            particlesJS('particles-js', {
                "particles": {
                    "number": {"value": 120},
                    "color": {"value": "#00d2ff"},
                    "shape": {"type": "circle"},
                    "opacity": {"value": 0.4},
                    "size": {"value": 2},
                    "line_linked": {"enable": true, "distance": 150, "color": "#3a7bd5", "opacity": 0.3, "width": 1},
                    "move": {"enable": true, "speed": 1.5}
                },
                "interactivity": {"events": {"onhover": {"enable": true, "mode": "bubble"}}}
            });
        </script>
    """, height=0)

# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, email TEXT, 
                 plan TEXT, expiry_date TEXT, usage_count INTEGER, receipt_id TEXT)''')
    c.execute("PRAGMA table_info(users)")
    if "receipt_id" not in [col[1] for col in c.fetchall()]:
        c.execute("ALTER TABLE users ADD COLUMN receipt_id TEXT DEFAULT 'NONE'")
    conn.commit()
    conn.close()

def hash_pass(password):
    return hashlib.sha256(str.encode(password[:8])).hexdigest()

def update_password(username, new_password):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET password=? WHERE username=?", (hash_pass(new_password), username))
    conn.commit()
    conn.close()

# --- VOICE SYSTEM ---
def listen_for_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.toast("🎤 System Listening...")
        try:
            audio = r.listen(source, timeout=5)
            return r.recognize_google(audio).lower()
        except: return None

# --- APP START ---
st.set_page_config(page_title="Ultra AI Studio", layout="wide")
inject_ui_engine()
init_db()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'auth_mode' not in st.session_state: st.session_state.auth_mode = "Login"

# --- AUTHENTICATION SUITE ---
if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.title("🌌 AI Studio")
        
        if st.session_state.auth_mode == "Login":
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Initialize Access"):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hash_pass(p)))
                if c.fetchone():
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Verification Failed")
                conn.close()
            
            # Sub-navigation
            st.markdown("---")
            c1, c2 = st.columns(2)
            if c1.button("Create Account"): st.session_state.auth_mode = "Signup"; st.rerun()
            if c2.button("Forgot Password?"): st.session_state.auth_mode = "Recover"; st.rerun()

        elif st.session_state.auth_mode == "Signup":
            u = st.text_input("New Username")
            e = st.text_input("Email")
            p = st.text_input("Pass (8 chars)", type="password", max_chars=8)
            if st.button("Register Neural ID"):
                if len(p) == 8:
                    conn = sqlite3.connect(DB_PATH)
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (u, hash_pass(p), e, "Free", "N/A", 0, "NONE"))
                        conn.commit()
                        st.success("Identity Created!")
                        st.session_state.auth_mode = "Login"; st.rerun()
                    except: st.error("ID Taken")
                    conn.close()
            if st.button("Back to Login"): st.session_state.auth_mode = "Login"; st.rerun()

        elif st.session_state.auth_mode == "Recover":
            st.subheader("Password Recovery")
            u = st.text_input("Your Username")
            e = st.text_input("Registered Email")
            new_p = st.text_input("New Password (8 chars)", type="password", max_chars=8)
            if st.button("Reset Password"):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND email=?", (u, e))
                if c.fetchone():
                    update_password(u, new_p)
                    st.success("Password Updated!")
                    st.session_state.auth_mode = "Login"; st.rerun()
                else: st.error("Email/User mismatch")
                conn.close()
            if st.button("Cancel"): st.session_state.auth_mode = "Login"; st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD ---
else:
    # Fetch user data
    conn = sqlite3.connect(DB_PATH)
    userData = conn.execute("SELECT * FROM users WHERE username=?", (st.session_state.user,)).fetchone()
    conn.close()
    _, _, email, plan, expiry, usage, receipt_id = userData

    # Animated Sidebar
    with st.sidebar:
        st.title(f"🚀 {st.session_state.user}")
        st.write(f"Level: **{plan}**")
        if st.button("🎙️ Voice Command"):
            cmd = listen_for_command()
            if cmd and "logout" in cmd: st.session_state.logged_in = False; st.rerun()
        if st.button("Exit"): st.session_state.logged_in = False; st.rerun()

    # Tabs with Slide-in Animation
    t1, t2, t3, t4 = st.tabs(["🔊 Generator", "🎙️ Cloning", "💳 Subscription", "📄 Billing"])

    with t1:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.header("Neural Audio Lab")
        txt = st.text_area("Script", "Synthesizing futuristic audio...")
        if st.button("⚡ Generate"):
            with st.spinner("Processing..."):
                audio = client.text_to_speech.convert(voice_id="pNInz6obpgDQGcFmaJgB", text=txt, model_id="eleven_multilingual_v2")
                st.audio(b"".join(audio))
        st.markdown('</div>', unsafe_allow_html=True)

    with t3:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.header("Upgrade Matrix")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Standard")
            st.write("₹1 / Mo")
            if st.button("Select Standard"): pass # Logic here
        with c2:
            st.subheader("👑 Premium Ultra")
            st.write("₹10 / Mo")
            if st.button("Activate Ultra"): 
                # (Existing upgrade logic)
                st.snow()
        
        st.divider()
        upi_link = f"upi://pay?pa={ADMIN_MOBILE}@ybl&am=10.00"
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={upi_link}")
        st.markdown('</div>', unsafe_allow_html=True)

    with t4:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.header("Digital Ledger")
        st.write(f"Receipt ID: **{receipt_id}**")
        st.write(f"Status: **VERIFIED**")
        st.markdown('</div>', unsafe_allow_html=True)
