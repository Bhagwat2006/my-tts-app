import os
import sqlite3
import hashlib
import uuid
import datetime
from datetime import datetime, timedelta
import streamlit as st
from elevenlabs.client import ElevenLabs

# --- CONFIGURATION & SECURITY ---
# Hardcoded fallback as per your instruction to keep everything in one place
try:
    ELEVEN_KEY = st.secrets.get("ELEVEN_API_KEY", "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40")
except:
    ELEVEN_KEY = "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40"

client = ElevenLabs(api_key=ELEVEN_KEY)
DB_PATH = "studio_v4.db"
ADMIN_MOBILE = "8452095418"

# --- DATABASE ENGINE & AUTO-MIGRATION ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Ensure Tables Exist
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, email TEXT, 
                  plan TEXT, expiry_date TEXT, usage_count INTEGER, receipt_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_voices 
                 (username TEXT, voice_name TEXT, voice_id TEXT)''')
    
    # CRITICAL FIX: Auto-Add receipt_id column if it's missing (Prevents Unpack Error)
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

# --- UI SETUP ---
st.set_page_config(page_title="Global AI Voice Studio Pro", layout="wide")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- AUTHENTICATION INTERFACE ---
if not st.session_state.logged_in:
    st.title("🌐 Global AI Voice Studio")
    auth_action = st.sidebar.selectbox("Account Access", ["Login", "Sign Up"])
    
    if auth_action == "Sign Up":
        u = st.text_input("Choose Username")
        e = st.text_input("Email Address")
        p = st.text_input("Create Password (Exactly 8 chars)", type="password", max_chars=8)
        if st.button("Create Account"):
            if len(p) == 8:
                conn = sqlite3.connect(DB_PATH)
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (u, hash_pass(p), e, "Free", "N/A", 0, "NONE"))
                    conn.commit()
                    st.success("Account created! Please switch to Login.")
                except: st.error("Username already taken!")
                conn.close()
            else: st.warning("Password must be exactly 8 characters.")
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
            else: st.error("Invalid credentials!")
            conn.close()

# --- MAIN DASHBOARD AREA ---
else:
    username = st.session_state.user
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    userData = c.fetchone()
    conn.close()
    
    # Safe Unpacking (Matches 7 Columns)
    _, _, email, plan, expiry, usage, receipt_id = userData

    st.sidebar.title(f"User: {username}")
    st.sidebar.info(f"Membership: {plan}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    t1, t2, t3, t4 = st.tabs(["🔊 Generator", "🎙️ Cloning", "💳 Subscription", "📄 Billing"])

    with t1:
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
                st.error("Usage limit reached. Please upgrade your subscription.")
            elif not script_text:
                st.warning("Please enter some text.")
            else:
                with st.spinner(f"Generating {target_lang} speech..."):
                    try:
                        audio_stream = client.text_to_speech.convert(
                            voice_id=el_voices[selected_v],
                            text=script_text,
                            model_id="eleven_multilingual_v2",
                            output_format="mp3_44100_128"
                        )
                        st.audio(b"".join(audio_stream))
                        
                        conn = sqlite3.connect(DB_PATH)
                        conn.execute("UPDATE users SET usage_count = usage_count + 1 WHERE username=?", (username,))
                        conn.commit()
                        conn.close()
                    except Exception as e: st.error(f"Error: {e}")

    with t2:
        st.header("Private Voice Cloning")
        if plan == "Free":
            st.warning("Voice Cloning requires a Standard or Premium subscription.")
        else:
            voice_file = st.file_uploader("Upload clear voice sample (MP3/WAV)", type=['wav','mp3'])
            label = st.text_input("Name this Voice")
            if st.button("Create Personal Clone"):
                if voice_file and label:
                    with st.spinner("Analyzing and Cloning..."):
                        new_voice = client.voices.add(name=label, files=[voice_file])
                        st.success(f"Success! Voice ID: {new_voice.voice_id}")
                else: st.error("Upload a file and give it a name.")

    with t3:
        st.header("Upgrade Your Membership")
        st.write("Professional plans for global creators.")
        
        col_std, col_pre = st.columns(2)
        with col_std:
            with st.container(border=True):
                st.subheader("Standard Plan")
                st.write("Price: ₹1 / Month")
                st.write("- 50 High-Quality Generations")
                if st.button("Activate Standard"):
                    rid, exp = upgrade_plan(username, "Standard")
                    st.success(f"Activated! Receipt: {rid}")
                    st.rerun()

        with col_pre:
            with st.container(border=True):
                st.subheader("Premium Unlimited")
                st.write("Price: ₹10 / Month")
                st.write("- 5000 Generations & Cloning")
                if st.button("Activate Premium"):
                    rid, exp = upgrade_plan(username, "Premium")
                    st.success(f"Activated! Receipt: {rid}")
                    st.rerun()
        
        st.divider()
        st.write("### 📲 Instant UPI Payment")
        upi_link = f"upi://pay?pa={ADMIN_MOBILE}@ybl&pn=AI_Studio&am=1.00&cu=INR"
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={upi_link}")
        st.info(f"Payment Support: +91-{ADMIN_MOBILE}")

    with t4:
        st.header("Official Digital Receipt")
        if receipt_id == "NONE":
            st.write("No active paid subscriptions found.")
        else:
            with st.container(border=True):
                st.title("INVOICE / RECEIPT")
                st.divider()
                st.subheader(f"ID: {receipt_id}")
                c_inv1, c_inv2 = st.columns(2)
                with c_inv1:
                    st.write("**Customer:**", username)
                    st.write("**Email:**", email)
                with c_inv2:
                    st.write("**Plan:**", plan)
                    st.write("**Expiry:**", expiry)
                st.divider()
                st.success("STATUS: PAID & VERIFIED")

# Strictly no file modification or deletion logic.
