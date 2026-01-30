# =========================================================
# GLOBAL AI STUDIO PRO – ENTERPRISE SINGLE FILE
# Author: Senior SaaS Architecture Pattern
# =========================================================

import os, time, hmac, hashlib, asyncio, secrets, logging
from datetime import datetime
import streamlit as st
import pandas as pd
import edge_tts
from supabase import create_client

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Global AI Studio Pro",
    page_icon="🎙️",
    layout="wide"
)

# =========================================================
# LOGGING (PRODUCTION)
# =========================================================
logging.basicConfig(level=logging.INFO)

# =========================================================
# SECRETS VALIDATION
# =========================================================
REQUIRED_SECRETS = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "ELEVEN_API_KEY",
    "RAZORPAY_KEY_SECRET"
]
missing = [s for s in REQUIRED_SECRETS if s not in st.secrets]
if missing:
    st.error(f"Missing secrets: {', '.join(missing)}")
    st.stop()

# =========================================================
# CONSTANTS
# =========================================================
ADMIN_PASSWORD = "ADMIN@123"
UPI_ID = "8452095418@ybl"

PLAN_LIMITS = {
    "Free": 10,
    "Standard": 100,
    "Premium": 1000
}

VOICE_MODELS = {
    "Madhur (Male)": {
        "id": "hi-IN-MadhurNeural",
        "preview": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    },
    "Swara (Female)": {
        "id": "hi-IN-SwaraNeural",
        "preview": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"
    },
    "Adam (EN)": {
        "id": "en-US-AdamMultilingual",
        "preview": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"
    }
}

# =========================================================
# DATABASE
# =========================================================
@st.cache_resource
def get_db():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = get_db()

# =========================================================
# SECURITY UTILITIES
# =========================================================
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def rate_limit(key, limit=5, window=60):
    now = time.time()
    history = st.session_state.get(key, [])
    history = [t for t in history if now - t < window]
    if len(history) >= limit:
        return False
    history.append(now)
    st.session_state[key] = history
    return True

def check_usage(user):
    if user["usage_count"] >= PLAN_LIMITS.get(user["plan"], 0):
        st.error("Usage limit reached. Please upgrade.")
        st.stop()

# =========================================================
# VOICE ENGINE (SAFE ASYNC)
# =========================================================
async def _tts(text, voice, rate, pitch):
    tts = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    audio = b""
    async for c in tts.stream():
        if c["type"] == "audio":
            audio += c["data"]
    return audio

def generate_audio(text, voice, rate, pitch):
    return asyncio.run(_tts(text, voice, rate, pitch))

# =========================================================
# SESSION INIT
# =========================================================
defaults = {
    "user": None,
    "page": "Studio",
    "theme": "Dark",
    "voice_id": list(VOICE_MODELS.values())[0]["id"],
    "voice_history": []
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# =========================================================
# THEME TOGGLE
# =========================================================
if st.sidebar.toggle("🌗 Dark Mode", value=True):
    st.markdown("<style>body{background:#0f0c29;color:white}</style>", unsafe_allow_html=True)
else:
    st.markdown("<style>body{background:white;color:black}</style>", unsafe_allow_html=True)

# =========================================================
# AUTH
# =========================================================
if not st.session_state.user:
    st.title("🚀 Global AI Studio Pro")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        res = supabase.table("users").select("*")\
            .eq("username", u)\
            .eq("password", hash_password(p)).execute()
        if res.data:
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# =========================================================
# LOAD USER
# =========================================================
user = supabase.table("users").select("*")\
    .eq("username", st.session_state.user).execute().data[0]

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown(f"### 👋 {user['username']}")
    st.caption(f"Plan: {user['plan']}")
    st.caption(f"Usage: {user['usage_count']}")

    if st.button("🎙 Studio"): st.session_state.page = "Studio"
    if st.button("💳 Billing"): st.session_state.page = "Billing"
    if st.button("📊 Admin"): st.session_state.page = "Admin"
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.rerun()

# =========================================================
# STUDIO
# =========================================================
if st.session_state.page == "Studio":
    st.header("🎙 Advanced Voice Lab")

    cols = st.columns(len(VOICE_MODELS))
    for i, (name, v) in enumerate(VOICE_MODELS.items()):
        with cols[i]:
            st.markdown(name)
            st.audio(v["preview"])
            if st.button("Select", key=name):
                st.session_state.voice_id = v["id"]

    text = st.text_area("Script")
    speed = st.slider("Speed", 0.5, 2.0, 1.0)
    pitch = st.slider("Pitch", -20, 20, 0)

    if st.button("⚡ Generate"):
        if not rate_limit("gen"):
            st.error("Too many requests. Slow down.")
            st.stop()

        check_usage(user)

        audio = generate_audio(
            text,
            st.session_state.voice_id,
            f"{int((speed-1)*100)}%",
            f"{pitch}Hz"
        )

        st.audio(audio)
        st.download_button("Download", audio, "voice.mp3")

        st.session_state.voice_history.append({
            "time": datetime.utcnow(),
            "audio": audio
        })

        supabase.table("users").update({
            "usage_count": user["usage_count"] + 1
        }).eq("username", user["username"]).execute()

        st.rerun()

    with st.expander("🎧 Voice History"):
        for v in st.session_state.voice_history[::-1]:
            st.audio(v["audio"])

# =========================================================
# BILLING
# =========================================================
elif st.session_state.page == "Billing":
    st.header("💳 Upgrade Plan")
    st.image(
        f"https://api.qrserver.com/v1/create-qr-code/?data=upi://pay?pa={UPI_ID}",
        width=250
    )
    st.info("After payment, admin will verify & upgrade automatically.")

# =========================================================
# ADMIN
# =========================================================
elif st.session_state.page == "Admin":
    st.header("🛡 Admin Dashboard")
    key = st.text_input("Admin Key", type="password")
    if key == ADMIN_PASSWORD:
        users = supabase.table("users").select("*").execute().data
        df = pd.DataFrame(users)
        st.metric("Total Users", len(df))
        st.metric("Total Usage", df["usage_count"].sum())
        st.bar_chart(df.groupby("plan")["usage_count"].sum())
        st.dataframe(df)
