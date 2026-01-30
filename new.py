import os
import hashlib
import uuid
import asyncio
import datetime
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import edge_tts
from gtts import gTTS
import io
import pandas as pd
from supabase import create_client, Client

# --- PAGE CONFIG ---
st.set_page_config(page_title="Global AI Studio Pro", page_icon="🎙️", layout="wide")

# --- DATABASE ---
@st.cache_resource
def get_supabase_client():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = get_supabase_client()

# --- CONFIG ---
ADMIN_PASSWORD = "ADMIN@123"
ELEVEN_KEY = st.secrets.get("ELEVEN_API_KEY", "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40")
client = ElevenLabs(api_key=ELEVEN_KEY)
UPI_ID = "8452095418@ybl"

# --- VOICE PRESETS ---
VOICE_MODELS = {
    "Madhur (Male)": {"id": "hi-IN-MadhurNeural", "lang": "Hindi", "preview": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"},
    "Swara (Female)": {"id": "hi-IN-SwaraNeural", "lang": "Hindi", "preview": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"},
    "English - Adam": {"id": "en-US-AdamMultilingual", "lang": "English", "preview": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"},
    "English - Bella": {"id": "en-US-BellaNeural", "lang": "English", "preview": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"}
}

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- CSS FOR SPEED & 3D ---
st.markdown("""
    <style>
    .stApp { background: #0f0c29; color: white; }
    div[data-testid="stSidebarNav"] { display: none; }
    .stButton>button { width: 100%; border-radius: 12px; transition: 0.2s; background: linear-gradient(45deg, #6e8efb, #a7b7fb); color: white; }
    .stButton>button:hover { transform: scale(1.02); }
    .glass-card { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); }
    </style>
""", unsafe_allow_html=True)

# --- ENGINE ---
async def generate_voice(text, voice_id, rate, pitch):
    communicate = edge_tts.Communicate(text, voice_id, rate=rate, pitch=pitch)
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": data += chunk["data"]
    return data

# --- APP START ---
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = "Studio"
if 'auth_mode' not in st.session_state: st.session_state.auth_mode = "Login"

# --- AUTHENTICATION SCREEN ---
if not st.session_state.user:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🚀 Global AI Studio")
        
        # LOGIN MODE
        if st.session_state.auth_mode == "Login":
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login"):
                res = supabase.table("users").select("*").eq("username", u).eq("password", hash_pass(p)).execute()
                if res.data: 
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Invalid Login Credentials")
            
            col_l, col_r = st.columns(2)
            if col_l.button("New User? Register"):
                st.session_state.auth_mode = "Register"
                st.rerun()
            if col_r.button("Forgot Password?"):
                st.session_state.auth_mode = "Forgot"
                st.rerun()

        # REGISTRATION MODE
        elif st.session_state.auth_mode == "Register":
            st.subheader("Create New Account")
            new_u = st.text_input("Choose Username")
            new_p = st.text_input("Choose Password", type="password")
            confirm_p = st.text_input("Confirm Password", type="password")
            
            if st.button("Sign Up"):
                if new_p != confirm_p:
                    st.error("Passwords do not match!")
                elif len(new_u) < 3:
                    st.error("Username too short!")
                else:
                    # Check if user exists
                    check = supabase.table("users").select("username").eq("username", new_u).execute()
                    if check.data:
                        st.error("Username already exists!")
                    else:
                        supabase.table("users").insert({
                            "username": new_u, 
                            "password": hash_pass(new_p),
                            "plan": "Free",
                            "usage_count": 0
                        }).execute()
                        st.success("Registration Successful! Please Login.")
                        st.session_state.auth_mode = "Login"
                        st.rerun()
            
            if st.button("Back to Login"):
                st.session_state.auth_mode = "Login"
                st.rerun()

        # FORGOT PASSWORD MODE
        elif st.session_state.auth_mode == "Forgot":
            st.subheader("Account Recovery")
            st.info("Please enter your username to verify your account.")
            u_recover = st.text_input("Username")
            if st.button("Verify & Reset"):
                res = supabase.table("users").select("*").eq("username", u_recover).execute()
                if res.data:
                    st.success(f"Account verified! Contact Admin at {UPI_ID} for manual reset.")
                else:
                    st.error("User not found.")
            
            if st.button("Back to Login"):
                st.session_state.auth_mode = "Login"
                st.rerun()

# --- MAIN APP INTERFACE ---
else:
    # --- GET DATA ---
    res = supabase.table("users").select("*").eq("username", st.session_state.user).execute()
    u_info = res.data[0]

    # --- FAST SIDEBAR ---
    with st.sidebar:
        st.title(f"Hi, {st.session_state.user}")
        if st.button("✨ Studio"): st.session_state.page = "Studio"; st.rerun()
        if st.button("🧬 Cloning"): st.session_state.page = "Cloning"; st.rerun()
        if st.button("💳 Upgrade"): st.session_state.page = "Billing"; st.rerun()
        if st.button("🛠️ Admin"): st.session_state.page = "Admin"; st.rerun()
        st.divider()
        if st.button("🚪 Logout"): 
            st.session_state.user = None
            st.session_state.auth_mode = "Login"
            st.rerun()

    # --- STUDIO PAGE ---
    if st.session_state.page == "Studio":
        st.header("🎙️ Advanced Voice Lab")
        
        # Voice Selection Gallery
        st.subheader("1. Select Your AI Voice Model")
        cols = st.columns(len(VOICE_MODELS))
        
        for i, (name, data) in enumerate(VOICE_MODELS.items()):
            with cols[i]:
                st.markdown(f"**{name}**")
                st.caption(data['lang'])
                st.audio(data['preview'], format="audio/mp3")
                if st.button(f"Select {name.split()[0]}", key=f"btn_{i}"):
                    st.session_state.v_id = data['id']
                    st.success(f"Selected: {name}")

        st.divider()
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("2. Script & Generation")
            txt = st.text_area("Write Script Here", height=200)
            
            with st.expander("🎚️ Audio Fine-Tuning"):
                s_rate = st.slider("Speed", 0.5, 2.0, 1.0)
                s_pitch = st.slider("Pitch", -20, 20, 0)
            
            if st.button("⚡ Generate Audio Now"):
                if not txt: st.warning("Please enter text.")
                else:
                    with st.spinner("Processing..."):
                        try:
                            v_to_use = st.session_state.get('v_id', "hi-IN-MadhurNeural")
                            r_str = f"{int((s_rate-1)*100)}%"
                            p_str = f"{s_pitch}Hz"
                            
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            audio_data = loop.run_until_complete(generate_voice(txt, v_to_use, r_str, p_str))
                            
                            if audio_data:
                                st.audio(audio_data)
                                st.download_button("📥 Download MP3", audio_data, "voice.mp3")
                                supabase.table("users").update({"usage_count": u_info['usage_count']+1}).eq("username", st.session_state.user).execute()
                                st.rerun() # Refresh stats
                        except Exception as e: st.error(f"Error: {e}")
        
        with c2:
            st.markdown(f"""
            <div class="glass-card">
            <h3>User Stats</h3>
            <p>Plan: <b>{u_info['plan']}</b></p>
            <p>Usage: <b>{u_info['usage_count']}</b></p>
            </div>
            """, unsafe_allow_html=True)

    # --- BILLING PAGE ---
    elif st.session_state.page == "Billing":
        st.header("💳 Upgrade Plan")
        col1, col2 = st.columns(2)
        with col1:
            st.info("Standard - ₹1")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?data=upi://pay?pa={UPI_ID}%26am=1.00")
        with col2:
            st.success("Premium - ₹10")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?data=upi://pay?pa={UPI_ID}%26am=10.00")

    # --- ADMIN PAGE ---
    elif st.session_state.page == "Admin":
        st.header("🛡️ Admin Panel")
        if st.text_input("Master Key", type="password") == ADMIN_PASSWORD:
            users_res = supabase.table("users").select("*").execute()
            st.table(pd.DataFrame(users_res.data))
