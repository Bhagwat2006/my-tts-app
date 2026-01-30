import os
import hashlib
import uuid
import asyncio
import datetime
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components
from elevenlabs.client import ElevenLabs
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
ADMIN_MOBILE = "8452095418"  # Your UPI Number
UPI_ID = f"{ADMIN_MOBILE}@ybl"

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- DYNAMIC 3D UI & NAVIGATION CSS ---
def inject_ui_effects():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
        
        * {{ font-family: 'Poppins', sans-serif; }}
        
        .main {{ 
            background: radial-gradient(circle at top right, #1e1e2f, #0f0c29); 
            color: white; 
        }}

        /* 3D Glassmorphism Cards */
        .st-emotion-cache-1r6slb0 {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .st-emotion-cache-1r6slb0:hover {{
            transform: translateY(-5px) rotateX(2deg);
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }}

        /* Animated Buttons */
        .stButton>button {{
            background: linear-gradient(45deg, #6e8efb, #a7b7fb);
            border: none;
            color: white;
            font-weight: 600;
            border-radius: 12px;
            padding: 10px 24px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .stButton>button:hover {{
            transform: scale(1.05);
            box-shadow: 0 0 20px rgba(110,142,251,0.6);
        }}

        /* Custom Floating Help Button */
        .help-footer {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(110,142,251,0.9);
            padding: 15px 25px;
            border-radius: 50px;
            color: white;
            font-weight: bold;
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
            z-index: 1000;
            cursor: pointer;
            transition: 0.3s;
        }}
        .help-footer:hover {{ transform: scale(1.1); background: #fff; color: #6e8efb; }}
        </style>
    """, unsafe_allow_html=True)
    
    # Help Center Floating Button
    st.markdown(f'<div class="help-footer">🆘 Help Center: +91 {ADMIN_MOBILE}</div>', unsafe_allow_html=True)

# --- ENGINES ---
async def generate_edge_tts(text, voice):
    try:
        communicate = edge_tts.Communicate(text, voice)
        data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": data += chunk["data"]
        return data
    except: return None

# --- APP START ---
inject_ui_effects()

if 'user' not in st.session_state: st.session_state.user = None
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False
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

# --- DASHBOARD LAYER ---
else:
    # 3D SIDEBAR NAVIGATION
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user}")
        st.divider()
        
        # Dynamic Navigation Buttons
        if st.button("✨ Voice Studio"): st.session_state.current_page = "Studio"
        if st.button("🧬 Neural Cloning"): st.session_state.current_page = "Cloning"
        if st.button("💳 Billing & Upgrades"): st.session_state.current_page = "Billing"
        if st.button("🛠️ Admin Panel"): st.session_state.current_page = "Admin"
        
        st.divider()
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.rerun()

    # --- DATABASE FETCH ---
    res = supabase.table("users").select("*").eq("username", st.session_state.user).execute()
    u_info = res.data[0]

    # --- PAGE: STUDIO ---
    if st.session_state.current_page == "Studio":
        st.header("🎙️ AI Voice Generation Studio")
        c1, c2 = st.columns([2, 1])
        with c1:
            eng = st.selectbox("Model", ["Edge-TTS Ultra", "gTTS Basic", "ElevenLabs Pro"])
            txt = st.text_area("Your Script", placeholder="Type here...", height=250)
            if st.button("⚡ Generate Audio"):
                if u_info['plan'] == "Basic" and u_info['usage_count'] >= 5:
                    st.warning("Daily limit reached. Please Upgrade.")
                else:
                    with st.spinner("✨ Synthesizing 3D Audio..."):
                        if "Edge" in eng:
                            aud = asyncio.run(generate_edge_tts(txt, "hi-IN-MadhurNeural"))
                        elif "gTTS" in eng:
                            tts = gTTS(txt, lang='hi'); f = io.BytesIO(); tts.write_to_fp(f); aud = f.getvalue()
                        else:
                            if u_info['plan'] != "Premium": st.error("ElevenLabs is Premium Only."); st.stop()
                            s = client.text_to_speech.convert(voice_id="pNInz6obpgDQGcFmaJgB", text=txt, model_id="eleven_multilingual_v2")
                            aud = b"".join(s)
                        
                        if aud:
                            st.audio(aud)
                            supabase.table("users").update({"usage_count": u_info['usage_count'] + 1}).eq("username", st.session_state.user).execute()
        with c2:
            st.markdown(f"""
            ### Status Board
            - **Plan:** {u_info['plan']}
            - **Usage:** {u_info['usage_count']} Generations
            - **Expiry:** {u_info['expiry_date']}
            """)
            if st.button("🚀 Quick Upgrade"):
                st.session_state.current_page = "Billing"
                st.rerun()

    # --- PAGE: CLONING ---
    elif st.session_state.current_page == "Cloning":
        st.header("🧬 Voice Cloning Lab")
        if u_info['plan'] != "Premium":
            st.error("Locked! Premium Plan required for Neural Cloning.")
            if st.button("Unlock Premium Now"):
                st.session_state.current_page = "Billing"
                st.rerun()
        else:
            st.file_uploader("Upload Sample (20s)")
            st.button("Start Training Model")

    # --- PAGE: BILLING & UPGRADES ---
    elif st.session_state.current_page == "Billing":
        st.header("💳 Membership & Upgrades")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("### Standard (₹1)")
            st.write("Unlimited Basic Generations + No Ads")
            if st.button("Purchase Standard"):
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?data=upi://pay?pa={UPI_ID}%26am=1.00")
                if st.button("Confirm ₹1 Payment"):
                    rid = "STD-" + uuid.uuid4().hex[:6].upper()
                    exp = (datetime.now()+timedelta(days=30)).strftime("%Y-%m-%d")
                    supabase.table("users").update({"plan": "Standard", "expiry_date": exp, "receipt_id": rid}).eq("username", st.session_state.user).execute()
                    st.success("Welcome to Standard!")
                    st.rerun()

        with col2:
            st.success("### Premium (₹10)")
            st.write("ElevenLabs + Voice Cloning + 24/7 Support")
            if st.button("Purchase Premium"):
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?data=upi://pay?pa={UPI_ID}%26am=10.00")
                if st.button("Confirm ₹10 Payment"):
                    rid = "PRM-" + uuid.uuid4().hex[:6].upper()
                    exp = (datetime.now()+timedelta(days=30)).strftime("%Y-%m-%d")
                    supabase.table("users").update({"plan": "Premium", "expiry_date": exp, "receipt_id": rid}).eq("username", st.session_state.user).execute()
                    st.success("Welcome to Premium!")
                    st.rerun()

    # --- PAGE: ADMIN ---
    elif st.session_state.current_page == "Admin":
        st.header("🛡️ Master Control")
        pwd = st.text_input("Admin Key", type="password")
        if pwd == ADMIN_PASSWORD:
            res = supabase.table("users").select("*").execute()
            st.dataframe(pd.DataFrame(res.data))
        else: st.warning("Restricted Area")

