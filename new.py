import streamlit as st
import asyncio
import hashlib
from datetime import date, timedelta
from supabase import create_client
import edge_tts
from gtts import gTTS
import io

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="AI Voice Studio Pro",
    layout="wide"
)

# -------------------------------------------------
# DATABASE
# -------------------------------------------------
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# -------------------------------------------------
# PLANS
# -------------------------------------------------
PLAN_RULES = {
    "Free": {"edge": 3, "gtts": 0, "eleven": 0, "words": 300},
    "Standard": {"edge": 10, "gtts": 10, "eleven": 0, "words": 1000},
    "Premium": {"edge": -1, "gtts": -1, "eleven": -1, "words": -1}
}

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def reset_daily(user):
    today = str(date.today())
    if user.get("last_reset") != today:
        supabase.table("users").update({
            "edge_count": 0,
            "gtts_count": 0,
            "eleven_count": 0,
            "last_reset": today
        }).eq("username", user["username"]).execute()

def check_limits(user, engine, text):
    rules = PLAN_RULES[user["plan"]]

    if rules[engine] == 0:
        st.error("This engine is not allowed for your plan.")
        st.stop()

    if rules[engine] != -1:
        count_key = f"{engine}_count"
        if user[count_key] >= rules[engine]:
            st.error("Daily limit reached.")
            st.stop()

    if rules["words"] != -1 and len(text.split()) > rules["words"]:
        st.error("Word limit exceeded.")
        st.stop()

async def edge_generate(text, voice):
    tts = edge_tts.Communicate(text, voice)
    audio = b""
    async for c in tts.stream():
        if c["type"] == "audio":
            audio += c["data"]
    return audio

def gtts_generate(text):
    fp = io.BytesIO()
    tts = gTTS(text)
    tts.write_to_fp(fp)
    return fp.getvalue()

# -------------------------------------------------
# SESSION
# -------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Login"

# -------------------------------------------------
# AUTH (LOGIN / REGISTER / FORGOT)
# -------------------------------------------------
if not st.session_state.user:
    st.title("🎙 AI Voice Studio Pro")

    if st.session_state.auth_mode == "Login":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            res = supabase.table("users").select("*") \
                .eq("username", u) \
                .eq("password", hash_pass(p)).execute()

            if res.data:
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Invalid username or password")

        if st.button("New user? Register"):
            st.session_state.auth_mode = "Register"
            st.rerun()

        if st.button("Forgot password"):
            st.session_state.auth_mode = "Forgot"
            st.rerun()

    elif st.session_state.auth_mode == "Register":
        st.subheader("Create Account")
        u = st.text_input("Choose Username")
        p1 = st.text_input("Password", type="password")
        p2 = st.text_input("Confirm Password", type="password")

        if st.button("Create Account"):
            if p1 != p2:
                st.error("Passwords do not match")
            else:
                exists = supabase.table("users").select("username") \
                    .eq("username", u).execute()
                if exists.data:
                    st.error("Username already exists")
                else:
                    supabase.table("users").insert({
                        "username": u,
                        "password": hash_pass(p1),
                        "plan": "Free",
                        "plan_expiry": date.today() + timedelta(days=30),
                        "edge_count": 0,
                        "gtts_count": 0,
                        "eleven_count": 0,
                        "last_reset": str(date.today())
                    }).execute()
                    st.success("Account created. Please login.")
                    st.session_state.auth_mode = "Login"
                    st.rerun()

        if st.button("Back to login"):
            st.session_state.auth_mode = "Login"
            st.rerun()

    elif st.session_state.auth_mode == "Forgot":
        st.subheader("Reset Password")
        u = st.text_input("Username")
        new_p = st.text_input("New Password", type="password")

        if st.button("Reset Password"):
            res = supabase.table("users").select("username") \
                .eq("username", u).execute()
            if res.data:
                supabase.table("users").update({
                    "password": hash_pass(new_p)
                }).eq("username", u).execute()
                st.success("Password updated. Please login.")
                st.session_state.auth_mode = "Login"
                st.rerun()
            else:
                st.error("User not found")

        if st.button("Back to login"):
            st.session_state.auth_mode = "Login"
            st.rerun()

    st.stop()

# -------------------------------------------------
# LOAD USER
# -------------------------------------------------
user = supabase.table("users").select("*") \
    .eq("username", st.session_state.user).execute().data[0]

reset_daily(user)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
with st.sidebar:
    st.subheader(f"👋 {user['username']}")
    st.write("Plan:", user["plan"])
    st.write("Expires:", user["plan_expiry"])
    page = st.radio("Navigate", ["Dashboard", "Studio", "Billing"])
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.auth_mode = "Login"
        st.rerun()

# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
if page == "Dashboard":
    st.header("📊 Dashboard")
    st.metric("Edge Today", user["edge_count"])
    st.metric("gTTS Today", user["gtts_count"])
    st.metric("Eleven Today", user["eleven_count"])

# -------------------------------------------------
# STUDIO
# -------------------------------------------------
elif page == "Studio":
    st.header("🎙 Voice Studio")

    engine = st.selectbox("Engine", ["edge", "gtts", "eleven"])
    voice = st.selectbox("Voice", [
        "hi-IN-MadhurNeural",
        "hi-IN-SwaraNeural"
    ])
    text = st.text_area("Enter your script")

    if st.button("Generate Voice"):
        check_limits(user, engine, text)

        if engine == "edge":
            audio = asyncio.run(edge_generate(text, voice))
            key = "edge_count"
        elif engine == "gtts":
            audio = gtts_generate(text)
            key = "gtts_count"
        else:
            if user["plan"] != "Premium":
                st.error("ElevenLabs is Premium only.")
                st.stop()
            st.error("ElevenLabs integration placeholder.")
            st.stop()

        st.audio(audio)
        st.download_button("Download MP3", audio, "voice.mp3")

        supabase.table("users").update({
            key: user[key] + 1
        }).eq("username", user["username"]).execute()

        st.success("Voice generated successfully.")
        st.rerun()

# -------------------------------------------------
# BILLING
# -------------------------------------------------
elif page == "Billing":
    st.header("💳 Upgrade Plans")

    st.subheader("Standard – ₹49")
    st.write("✔ gTTS access\n✔ Higher limits")

    st.subheader("Premium – ₹99")
    st.write("✔ Unlimited usage\n✔ ElevenLabs\n✔ No restrictions")

    st.info("Payment gateway can be added without changing this file.")
