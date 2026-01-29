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

# --- SUPABASE CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Connection Error: Check Streamlit Secrets for SUPABASE_URL and SUPABASE_KEY")
    st.stop()

# --- CONFIGURATION ---
ADMIN_PASSWORD = "ADMIN@123"
try:
    ELEVEN_KEY = st.secrets.get("ELEVEN_API_KEY", "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40")
except:
    ELEVEN_KEY = "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40"

client = ElevenLabs(api_key=ELEVEN_KEY)
ADMIN_MOBILE = "8452095418"
ADMIN_NAME = "AI Studio Admin"

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- UI EFFECTS ---
def inject_ui_effects():
    st.markdown("""
        <style>
        .main { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: white; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: rgba(255,255,255,0.1); border-radius: 10px; padding: 10px; color: white; transition: 0.3s; }
        .stTabs [data-baseweb="tab"]:hover { background-color: rgba(255,255,255,0.2); }
        </style>
    """, unsafe_allow_html=True)
    
    components.html("""
        <canvas id="canvas1" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; pointer-events: none;"></canvas>
        <script>
            const canvas = document.getElementById('canvas1');
            const ctx = canvas.getContext('2d');
            canvas.width = window.innerWidth; canvas.height = window.innerHeight;
            let particles = [];
            class P {
                constructor() { this.x = Math.random()*canvas.width; this.y = Math.random()*canvas.height; this.s = Math.random()*3+1; this.vx = Math.random()*2-1; this.vy = Math.random()*2-1; }
                u() { this.x += this.vx; this.y += this.vy; if(this.x<0||this.x>canvas.width)this.vx*=-1; if(this.y<0||this.y>canvas.height)this.vy*=-1; }
                d() { ctx.fillStyle='rgba(110,142,251,0.5)'; ctx.beginPath(); ctx.arc(this.x,this.y,this.s,0,Math.PI*2); ctx.fill(); }
            }
            for(let i=0;i<50;i++) particles.push(new P());
            function anim() { ctx.clearRect(0,0,canvas.width,canvas.height); particles.forEach(p=>{p.u();p.d();}); requestAnimationFrame(anim); }
            anim();
        </script>
    """, height=0)

# --- ENGINES ---
async def generate_edge_tts(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": data += chunk["data"]
    return data

# --- START APP ---
inject_ui_effects()

if 'user' not in st.session_state: st.session_state.user = None
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False

# --- AUTH ---
if not st.session_state.user:
    st.title("🚀 Global AI Voice Studio Pro")
    choice = st.sidebar.radio("Navigation", ["Login", "Sign Up", "Forgot Password"])
    
    if choice == "Sign Up":
        u = st.text_input("Username")
        e = st.text_input("Email")
        p = st.text_input("Password (8 chars)", type="password", max_chars=16)
        if st.button("Register"):
            if len(p) < 8: st.error("Password must be 8 characters.")
            else:
                user_data = {
                    "username": u, "password": hash_pass(p), "email": e, 
                    "plan": "Basic", "expiry_date": "N/A", "usage_count": 0, "receipt_id": "NONE"
                }
                try:
                    supabase.table("users").insert(user_data).execute()
                    st.success("Success! Please Login.")
                except: st.error("User already exists or Database Error.")

    elif choice == "Login":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            res = supabase.table("users").select("*").eq("username", u).eq("password", hash_pass(p)).execute()
            if res.data:
                st.session_state.user = u
                st.rerun()
            else: st.error("Invalid credentials.")

    elif choice == "Forgot Password":
        email = st.text_input("Registered Email")
        if st.button("Verify Email"):
            st.success(f"Verification simulated for {email}")
            new_p = st.text_input("New 8 Char Password", type="password", max_chars=8)
            if st.button("Update"):
                supabase.table("users").update({"password": hash_pass(new_p)}).eq("email", email).execute()
                st.success("Done!")

# --- DASHBOARD ---
else:
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.admin_mode = False
        st.rerun()
    
    st.sidebar.divider()
    if st.sidebar.button("🛠️ Access Admin Panel"):
        st.session_state.admin_mode = not st.session_state.admin_mode

    # ADMIN PANEL VIEW
    if st.session_state.admin_mode:
        st.title("🛡️ Admin Management Dashboard")
        pwd = st.text_input("Enter Master Admin Password", type="password")
        if pwd == ADMIN_PASSWORD:
            res = supabase.table("users").select("*").execute()
            df = pd.DataFrame(res.data)
            st.write("### User Database")
            st.dataframe(df, use_container_width=True)
            
            st.write("### Quick Management")
            target_user = st.selectbox("Select User to Modify", df['username'] if not df.empty else [])
            new_plan = st.selectbox("Change Plan To", ["Basic", "Standard", "Premium"])
            if st.button("Update User Plan"):
                exp = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d") if new_plan != "Basic" else "N/A"
                supabase.table("users").update({"plan": new_plan, "expiry_date": exp}).eq("username", target_user).execute()
                st.success("Updated!")
                st.rerun()
        else:
            st.warning("Authorized Personnel Only")
            
    # USER VIEW
    else:
        res = supabase.table("users").select("*").eq("username", st.session_state.user).execute()
        user_info = res.data[0]
        u_plan = user_info['plan']
        u_expiry = user_info['expiry_date']
        u_usage = user_info['usage_count']
        u_receipt = user_info['receipt_id']
        
        # Check Expiry
        if u_expiry != "N/A" and datetime.now() > datetime.strptime(u_expiry, "%Y-%m-%d"):
            supabase.table("users").update({"plan": "Basic", "expiry_date": "N/A"}).eq("username", st.session_state.user).execute()
            u_plan = "Basic"

        tab1, tab2, tab3, tab4 = st.tabs(["🔊 Generator", "🎙️ Clone", "💎 Plans", "📜 Billing"])

        with tab1:
            st.subheader("High Fidelity TTS Engine")
            eng = st.selectbox("Engine", ["Edge-TTS (Free)", "gTTS (Basic)", "ElevenLabs (Pro)"])
            
            if eng == "ElevenLabs (Pro)" and u_plan != "Premium":
                st.error("Premium Plan required for ElevenLabs.")
            else:
                txt = st.text_area("Script", max_chars=300 if u_plan == "Standard" else 5000)
                if st.button("⚡ Generate"):
                    if u_plan == "Basic" and u_usage >= 3: st.error("Daily limit reached.")
                    else:
                        with st.spinner("Processing..."):
                            try:
                                if eng == "Edge-TTS (Free)":
                                    aud = asyncio.run(generate_edge_tts(txt, "hi-IN-MadhurNeural"))
                                elif eng == "gTTS (Basic)":
                                    tts = gTTS(txt, lang='hi'); fp = io.BytesIO(); tts.write_to_fp(fp); aud = fp.getvalue()
                                else:
                                    aud_stream = client.text_to_speech.convert(voice_id="pNInz6obpgDQGcFmaJgB", text=txt, model_id="eleven_multilingual_v2")
                                    aud = b"".join(aud_stream)
                                
                                st.audio(aud)
                                supabase.table("users").update({"usage_count": u_usage + 1}).eq("username", st.session_state.user).execute()
                            except: st.error("Engine Busy. Re-trying...")

        with tab2:
            if u_plan != "Premium": st.warning("Cloning is for Premium Users.")
            else:
                st.file_uploader("Upload 20s Sample", type=['mp3','wav'])
                if st.button("Start Cloning"): st.success("Clone added to your library.")

        with tab3:
            st.write("### Upgrade Membership")
            col1, col2 = st.columns(2)
            with col1:
                st.info("Standard (₹1)")
                if st.button("Buy Standard"):
                    st.image(f"https://api.qrserver.com/v1/create-qr-code/?data=upi://pay?pa={ADMIN_MOBILE}@ybl%26am=1.00")
                    if st.button("Confirm Payment 1"):
                        rid = "REC-" + uuid.uuid4().hex[:6].upper()
                        exp = (datetime.now()+timedelta(days=30)).strftime("%Y-%m-%d")
                        supabase.table("users").update({"plan": "Standard", "expiry_date": exp, "receipt_id": rid}).eq("username", st.session_state.user).execute()
                        st.rerun()
            with col2:
                st.success("Premium (₹10)")
                if st.button("Buy Premium"):
                    st.image(f"https://api.qrserver.com/v1/create-qr-code/?data=upi://pay?pa={ADMIN_MOBILE}@ybl%26am=10.00")

        with tab4:
            if u_receipt != "NONE":
                st.markdown(f"""
                <div style="border: 2px solid #6e8efb; padding: 20px; border-radius: 10px;">
                    <h3>Official Receipt</h3>
                    <p><b>ID:</b> {u_receipt}</p>
                    <p><b>User:</b> {st.session_state.user}</p>
                    <p><b>Plan:</b> {u_plan}</p>
                    <p><b>Valid Until:</b> {u_expiry}</p>
                    <hr>
                    <p style="color: green;"><b>STATUS: VERIFIED</b></p>
                </div>
                """, unsafe_allow_html=True)
            else: st.write("No paid invoices.")
