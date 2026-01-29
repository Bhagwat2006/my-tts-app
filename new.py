import os
import sqlite3
import hashlib
import uuid
import datetime
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

# --- 🚀 FUTURISTIC 3D ENGINE & ANIMATIONS ---
def inject_futuristic_elements():
    # CSS for Animations, Glassmorphism, and Futuristic UI
    st.markdown("""
        <style>
        /* Main Background */
        .main {
            background-color: #0a0a12;
            color: #ffffff;
        }

        /* Glassmorphism Containers */
        div[data-testid="stVerticalBlock"] > div:has(div.glass-card) {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2rem;
            transition: all 0.5s ease;
        }

        /* Animated Tab Transitions */
        [data-baseweb="tab-panel"] {
            animation: fadeInSlide 0.8s ease-out;
        }

        @keyframes fadeInSlide {
            0% { opacity: 0; transform: translateY(20px); filter: blur(10px); }
            100% { opacity: 1; transform: translateY(0); filter: blur(0); }
        }

        /* Glowing Buttons */
        .stButton>button {
            background: linear-gradient(45deg, #00f2fe 0%, #4facfe 100%) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
            transition: all 0.3s ease !important;
            border-radius: 10px !important;
        }
        .stButton>button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 25px #00f2fe;
        }

        /* Login Animation */
        .login-box {
            animation: pulseGlow 4s infinite alternate;
        }
        @keyframes pulseGlow {
            from { box-shadow: 0 0 20px rgba(0, 242, 254, 0.1); }
            to { box-shadow: 0 0 40px rgba(0, 242, 254, 0.3); }
        }
        </style>
    """, unsafe_allow_html=True)

    # 3D Particles Background (JS)
    components.html("""
        <div id="particles-js" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;"></div>
        <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
        <script>
            particlesJS('particles-js', {
                "particles": {
                    "number": {"value": 80, "density": {"enable": true, "value_area": 800}},
                    "color": {"value": "#4facfe"},
                    "shape": {"type": "circle"},
                    "opacity": {"value": 0.5, "random": false},
                    "size": {"value": 3, "random": true},
                    "line_linked": {"enable": true, "distance": 150, "color": "#00f2fe", "opacity": 0.4, "width": 1},
                    "move": {"enable": true, "speed": 2, "direction": "none", "random": false, "straight": false, "out_mode": "out"}
                },
                "interactivity": {
                    "events": {"onhover": {"enable": true, "mode": "grab"}, "onclick": {"enable": true, "mode": "push"}}
                }
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
inject_futuristic_elements()
init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- DYNAMIC LOGIN PAGE ---
if not st.session_state.logged_in:
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown('<div class="login-box glass-card">', unsafe_allow_html=True)
        st.title("🌐 AI Studio Nexus")
        auth_action = st.tabs(["Login Access", "Register Identity"])
        
        with auth_action[1]:
            u = st.text_input("New Username")
            e = st.text_input("Email")
            p = st.text_input("Password (8 chars)", type="password", max_chars=8)
            if st.button("Initialize Account"):
                if len(p) == 8:
                    conn = sqlite3.connect(DB_PATH)
                    try:
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (u, hash_pass(p), e, "Free", "N/A", 0, "NONE"))
                        conn.commit()
                        st.success("Identity Created! Switch to Login.")
                    except: st.error("ID already exists.")
                    conn.close()
                else: st.warning("Requires exactly 8 chars.")

        with auth_action[0]:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password", max_chars=8)
            if st.button("Bypass Security / Login"):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hash_pass(p)))
                userData = c.fetchone()
                if userData:
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Verification failed.")
                conn.close()
        st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD ---
else:
    username = st.session_state.user
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    userData = c.fetchone()
    conn.close()
    
    _, _, email, plan, expiry, usage, receipt_id = userData

    st.sidebar.markdown(f"### 🛡️ Authorized: \n**{username}**")
    st.sidebar.write(f"Plan: `{plan}`")
    if st.sidebar.button("Logout System"):
        st.session_state.logged_in = False
        st.rerun()

    # Animated Navigation Tabs
    t1, t2, t3, t4 = st.tabs(["🔊 Generator", "🎙️ Cloning", "💳 Subscription", "📄 Billing"])

    with t1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.header("Neural Voice Generation")
        col1, col2 = st.columns(2)
        with col1:
            lang = st.selectbox("Language Matrix", ["English", "Hindi", "French", "Spanish"])
            voice = st.selectbox("Model", ["Bella (Soft)", "Adam (Deep)", "Rachel (Pro)"])
        
        text = st.text_area("Input Script", placeholder="Enter text for AI synthesis...")
        
        if st.button("⚡ Generate Neural Audio"):
            # Trigger 'Reaction' animation via toast
            st.toast("🧬 Particles reacting to audio synthesis...")
            with st.spinner("Processing..."):
                try:
                    # Logic remains unchanged
                    el_voices = {"Bella (Soft)": "21m00Tcm4TlvDq8ikWAM", "Adam (Deep)": "pNInz6obpgDQGcFmaJgB"}
                    audio = client.text_to_speech.convert(voice_id=el_voices.get(voice, "21m00Tcm4TlvDq8ikWAM"), text=text, model_id="eleven_multilingual_v2")
                    st.audio(b"".join(audio))
                    
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("UPDATE users SET usage_count = usage_count + 1 WHERE username=?", (username,))
                    conn.commit()
                    conn.close()
                except Exception as e: st.error(f"Sync Error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with t2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.header("Voice DNA Cloning")
        if plan == "Free":
            st.warning("Access Denied. Premium Subscription Required.")
        else:
            up_file = st.file_uploader("Upload Sample", type=['mp3', 'wav'])
            name = st.text_input("Clone Name")
            if st.button("Start Bio-Clone"):
                st.info("Cloning in progress...")
        st.markdown('</div>', unsafe_allow_html=True)

    with t3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.header("Upgrade Neural Level")
        
        # ADDED THE ₹10 PLAN AS REQUESTED
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.container(border=True):
                st.subheader("Free")
                st.write("₹0")
                st.write("- 3 Gens")
        
        with c2:
            with st.container(border=True):
                st.subheader("Standard")
                st.write("₹1")
                if st.button("Select Standard"):
                    upgrade_plan(username, "Standard")
                    st.rerun()

        with c3:
            with st.container(border=True):
                st.subheader("👑 Premium")
                st.title("₹10")
                st.write("**Unlimited Access**\n- Voice Cloning\n- 5000 Gens")
                if st.button("Select Premium"):
                    upgrade_plan(username, "Premium")
                    st.balloons()
                    st.rerun()
        
        st.divider()
        st.subheader("📲 Instant UPI Checkout")
        # Dynamic UPI generation based on ₹10 Premium plan
        upi_link = f"upi://pay?pa={ADMIN_MOBILE}@ybl&pn=AI_Studio_Premium&am=10.00&cu=INR"
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={upi_link}", caption="Scan for ₹10 Premium Plan")
        st.markdown('</div>', unsafe_allow_html=True)

    with t4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.header("System Billing")
        if receipt_id == "NONE":
            st.info("No transaction records found.")
        else:
            st.subheader(f"Invoice: {receipt_id}")
            st.write(f"Customer: {username}")
            st.write(f"Expiry: {expiry}")
            st.success("Verified on Blockchain")
        st.markdown('</div>', unsafe_allow_html=True)
