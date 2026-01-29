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

# --- PROFESSIONAL PAGE CONFIG ---
st.set_page_config(page_title="Global AI Voice Studio Pro", page_icon="🎙️", layout="wide")

# --- CACHED SUPABASE CONNECTION ---
@st.cache_resource
def get_supabase_client():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("🛑 Database Connection Failed. Please check Secrets.")
        return None

supabase = get_supabase_client()

# --- CONFIGURATION ---
ADMIN_PASSWORD = "ADMIN@123"
ELEVEN_KEY = st.secrets.get("ELEVEN_API_KEY", "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40")
client = ElevenLabs(api_key=ELEVEN_KEY)
ADMIN_MOBILE = "8452095418"  
UPI_ID = f"{ADMIN_MOBILE}@ybl"

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- DYNAMIC 3D UI & NAVIGATION CSS ---
def inject_ui_effects():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
        * {{ font-family: 'Poppins', sans-serif; }}
        .main {{ background: radial-gradient(circle at top right, #1e1e2f, #0f0c29); color: white; }}
        .st-emotion-cache-1r6slb0 {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .stButton>button {{
            background: linear-gradient(45deg, #6e8efb, #a7b7fb);
            border-radius: 12px;
            transition: 0.3s;
        }}
        .help-footer {{
            position: fixed; bottom: 20px; right: 20px;
            background: rgba(110,142,251,0.9); padding: 15px 25px;
            border-radius: 50px; color: white; z-index: 1000;
        }}
        </style>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="help-footer">🆘 Help Center: +91 {ADMIN_MOBILE}</div>', unsafe_allow_html=True)

# --- ENGINES ---
async def generate_edge_tts(text, voice, rate="+0%", pitch="+0Hz"):
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": data += chunk["data"]
        return data
    except: return None

# --- APP START ---
inject_ui_effects()

if 'user' not in st.session_state: st.session_state.user = None
if 'current_page' not in st.session_state: st.session_state.current_page = "Studio"

# --- AUTH LAYER ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🚀 Global AI Studio Pro")
        auth_tab = st.tabs(["Login", "Sign Up"])
        with auth_tab[0]:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Access Studio"):
                res = supabase.table("users").select("*").eq("username", u).eq("password", hash_pass(p)).execute()
                if res.data:
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Access Denied.")
        with auth_tab[1]:
            nu = st.text_input("New Username")
            ne = st.text_input("Email")
            np = st.text_input("New Password", type="password")
            if st.button("Create Account"):
                try:
                    supabase.table("users").insert({"username": nu, "password": hash_pass(np), "email": ne}).execute()
                    st.success("Account Created!")
                except: st.error("User exists.")

else:
    # --- FETCH USER DATA ---
    res = supabase.table("users").select("*").eq("username", st.session_state.user).execute()
    u_info = res.data[0]

    # --- 3D SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user}")
        st.caption(f"Plan: {u_info['plan']}")
        st.divider()
        if st.button("✨ Voice Studio"): st.session_state.current_page = "Studio"
        if st.button("🧬 Voice Cloning"): st.session_state.current_page = "Cloning"
        if st.button("🔑 API Access"): st.session_state.current_page = "API"
        if st.button("💳 Billing"): st.session_state.current_page = "Billing"
        if st.button("🛠️ Admin"): st.session_state.current_page = "Admin"
        st.divider()
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.rerun()

    # --- PAGE: STUDIO (WITH ELEVENLABS SLIDERS) ---
    if st.session_state.current_page == "Studio":
        st.header("🎙️ Advanced AI Voice Lab")
        
        tab_simple, tab_pro = st.tabs(["Standard Mode", "Professional Audio Lab"])
        
        with tab_pro:
            st.subheader("Fine-Tuning Controls (ElevenLabs Style)")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                stability = st.slider("Stability", 0.0, 1.0, 0.5, help="High: Consistent voice. Low: Emotional/Variable.")
                speed = st.slider("Speech Rate", 0.5, 2.0, 1.0)
            with col_s2:
                clarity = st.slider("Clarity + Similarity", 0.0, 1.0, 0.75)
                pitch_val = st.slider("Pitch Control", -20, 20, 0)
            with col_s3:
                exaggeration = st.slider("Style Exaggeration", 0.0, 1.0, 0.0)
                st.info("Pro Tip: Lower stability for story telling, higher for news.")

        c1, c2 = st.columns([2, 1])
        with c1:
            eng = st.selectbox("Engine", ["Edge-TTS Ultra", "ElevenLabs v2", "gTTS Basic"])
            txt = st.text_area("Script", placeholder="Tip: Use 'Name: Text' for future multi-speaker support...", height=200)
            
            if st.button("⚡ Synthesize Master Audio"):
                if u_info['plan'] == "Basic" and u_info['usage_count'] >= 5:
                    st.warning("Limit reached. Upgrade to continue.")
                else:
                    with st.spinner("Generating High-Fidelity Audio..."):
                        if "Edge" in eng:
                            p_str = f"{pitch_val}Hz"
                            r_str = f"{int((speed-1)*100)}%"
                            aud = asyncio.run(generate_edge_tts(txt, "hi-IN-MadhurNeural", rate=r_str, pitch=p_str))
                        elif "ElevenLabs" in eng:
                            if u_info['plan'] != "Premium": st.error("Premium Plan Required"); st.stop()
                            s = client.text_to_speech.convert(
                                voice_id="pNInz6obpgDQGcFmaJgB",
                                text=txt,
                                model_id="eleven_multilingual_v2",
                                voice_settings=VoiceSettings(stability=stability, similarity_boost=clarity, style=exaggeration)
                            )
                            aud = b"".join(s)
                        else:
                            tts = gTTS(txt, lang='hi'); f = io.BytesIO(); tts.write_to_fp(f); aud = f.getvalue()

                        if aud:
                            st.audio(aud)
                            st.download_button("📥 Download MP3", aud, file_name="ai_studio_pro.mp3")
                            supabase.table("users").update({"usage_count": u_info['usage_count'] + 1}).eq("username", st.session_state.user).execute()

    # --- PAGE: API KEY GENERATION ---
    elif st.session_state.current_page == "API":
        st.header("🔑 Developer API Portal")
        if u_info['plan'] == "Basic":
            st.warning("API Access is for Standard/Premium users.")
        else:
            st.write("Integrate our AI Voice into your own apps.")
            if st.button("Generate New API Secret"):
                new_key = f"sk_live_{uuid.uuid4().hex[:16]}"
                st.code(new_key, language="text")
                st.success("Keep this safe! It will not be shown again.")

    # --- PAGE: CLONING ---
    elif st.session_state.current_page == "Cloning":
        st.header("🧬 Neural Voice Cloning")
        if u_info['plan'] != "Premium":
            st.error("Premium Required for Voice Cloning.")
        else:
            st.file_uploader("Upload 20s High-Quality Sample")
            st.button("Train Voice Model")

    # --- PAGE: BILLING ---
    elif st.session_state.current_page == "Billing":
        st.header("💳 Membership Plans")
        p1, p2 = st.columns(2)
        with p1:
            st.info("### Standard (₹1)")
            if st.button("Get Standard"):
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?data=upi://pay?pa={UPI_ID}%26am=1.00")
        with p2:
            st.success("### Premium (₹10)")
            if st.button("Get Premium"):
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?data=upi://pay?pa={UPI_ID}%26am=10.00")

    # --- PAGE: ADMIN ---
    elif st.session_state.current_page == "Admin":
        st.header("🛡️ Master Dashboard")
        apk = st.text_input("Admin Key", type="password")
        if apk == ADMIN_PASSWORD:
            all_u = supabase.table("users").select("*").execute()
            st.dataframe(pd.DataFrame(all_u.data))
