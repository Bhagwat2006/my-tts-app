import os
import sqlite3
import hashlib
import uuid
import datetime
from datetime import datetime, timedelta
import streamlit as st
from elevenlabs.client import ElevenLabs

# --- UI & THEMING ---
st.set_page_config(page_title="Global AI Voice Studio Pro", layout="wide", page_icon="🎙️")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 5px; height: 3em; background-color: #6d28d9; color: white;}
    .stTextArea>div>div>textarea {background-color: #0e1117; color: #ffffff;}
    .css-1dp590f {padding-top: 2rem;}
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURATION & SECURITY ---
# Secure API Key Handling
ELEVEN_KEY = st.secrets.get("ELEVEN_API_KEY", "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40")
client = ElevenLabs(api_key=ELEVEN_KEY)
DB_PATH = "studio_v4.db"
ADMIN_MOBILE = "8452095418"

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, email TEXT, 
                 plan TEXT, expiry_date TEXT, usage_count INTEGER, receipt_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_voices 
                 (username TEXT, voice_name TEXT, voice_id TEXT)''')
    
    # Auto-Add receipt_id column if missing
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

init_db()

# --- AUTH LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.title("🌐 AI Voice Studio")
        auth_action = st.tabs(["Login", "Create Account"])
        
        with auth_action[1]:
            u = st.text_input("Username")
            e = st.text_input("Email")
            p = st.text_input("Password (8 chars)", type="password", max_chars=8)
            if st.button("Register"):
                if len(p) == 8:
                    try:
                        conn = sqlite3.connect(DB_PATH)
                        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (u, hash_pass(p), e, "Free", "N/A", 0, "NONE"))
                        conn.commit()
                        st.success("Account Ready!")
                    except: st.error("Username exists.")
                else: st.warning("Use 8 characters.")

        with auth_action[0]:
            u_log = st.text_input("Username", key="log_u")
            p_log = st.text_input("Password", type="password", key="log_p")
            if st.button("Login to Studio"):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u_log, hash_pass(p_log)))
                if c.fetchone():
                    st.session_state.logged_in = True
                    st.session_state.user = u_log
                    st.rerun()
                else: st.error("Wrong details.")

# --- MAIN STUDIO INTERFACE ---
else:
    username = st.session_state.user
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    _, _, email, plan, expiry, usage, receipt_id = c.fetchone()
    conn.close()

    # Sidebar Navigation & Stats
    with st.sidebar:
        st.title("🎙️ Studio Control")
        st.markdown(f"**User:** `{username}`")
        st.markdown(f"**Plan:** `{plan}`")
        
        limit = 3 if plan == "Free" else (100 if plan == "Standard" else 10000)
        progress = usage / limit
        st.progress(min(progress, 1.0))
        st.caption(f"Usage: {usage} / {limit} Generations")
        
        st.divider()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    t1, t2, t3, t4 = st.tabs(["🔊 Speech Synthesis", "🎙️ Voice Lab", "💳 Billing", "📜 Receipt"])

    with t1:
        st.subheader("Generate Natural Speech")
        
        c1, c2 = st.columns([2, 1])
        
        with c2:
            st.markdown("### Voice Settings")
            el_voices = {
                "Bella (Soft)": "21m00Tcm4TlvDq8ikWAM", 
                "Adam (Deep)": "pNInz6obpgDQGcFmaJgB", 
                "Antoni (News)": "erXw75RsuO7eL56y7m6F"
            }
            selected_v = st.selectbox("Base Model", list(el_voices.keys()))
            
            # --- ELEVENLABS PRO FEATURES ---
            st.info("Fine-tune your output:")
            stability = st.slider("Stability", 0.0, 1.0, 0.5, help="High: Consistent voice. Low: Emotional/Variable.")
            similarity = st.slider("Similarity", 0.0, 1.0, 0.75, help="Boosts likeness to the original speaker.")
            style = st.slider("Style Exaggeration", 0.0, 1.0, 0.0, help="Amplifies the character of the voice.")
            
        with c1:
            script_text = st.text_area("Script", height=300, placeholder="Once upon a time in a digital world...")
            char_count = len(script_text)
            st.caption(f"Characters: {char_count} | Estimated Cost: Free" if plan != "Free" else f"Characters: {char_count}")

            if st.button("⚡ Generate Professional Audio"):
                if usage >= limit:
                    st.error("Limit reached! Upgrade in Subscription tab.")
                elif not script_text:
                    st.warning("Input text first.")
                else:
                    with st.spinner("AI is thinking..."):
                        try:
                            audio_stream = client.text_to_speech.convert(
                                voice_id=el_voices[selected_v],
                                text=script_text,
                                model_id="eleven_multilingual_v2",
                                voice_settings={
                                    "stability": stability,
                                    "similarity_boost": similarity,
                                    "style": style
                                }
                            )
                            audio_bytes = b"".join(audio_stream)
                            st.audio(audio_bytes)
                            st.download_button("Download Audio", audio_bytes, file_name="speech.mp3", mime="audio/mp3")
                            
                            # Update Usage
                            conn = sqlite3.connect(DB_PATH)
                            conn.execute("UPDATE users SET usage_count = usage_count + 1 WHERE username=?", (username,))
                            conn.commit()
                            conn.close()
                        except Exception as e:
                            st.error(f"API Error: {e}")

    with t2:
        st.header("Voice Cloning (Pro)")
        if plan == "Free":
            st.warning("Standard or Premium required for Cloning.")
        else:
            v_file = st.file_uploader("Upload Sample", type=['mp3', 'wav'])
            v_name = st.text_input("Voice Name")
            if st.button("Start Cloning") and v_file and v_name:
                with st.spinner("Processing biological voice data..."):
                    new_v = client.voices.add(name=v_name, files=[v_file])
                    st.success(f"Voice Created: {new_v.voice_id}")

    with t3:
        st.header("Upgrade Studio")
        sc1, sc2 = st.columns(2)
        with sc1:
            with st.container(border=True):
                st.subheader("Standard")
                st.markdown("₹1 / Mo\n- 100 Gens\n- Voice Cloning")
                if st.button("Get Standard"):
                    upgrade_plan(username, "Standard")
                    st.rerun()
        with sc2:
            with st.container(border=True):
                st.subheader("Premium")
                st.markdown("₹10 / Mo\n- Unlimited Gen\n- Ultra HQ Audio")
                if st.button("Get Premium"):
                    upgrade_plan(username, "Premium")
                    st.rerun()

    with t4:
        st.header("Your Invoices")
        if receipt_id != "NONE":
            st.code(f"RECEIPT ID: {receipt_id}\nUSER: {username}\nPLAN: {plan}\nEXPIRY: {expiry}\nSTATUS: PAID")
        else:
            st.write("No payments yet.")
