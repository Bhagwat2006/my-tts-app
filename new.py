import os
import sqlite3
import hashlib
import uuid
import datetime
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components
from elevenlabs.client import ElevenLabs
import speech_recognition as sr  # Added for voice-to-voice commands

# --- CONFIGURATION & SECURITY ---
try:
    ELEVEN_KEY = st.secrets.get("ELEVEN_API_KEY", "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40")
except:
    ELEVEN_KEY = "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40"

client = ElevenLabs(api_key=ELEVEN_KEY)
DB_PATH = "studio_v4.db"
ADMIN_MOBILE = "8452095418"

# --- 🚀 FUTURISTIC 3D UI & ANIMATIONS ---
def inject_3d_engine():
    # CSS for Glassmorphism and Transitions
    st.markdown("""
        <style>
        .main { background: #0a0a0f; color: white; }
        .stTabs [data-baseweb="tab-list"] { gap: 20px; }
        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px 10px 0 0;
            padding: 10px 20px;
            transition: all 0.5s ease;
        }
        .stTabs [aria-selected="true"] { 
            background: linear-gradient(45deg, #00f2fe, #4facfe) !important;
            box-shadow: 0 0 15px #4facfe;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            animation: fadeIn 1.5s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        </style>
    """, unsafe_allow_html=True)

    # 3D Particles Javascript (Reacts to the environment)
    components.html("""
        <div id="particles-js" style="position: fixed; width: 100vw; height: 100vh; top: 0; left: 0; z-index: -1;"></div>
        <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
        <script>
            particlesJS('particles-js', {
                "particles": {
                    "number": {"value": 100, "density": {"enable": true, "value_area": 800}},
                    "color": {"value": "#4facfe"},
                    "shape": {"type": "circle"},
                    "opacity": {"value": 0.5, "random": true},
                    "size": {"value": 3, "random": true},
                    "line_linked": {"enable": true, "distance": 150, "color": "#00f2fe", "opacity": 0.4, "width": 1},
                    "move": {"enable": true, "speed": 2, "direction": "none", "random": true, "straight": false}
                },
                "interactivity": {
                    "detect_on": "canvas",
                    "events": {"onhover": {"enable": true, "mode": "grab"}, "onclick": {"enable": true, "mode": "push"}}
                }
            });
        </script>
    """, height=0)

# --- VOICE COMMAND LOADER ---
def listen_for_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.toast("🎙️ Listening for Voice Command...")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            return r.recognize_google(audio).lower()
        except: return None

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

def hash_pass(password):
    return hashlib.sha256(str.encode(password[:8])).hexdigest()

def upgrade_plan(username, plan_type):
    receipt_id = f"REC-{uuid.uuid4().hex[:8].upper()}"
    expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET plan=?, expiry_date=?, usage_count=0, receipt_id=? WHERE username=?", 
                 (plan_type, expiry, receipt_id, username))
    conn.commit()
    conn.close()
    return receipt_id, expiry

# --- APP START ---
st.set_page_config(page_title="V4 Futuristic Voice Studio", layout="wide")
inject_3d_engine()
init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- AUTHENTICATION ---
if not st.session_state.logged_in:
    st.title("🌐 Global AI Voice Studio")
    auth_action = st.sidebar.selectbox("Account Access", ["Login", "Sign Up"])
    
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if auth_action == "Sign Up":
            u = st.text_input("Choose Username")
            e = st.text_input("Email Address")
            p = st.text_input("Password (8 chars)", type="password", max_chars=8)
            if st.button("Create Account"):
                if len(p) == 8:
                    conn = sqlite3.connect(DB_PATH)
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (u, hash_pass(p), e, "Free", "N/A", 0, "NONE"))
                        conn.commit()
                        st.success("Account Created!")
                    except: st.error("User already exists")
                    conn.close()
        else:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password", max_chars=8)
            if st.button("Secure Login"):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hash_pass(p)))
                userData = c.fetchone()
                if userData:
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Invalid credentials")
                conn.close()
        st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN DASHBOARD ---
else:
    username = st.session_state.user
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    userData = c.fetchone()
    conn.close()
    
    _, _, email, plan, expiry, usage, receipt_id = userData

    # Navigation Sidebar
    st.sidebar.title(f"User: {username}")
    st.sidebar.info(f"Membership: {plan}")
    
    # VOICE TO COMMAND TRIGGER
    if st.sidebar.button("🎙️ Speak Command"):
        cmd = listen_for_command()
        if cmd:
            st.sidebar.write(f"Recognized: **{cmd}**")
            if "logout" in cmd:
                st.session_state.logged_in = False
                st.rerun()

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # TABS WITH ANIMATED UI
    t1, t2, t3, t4 = st.tabs(["🔊 Generator", "🎙️ Cloning", "💳 Subscription", "📄 Billing"])

    with t1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.header("Studio-Quality AI Generation")
        c1, c2 = st.columns(2)
        with c1:
            target_lang = st.selectbox("Select Script Language", ["English", "Hindi", "French", "German", "Spanish", "Japanese"])
            el_voices = {"Bella (Soft)": "21m00Tcm4TlvDq8ikWAM", "Adam (Deep)": "pNInz6obpgDQGcFmaJgB", "Rachel (Pro)": "21m00Tcm4TlvDq8ikWAM"}
            selected_v = st.selectbox("Select Voice Model", list(el_voices.keys()))
        
        script_text = st.text_area("Write your script here:", placeholder="Type your text...")
        limit = 3 if plan == "Free" else (50 if plan == "Standard" else 5000)
        
        if st.button("⚡ Generate Audio"):
            if usage >= limit:
                st.error("Upgrade Required.")
            elif not script_text:
                st.warning("Enter text first.")
            else:
                with st.spinner("AI Synthesis in progress..."):
                    try:
                        audio_stream = client.text_to_speech.convert(
                            voice_id=el_voices[selected_v],
                            text=script_text,
                            model_id="eleven_multilingual_v2",
                            output_format="mp3_44100_128"
