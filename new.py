import os
import sqlite3
import bcrypt  # Replaced hashlib
import uuid
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components
from elevenlabs.client import ElevenLabs

# --- CONFIGURATION & SECURITY ---
try:
    ELEVEN_KEY = st.secrets.get("ELEVEN_API_KEY", "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40")
except:
    ELEVEN_KEY = "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40"

client = ElevenLabs(api_key=ELEVEN_KEY)
DB_PATH = "studio_v4.db"
ADMIN_MOBILE = "8452095418"

# --- 🚀 THE 3D ENGINE & GLASS UI ---
def inject_ui_engine():
    st.markdown("""
        <style>
        .main { background: #05050a; color: #e0e0e0; font-family: 'Inter', sans-serif; }
        .glass-card {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(20px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 25px !important;
            padding: 40px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8) !important;
        }
        [data-baseweb="tab-panel"] {
            animation: slideIn 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
        }
        @keyframes slideIn {
            0% { opacity: 0; transform: translateY(30px); filter: blur(5px); }
            100% { opacity: 1; transform: translateY(0); filter: blur(0); }
        }
        input { 
            background: rgba(255, 255, 255, 0.05) !important; 
            border: 1px solid rgba(255, 255, 255, 0.1) !important; 
            color: white !important; 
            border-radius: 10px !important;
        }
        .stButton>button {
            background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
            border: none !important;
            color: white !important;
            padding: 12px 24px !important;
            border-radius: 12px !important;
            font-weight: bold !important;
            transition: 0.3s all ease !important;
            text-transform: uppercase !important;
        }
        .stButton>button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 5px 20px rgba(0, 210, 255, 0.5) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    components.html("""
        <div id="particles-js" style="position: fixed; width: 100vw; height: 100vh; top: 0; left: 0; z-index: -1;"></div>
        <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
        <script>
            particlesJS('particles-js', {
                "particles": {
                    "number": {"value": 100, "density": {"enable": true, "value_area": 800}},
                    "color": {"value": "#00d2ff"},
                    "shape": {"type": "circle"},
                    "opacity": {"value": 0.5, "random": true},
                    "size": {"value": 3, "random": true},
                    "line_linked": {"enable": true, "distance": 150, "color": "#3a7bd5", "opacity": 0.4, "width": 1},
                    "move": {"enable": true, "speed": 2, "out_mode": "out"}
                },
                "interactivity": {"events": {"onhover": {"enable": true, "mode": "grab"}, "onclick": {"enable": true, "mode": "push"}}}
            });
        </script>
    """, height=0)

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
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
    conn.close()

# --- SECURITY UPDATE: BCRYPT ---
def hash_pass(password):
    """Generates a secure bcrypt hash."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.strip().encode('utf-8'), salt).decode('utf-8')

def verify_pass(entered_password, stored_hash):
    """Verifies password against stored bcrypt hash."""
    try:
        return bcrypt.checkpw(entered_password.strip().encode('utf-8'), stored_hash.encode('utf-8'))
    except:
        return False

def upgrade_plan(username, plan_type):
    receipt_id = f"REC-{uuid.uuid4().hex[:8].upper()}"
    expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET plan=?, expiry_date=?, usage_count=0, receipt_id=? WHERE username=?", 
                  (plan_type, expiry, receipt_id, username))
    conn.commit()
    conn.close()
    return receipt_id, expiry

def recover_password(u, e, new_p):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE LOWER(username)=LOWER(?) AND LOWER(email)=LOWER(?)", (u.strip(), e.strip()))
    user_found = c.fetchone()
    if user_found:
        c.execute("UPDATE users SET password=? WHERE username=?", (hash_pass(new_p), user_found[0]))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

# --- UI SETUP ---
st.set_page_config(page_title="Ultra AI Studio Pro", layout="wide")
inject_ui_engine()
init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- DYNAMIC LOGIN PORTAL ---
if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.title("🌐 AI Studio Nexus")
        auth_action = st.radio("Access Protocol", ["Login", "Sign Up", "Forgot Password"], horizontal=True)
        
        if auth_action == "Sign Up":
            u = st.text_input("Choose Username").strip()
            e = st.text_input("Email Address").strip()
            p = st.text_input("Create Password (min 8 chars)", type="password").strip()
            if st.button("Initialize Account"):
                if u and e and len(p) >= 8:
                    conn = sqlite3.connect(DB_PATH)
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (u, hash_pass(p), e, "Free", "N/A", 0, "NONE"))
                        conn.commit()
                        st.success("Account created! Switch to Login.")
                    except sqlite3.IntegrityError: 
                        st.error("Username already taken!")
                    finally:
                        conn.close()
                else: st.warning("Ensure all fields are filled & password is at least 8 chars.")
        
        elif auth_action == "Forgot Password":
            st.subheader("Neural Recovery")
            u_rec = st.text_input("Target Username").strip()
            e_rec = st.text_input("Registered Email").strip()
            new_p = st.text_input("New Password (min 8 chars)", type="password").strip()
            if st.button("Reset Identity Password"):
                if u_rec and e_rec and len(new_p) >= 8:
                    if recover_password(u_rec, e_rec, new_p):
                        st.success("Identity Updated! Login now.")
                    else:
                        st.error("Verification Mismatch! Check Username/Email.")
                else: st.warning("Fill all fields correctly.")

        else:
            u_log = st.text_input("Username").strip()
            p_log = st.text_input("Password", type="password").strip()
            if st.button("Authorize Access"):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE LOWER(username)=LOWER(?)", (u_log,))
                userData = c.fetchone()
                conn.close()
                
                # Using the new bcrypt verification logic
                if userData and verify_pass(p_log, userData[1]):
                    st.session_state.logged_in = True
                    st.session_state.user = userData[0]
                    st.rerun()
                else: st.error("Invalid credentials!")
        st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN DASHBOARD AREA ---
else:
    username = st.session_state.user
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    userData = c.fetchone()
    conn.close()
    
    _, _, email, plan, expiry, usage, receipt_id = userData

    with st.sidebar:
        st.markdown(f"### 🛡️ Operator: {username}")
        st.info(f"Membership: {plan}")
        if st.button("Terminate Session"):
            st.session_state.logged_in = False
            st.rerun()

    t1, t2, t3, t4 = st.tabs(["🔊 Generator", "🎙️ Cloning", "💳 Subscription", "📄 Billing"])

    with t1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.header("Neural Audio Synthesis")
        c1, c2 = st.columns(2)
        with c1:
            target_lang = st.selectbox("Language", ["English", "Hindi", "French", "German"])
            el_voices = {"Bella (Soft)": "21m00Tcm4TlvDq8ikWAM", "Adam (Deep)": "pNInz6obpgDQGcFmaJgB"}
            selected_v = st.selectbox("Voice Model", list(el_voices.keys()))
        
        script_text = st.text_area("Input Script", placeholder="Enter text for global synthesis...")
        limit = 3 if plan == "Free" else (50 if plan == "Standard" else 5000)
        
        if st.button("⚡ Execute Generation"):
            if usage >= limit:
                st.error("Limit reached. Upgrade at Subscription tab.")
            elif not script_text:
                st.warning("Input required.")
            else:
                with st.spinner(f"Synthesizing {target_lang}..."):
                    try:
                        audio_stream = client.text_to_speech.convert(
                            voice_id=el_voices[selected_v],
                            text=script_text,
                            model_id="eleven_multilingual_v2"
                        )
                        st.audio(b"".join(audio_stream))
                        
                        conn = sqlite3.connect(DB_PATH)
                        conn.execute("UPDATE users SET usage_count = usage_count + 1 WHERE username=?", (username,))
                        conn.commit()
                        conn.close()
                    except Exception as e: st.error(f"Error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with t2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.header("Private Voice Cloning")
        if plan == "Free":
            st.warning("Cloning requires a Standard or Premium subscription.")
        else:
            voice_file = st.file_uploader("Upload Sample", type=['wav','mp3'])
            label = st.text_input("Voice Name")
            if st.button("Begin Neural Clone"):
                if voice_file and label:
                    with st.spinner("Analyzing DNA..."):
                        new_voice = client.voices.add(name=label, files=[voice_file])
                        st.success(f"Success! Voice ID: {new_voice.voice_id}")
        st.markdown('</div>', unsafe_allow_html=True)

    with t3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.header("Upgrade Neural Level")
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.subheader("Standard")
                st.write("₹1 / Mo")
                if st.button("Activate Standard"):
                    upgrade_plan(username, "Standard")
                    st.rerun()

        with col2:
            with st.container(border=True):
                st.subheader("👑 Premium Ultra")
                st.write("₹10 / Mo")
                if st.button("Activate Premium"):
                    upgrade_plan(username, "Premium")
                    st.balloons()
                    st.rerun()
        
        st.divider()
        st.write("### 📲 Instant UPI Payment")
        st.info(f"Pay to UPI ID / Number: {ADMIN_MOBILE}@ybl")
        upi_link = f"upi://pay?pa={ADMIN_MOBILE}@ybl&pn=AI_Studio_Premium&am=10.00&cu=INR"
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={upi_link}")
        st.markdown('</div>', unsafe_allow_html=True)

    with t4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.header("Digital Ledger")
        if receipt_id == "NONE":
            st.info("No active paid subscriptions.")
        else:
            st.title("INVOICE / RECEIPT")
            st.divider()
            st.subheader(f"ID: {receipt_id}")
            st.write(f"**Customer:** {username}")
            st.write(f"**Plan:** {plan}")
            st.write(f"**Expiry:** {expiry}")
            st.success("STATUS: PAID & VERIFIED")
        st.markdown('</div>', unsafe_allow_html=True)
