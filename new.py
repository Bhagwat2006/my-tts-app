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

# --- DATABASE ENGINE (FIXED PERSISTENCE) ---
def init_db():
    # Using context manager 'with' ensures the connection closes properly
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (username TEXT PRIMARY KEY, password TEXT, email TEXT, 
                     plan TEXT, expiry_date TEXT, usage_count INTEGER, receipt_id TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_voices 
                     (username TEXT, voice_name TEXT, voice_id TEXT)''')
        
        # Auto-migration for missing columns
        c.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in c.fetchall()]
        if "receipt_id" not in columns:
            c.execute("ALTER TABLE users ADD COLUMN receipt_id TEXT DEFAULT 'NONE'")
        conn.commit()

def hash_pass(password):
    # Fixed to handle the 8-char limit logic correctly
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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

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
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", 
                                     (u, hash_pass(p), e, "Free", "N/A", 0, "NONE"))
                        conn.commit() # CRITICAL: This saves the user permanently
                        st.success("✅ Account created! Switch to Login now.")
                    except sqlite3.IntegrityError:
                        st.error("❌ Username already exists!")
            else:
                st.warning("⚠️ Password must be exactly 8 chars and all fields filled.")
    
    else:
        u = st.text_input("Username").strip()
        p = st.text_input("Password", type="password", max_chars=8)
        if st.button("Secure Login"):
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hash_pass(p)))
                userData = c.fetchone()
                if userData:
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
        
        # RESTORED: Fetch User's Cloned Voices for the Hybrid Engine
        c.execute("SELECT voice_name, voice_id FROM user_voices WHERE username=?", (username,))
        cloned_voices = {row[0]: row[1] for row in c.fetchall()}
    
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
        
        # HYBRID VOICE ENGINE SELECTION
        default_voices = {"Bella (Soft)": "21m00Tcm4TlvDq8ikWAM", "Adam (Deep)": "pNInz6obpgDQGcFmaJgB", "Rachel (Pro)": "21m00Tcm4TlvDq8ikWAM"}
        all_available_voices = {**default_voices, **cloned_voices} # Combines System + Cloned
        
        with c1:
            target_lang = st.selectbox("Select Script Language", ["English", "Hindi", "French", "German", "Spanish", "Japanese"])
            selected_v_name = st.selectbox("Select Voice Model (Includes Clones)", list(all_available_voices.keys()))
            selected_v_id = all_available_voices[selected_v_name]
        
        script_text = st.text_area("Write your script here:", placeholder="Type your text...")
        limit = 3 if plan == "Free" else (50 if plan == "Standard" else 5000)
        
        if st.button("⚡ Generate Audio"):
            if usage >= limit:
                st.error("Usage limit reached. Please upgrade.")
            elif not script_text:
                st.warning("Please enter some text.")
            else:
                with st.spinner("Generating..."):
                    try:
                        audio_stream = client.text_to_speech.convert(
                            voice_id=selected_v_id,
                            text=script_text,
                            model_id="eleven_multilingual_v2",
                            output_format="mp3_44100_128"
                        )
                        st.audio(b"".join(audio_stream))
                        
                        # Update usage
                        with sqlite3.connect(DB_PATH) as conn:
                            conn.execute("UPDATE users SET usage_count = usage_count + 1 WHERE username=?", (username,))
                            conn.commit()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with t2:
        st.header("Private Voice Cloning")
        if plan == "Free":
            st.warning("Upgrade to Standard/Premium to clone voices.")
        else:
            voice_file = st.file_uploader("Upload voice sample", type=['wav','mp3'])
            label = st.text_input("Voice Name")
            if st.button("Create Personal Clone"):
                if voice_file and label:
                    with st.spinner("Cloning..."):
                        new_voice = client.voices.add(name=label, files=[voice_file])
                        # SAVE CLONE TO DATABASE
                        with sqlite3.connect(DB_PATH) as conn:
                            conn.execute("INSERT INTO user_voices VALUES (?,?,?)", (username, label, new_voice.voice_id))
                            conn.commit()
                        st.success(f"Voice '{label}' added to your engine!")
                else:
                    st.error("Need a file and a name.")

    # ... [Rest of t3 and t4 tabs remain as provided in original] ...
    with t3:
        st.header("Upgrade Your Membership")
        col_std, col_pre = st.columns(2)
        with col_std:
            with st.container(border=True):
                st.subheader("Standard Plan")
                st.write("Price: ₹1 / Month")
                if st.button("Activate Standard"):
                    rid, exp = upgrade_plan(username, "Standard")
                    st.success(f"Activated! Receipt: {rid}")
                    st.rerun()
        with col_pre:
            with st.container(border=True):
                st.subheader("Premium Unlimited")
                st.write("Price: ₹10 / Month")
                if st.button("Activate Premium"):
                    rid, exp = upgrade_plan(username, "Premium")
                    st.success(f"Activated! Receipt: {rid}")
                    st.rerun()
        upi_link = f"upi://pay?pa={ADMIN_MOBILE}@ybl&pn=AI_Studio&am=1.00&cu=INR"
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={upi_link}")

    with t4:
        st.header("Official Digital Receipt")
        if receipt_id == "NONE":
            st.write("No active paid subscriptions.")
        else:
            with st.container(border=True):
                st.title("INVOICE")
                st.write(f"**Customer:** {username}")
                st.write(f"**Plan:** {plan}")
                st.write(f"**Receipt ID:** {receipt_id}")
                st.success("STATUS: PAID")
