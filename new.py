# =========================================================
# GLOBAL AI VOICE STUDIO — SINGLE FILE MVP (ENTERPRISE SAFE)
# =========================================================

import streamlit as st
import hashlib, asyncio, io, time
from datetime import date
import edge_tts
from gtts import gTTS
from supabase import create_client

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Global AI Voice Studio",
    page_icon="🎙️",
    layout="wide"
)

# =========================================================
# THEME TOGGLE
# =========================================================
if "theme" not in st.session_state:
    st.session_state.theme = "light"

with st.sidebar:
    if st.toggle("🌗 Dark Mode"):
        st.session_state.theme = "dark"

if st.session_state.theme == "dark":
    st.markdown("""
    <style>
    body { background-color:#0f172a; color:white }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# SECRETS
# =========================================================
for s in ["SUPABASE_URL", "SUPABASE_KEY"]:
    if s not in st.secrets:
        st.error(f"Missing secret: {s}")
        st.stop()

# =========================================================
# DATABASE
# =========================================================
@st.cache_resource
def db():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = db()

# =========================================================
# PLANS & LIMITS
# =========================================================
PLANS = {
    "Free": {"edge": 3, "words": 300},
    "Standard": {"edge": 10, "gtts": 10, "words": 1000},
    "Premium": {"edge": -1, "gtts": -1, "eleven": -1}
}

# =========================================================
# HELPERS
# =========================================================
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def reset_daily(user):
    if user["last_reset"] != str(date.today()):
        supabase.table("users").update({
            "edge_count": 0,
            "gtts_count": 0,
            "eleven_count": 0,
            "last_reset": str(date.today())
        }).eq("username", user["username"]).execute()

def rate_limit():
    now = time.time()
    last = st.session_state.get("last_req", 0)
    if now - last < 2:
        st.error("Too many requests. Slow down.")
        st.stop()
    st.session_state.last_req = now

# =========================================================
# VOICE ENGINES
# =========================================================
async def edge_voice(text, voice):
    tts = edge_tts.Communicate(text, voice)
    audio = b""
    async for c in tts.stream():
        if c["type"] == "audio":
            audio += c["data"]
    return audio

def generate(engine, text, voice):
    if engine == "edge":
        return asyncio.run(edge_voice(text, voice))
    if engine == "gtts":
        buf = io.BytesIO()
        gTTS(text).write_to_fp(buf)
        return buf.getvalue()
    st.error("ElevenLabs enabled in backend phase only")
    st.stop()

# =========================================================
# SESSION
# =========================================================
for k in ["user", "page"]:
    st.session_state.setdefault(k, None)

# =========================================================
# AUTH
# =========================================================
if not st.session_state.user:
    st.title("🎙 Global AI Voice Studio")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        res = supabase.table("users").select("*")\
            .eq("username", u)\
            .eq("password", hash_pw(p)).execute()
        if res.data:
            st.session_state.user = u
            st.session_state.page = "Dashboard"
            st.rerun()
        else:
            st.error("Invalid login")

    st.caption("🔐 Email verification & signup in next phase")
    st.stop()

# =========================================================
# LOAD USER
# =========================================================
user = supabase.table("users").select("*")\
    .eq("username", st.session_state.user).execute().data[0]

reset_daily(user)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown(f"### 👋 {user['username']}")
    st.caption(f"Plan: **{user['plan']}**")

    for p in ["Dashboard", "Studio", "Billing"]:
        if st.button(p):
            st.session_state.page = p

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

# =========================================================
# DASHBOARD
# =========================================================
if st.session_state.page == "Dashboard":
    st.header("📊 Usage Dashboard")

    c1, c2, c3 = st.columns(3)
    c1.metric("Plan", user["plan"])
    c2.metric("Total Requests", user["usage_count"])
    c3.metric("Today", user["last_reset"])

    st.subheader("Engine Usage Today")
    st.bar_chart({
        "Edge": user["edge_count"],
        "gTTS": user["gtts_count"],
        "ElevenLabs": user["eleven_count"]
    })

    st.caption("Admin analytics hooks ready")

# =========================================================
# STUDIO
# =========================================================
elif st.session_state.page == "Studio":
    st.header("🎧 Voice Studio")

    engine = st.selectbox("Engine", ["edge", "gtts", "eleven"])
    voice = st.text_input("Voice", "hi-IN-MadhurNeural")
    text = st.text_area("Text")

    if st.button("Generate"):
        rate_limit()

        plan = PLANS[user["plan"]]
        if engine not in plan and plan.get(engine, 0) != -1:
            st.error("Engine not available on your plan")
            st.stop()

        if plan.get("words", 999999) < len(text.split()):
            st.error("Word limit exceeded")
            st.stop()

        audio = generate(engine, text, voice)

        st.audio(audio)
        st.download_button("Download MP3", audio, "voice.mp3")

        supabase.table("users").update({
            f"{engine}_count": user[f"{engine}_count"] + 1,
            "usage_count": user["usage_count"] + 1
        }).eq("username", user["username"]).execute()

        st.success("Voice generated")

# =========================================================
# BILLING
# =========================================================
elif st.session_state.page == "Billing":
    st.header("💳 Upgrade Plan")

    st.markdown("""
    ### Premium – ₹99/month
    - Unlimited usage
    - All engines
    - No limits
    - API access (coming soon)
    """)

    st.info("Stripe / Razorpay auto-upgrade enabled in backend phase")

# =========================================================
# DEPLOYMENT NOTES
# =========================================================
st.caption("""
Deployment ready:
• Streamlit Cloud
• AWS EC2 + Nginx
• Secrets via environment variables
""")
