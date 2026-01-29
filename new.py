import os
import uuid
import hashlib
import asyncio
import edge_tts
import streamlit as st
from datetime import datetime, timedelta
from elevenlabs.client import ElevenLabs
from supabase import create_client, Client

# --- CLOUD DATABASE CONNECT ---
# Set these in Streamlit Cloud -> Settings -> Secrets
URL = st.secrets.get("SUPABASE_URL", "https://tipnrzvalmbgyegrwxxr.supabase.co")
KEY = st.secrets.get("SUPABASE_KEY", "sb_publishable_GNV3cJIH9dX7PI0p9id6hw_RUQVsfUd")
supabase: Client = create_client(URL, KEY)

# --- ELEVENLABS CONFIG ---
try:
    ELEVEN_KEY = st.secrets.get("ELEVEN_API_KEY", "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40")
except:
    ELEVEN_KEY = "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40"

client = ElevenLabs(api_key=ELEVEN_KEY)
ADMIN_MOBILE = "8452095418"

# --- AUTH LOGIC ---
def hash_pass(password):
    return hashlib.sha256(str.encode(password[:8])).hexdigest()

async def generate_free_voice(text, voice_id):
    communicate = edge_tts.Communicate(text, voice_id)
    temp_file = f"free_{uuid.uuid4().hex}.mp3"
    await communicate.save(temp_file)
    return temp_file

# --- APP START ---
st.set_page_config(page_title="Global AI Voice Studio Pro", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- LOGIN / SIGNUP ---
if not st.session_state.logged_in:
    st.title("🌐 Global AI Voice Studio")
    auth_action = st.sidebar.selectbox("Account Access", ["Login", "Sign Up"])
    
    if auth_action == "Sign Up":
        u = st.text_input("Choose Username")
        e = st.text_input("Email Address")
        p = st.text_input("Create Password (8 chars)", type="password", max_chars=8)
        if st.button("Create Account"):
            if len(p) == 8:
                try:
                    data = {"username": u, "password": hash_pass(p), "email": e, "plan": "Free", "expiry_date": "N/A", "usage_count": 0, "receipt_id": "NONE"}
                    supabase.table("users").insert(data).execute()
                    st.success("Account created on Cloud! Please Login.")
                except Exception as ex: st.error(f"Error: {ex}")
            else: st.warning("Password must be 8 characters.")
    else:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password", max_chars=8)
        if st.button("Secure Login"):
            res = supabase.table("users").select("*").eq("username", u).eq("password", hash_pass(p)).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.rerun()
            else: st.error("Invalid credentials!")

# --- DASHBOARD ---
else:
    username = st.session_state.user
    res = supabase.table("users").select("*").eq("username", username).execute()
    userData = res.data[0]
    
    # Safe Unpacking
    email = userData['email']
    plan = userData['plan']
    expiry = userData['expiry_date']
    usage = userData['usage_count']
    receipt_id = userData['receipt_id']

    st.sidebar.title(f"User: {username}")
    st.sidebar.info(f"Membership: {plan}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    t1, t2, t3, t4 = st.tabs(["🔊 Generator", "🎙️ Cloning", "💳 Subscription", "📄 Billing"])

    with t1:
        st.header("Studio-Quality AI Generation")
        engine_choice = st.radio("Select Generation Engine:", ["ElevenLabs (Premium)", "Free Server (No Error)"], horizontal=True)
        
        c1, c2 = st.columns(2)
        with c1:
            target_lang = st.selectbox("Select Script Language", ["English", "Hindi", "French", "German", "Spanish", "Japanese"])
            if engine_choice == "ElevenLabs (Premium)":
                el_voices = {"Bella (Soft)": "21m00Tcm4TlvDq8ikWAM", "Adam (Deep)": "pNInz6obpgDQGcFmaJgB", "Rachel (Pro)": "21m00Tcm4TlvDq8ikWAM"}
                selected_v = st.selectbox("Select ElevenLabs Voice", list(el_voices.keys()))
            else:
                free_voices = {"English": "en-US-AvaNeural", "Hindi": "hi-IN-MadhurNeural", "French": "fr-FR-EloiseNeural", "German": "de-DE-KatjaNeural", "Spanish": "es-ES-AlvaroNeural", "Japanese": "ja-JP-NanamiNeural"}
                selected_v_id = free_voices[target_lang]
        
        script_text = st.text_area("Write your script here:")
        limit = 3 if plan == "Free" else (50 if plan == "Standard" else 5000)
        
        if st.button("⚡ Generate Audio"):
            if usage >= limit:
                st.error("Limit reached. Please upgrade.")
            elif not script_text:
                st.warning("Enter text.")
            else:
                with st.spinner("Generating..."):
                    try:
                        if engine_choice == "ElevenLabs (Premium)":
                            audio = client.text_to_speech.convert(voice_id=el_voices[selected_v], text=script_text, model_id="eleven_multilingual_v2")
                            st.audio(b"".join(audio))
                        else:
                            temp_audio = asyncio.run(generate_free_voice(script_text, selected_v_id))
                            with open(temp_audio, "rb") as f: st.audio(f.read())
                            os.remove(temp_audio)
                        
                        # Update Cloud Usage Count
                        supabase.table("users").update({"usage_count": usage + 1}).eq("username", username).execute()
                    except Exception as e: st.error(f"Error: {e}")

    with t3:
        st.header("Upgrade Your Membership")
        col_std, col_pre = st.columns(2)
        with col_std:
            if st.button("Activate Standard (₹1)"):
                new_rid = f"REC-{uuid.uuid4().hex[:8].upper()}"
                new_exp = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                supabase.table("users").update({"plan": "Standard", "expiry_date": new_exp, "usage_count": 0, "receipt_id": new_rid}).eq("username", username).execute()
                st.success("Activated!"); st.rerun()

        st.divider()
        st.write("### 📲 Instant UPI Payment")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=upi://pay?pa={ADMIN_MOBILE}@ybl&pn=AI_Studio&am=1.00&cu=INR")

# Note: Billing and Cloning tabs follow the same logic as before.
