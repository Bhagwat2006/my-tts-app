# ==============================
# GLOBAL AI STUDIO PRO (PROD)
# ==============================

import os
import hashlib
import asyncio
import logging
from datetime import datetime

import streamlit as st
import pandas as pd
import edge_tts
from supabase import create_client, Client
from elevenlabs.client import ElevenLabs

# ------------------------------
# APP CONFIG
# ------------------------------
st.set_page_config(
    page_title="Global AI Studio Pro",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# LOGGING (PRODUCTION LEVEL)
# ------------------------------
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

# ------------------------------
# SECURITY CONSTANTS
# ------------------------------
ADMIN_PASSWORD = "ADMIN@123"
UPI_ID = "8452095418@ybl"

# ------------------------------
# SECRETS VALIDATION
# ------------------------------
REQUIRED_SECRETS = ["SUPABASE_URL", "SUPABASE_KEY", "ELEVEN_API_KEY"]
missing = [k for k in REQUIRED_SECRETS if k not in st.secrets]
if missing:
    st.error(f"Missing secrets: {', '.join(missing)}")
    st.stop()

# ------------------------------
# DATABASE
# ------------------------------
@st.cache_resource(show_spinner=False)
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = get_supabase()

# ------------------------------
# VOICE CLIENT
# ------------------------------
eleven_client = ElevenLabs(api_key=st.secrets["ELEVEN_API_KEY"])

VOICE_MODELS = {
    "Madhur (Male)": {"id": "hi-IN-MadhurNeural", "lang": "Hindi"},
    "Swara (Female)": {"id": "hi-IN-SwaraNeural", "lang": "Hindi"},
    "English - Adam": {"id": "en-US-AdamMultilingual", "lang": "English"},
    "English - Bella": {"id": "en-US-BellaNeural", "lang": "English"},
}

# ------------------------------
# UTILITIES
# ------------------------------
def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()

def require_login():
    if not st.session_state.get("user"):
        st.warning("Please login to continue.")
        st.stop()

def safe_rerun():
    st.experimental_set_query_params()
    st.rerun()

# ------------------------------
# ASYNC VOICE ENGINE (SAFE)
# ------------------------------
async def _edge_tts(text, voice, rate, pitch):
    tts = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    audio = b""
    async for chunk in tts.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
    return audio

def generate_voice_sync(text, voice, rate, pitch):
    return asyncio.run(_edge_tts(text, voice, rate, pitch))

# ------------------------------
# SESSION STATE INIT
# ------------------------------
for key, default in {
    "user": None,
    "page": "Studio",
    "auth_mode": "Login",
    "voice_id": "hi-IN-MadhurNeural"
}.items():
    st.session_state.setdefault(key, default)

# ==============================
# AUTHENTICATION
# ==============================
if not st.session_state.user:
    st.markdown("## 🚀 Global AI Studio Pro")

    if st.session_state.auth_mode == "Login":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            res = supabase.table("users").select("*")\
                .eq("username", u)\
                .eq("password", hash_password(p))\
                .execute()

            if res.data:
                st.session_state.user = u
                safe_rerun()
            else:
                st.error("Invalid credentials")

        col1, col2 = st.columns(2)
        if col1.button("Register"):
            st.session_state.auth_mode = "Register"
            safe_rerun()
        if col2.button("Forgot Password"):
            st.session_state.auth_mode = "Forgot"
            safe_rerun()

    elif st.session_state.auth_mode == "Register":
        st.subheader("Create Account")
        u = st.text_input("Username")
        p1 = st.text_input("Password", type="password")
        p2 = st.text_input("Confirm Password", type="password")

        if st.button("Sign Up"):
            if p1 != p2:
                st.error("Passwords mismatch")
            else:
                exists = supabase.table("users").select("username").eq("username", u).execute()
                if exists.data:
                    st.error("Username already exists")
                else:
                    supabase.table("users").insert({
                        "username": u,
                        "password": hash_password(p1),
                        "plan": "Free",
                        "usage_count": 0
                    }).execute()
                    st.success("Account created. Please login.")
                    st.session_state.auth_mode = "Login"
                    safe_rerun()

        if st.button("Back"):
            st.session_state.auth_mode = "Login"
            safe_rerun()

    elif st.session_state.auth_mode == "Forgot":
        st.info("Contact admin for manual reset")
        if st.button("Back"):
            st.session_state.auth_mode = "Login"
            safe_rerun()

    st.stop()

# ==============================
# MAIN APP
# ==============================
require_login()

user_row = supabase.table("users").select("*")\
    .eq("username", st.session_state.user).execute().data[0]

# ------------------------------
# SIDEBAR
# ------------------------------
with st.sidebar:
    st.markdown(f"### 👋 {st.session_state.user}")
    st.caption(f"Plan: {user_row['plan']}")
    st.caption(f"Usage: {user_row['usage_count']}")

    for label, page in [
        ("🎙 Studio", "Studio"),
        ("💳 Billing", "Billing"),
        ("🛠 Admin", "Admin")
    ]:
        if st.button(label, use_container_width=True):
            st.session_state.page = page
            safe_rerun()

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        safe_rerun()

# ==============================
# STUDIO PAGE
# ==============================
if st.session_state.page == "Studio":
    st.header("🎙 Advanced Voice Lab")

    st.subheader("Select Voice")
    cols = st.columns(len(VOICE_MODELS))
    for i, (name, v) in enumerate(VOICE_MODELS.items()):
        with cols[i]:
            if st.button(name, use_container_width=True):
                st.session_state.voice_id = v["id"]

    text = st.text_area("Script", height=180)
    speed = st.slider("Speed", 0.5, 2.0, 1.0)
    pitch = st.slider("Pitch", -20, 20, 0)

    if st.button("⚡ Generate Audio", type="primary"):
        if not text.strip():
            st.warning("Enter script text")
        else:
            with st.spinner("Generating audio..."):
                audio = generate_voice_sync(
                    text,
                    st.session_state.voice_id,
                    f"{int((speed-1)*100)}%",
                    f"{pitch}Hz"
                )

                st.audio(audio)
                st.download_button("Download MP3", audio, "voice.mp3")

                supabase.table("users").update({
                    "usage_count": user_row["usage_count"] + 1
                }).eq("username", st.session_state.user).execute()

                safe_rerun()

# ==============================
# BILLING
# ==============================
elif st.session_state.page == "Billing":
    st.header("💳 Upgrade Plan")
    st.image(
        f"https://api.qrserver.com/v1/create-qr-code/?data=upi://pay?pa={UPI_ID}",
        width=250
    )

# ==============================
# ADMIN
# ==============================
elif st.session_state.page == "Admin":
    st.header("🛡 Admin Panel")
    key = st.text_input("Master Key", type="password")
    if key == ADMIN_PASSWORD:
        users = supabase.table("users").select("*").execute()
        st.dataframe(pd.DataFrame(users.data), use_container_width=True)
