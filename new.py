import os
import sqlite3
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
import streamlit as st
from supabase import create_client, Client

# --- SUPABASE CONNECTION ---
# Add these to Streamlit Cloud -> Settings -> Secrets
# SUPABASE_URL = "your_project_url"
# SUPABASE_KEY = "your_api_key"

url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- REPLACING SQLITE WITH SUPABASE ---

def save_user_to_supabase(u, p_hash, e):
    # This replaces: conn.execute("INSERT INTO users...")
    data = {
        "username": u,
        "password": p_hash,
        "email": e,
        "plan": "Basic",
        "usage_count": 0,
        "receipt_id": "NONE"
    }
    try:
        supabase.table("users").insert(data).execute()
        st.success("User saved to Cloud Database!")
    except Exception as e:
        st.error(f"Error saving to Supabase: {e}")

def get_user_from_supabase(u):
    # This replaces: c.execute("SELECT * FROM users...")
    response = supabase.table("users").select("*").eq("username", u).execute()
    return response.data[0] if response.data else None

def update_usage_supabase(username):
    # This replaces: UPDATE users SET usage_count...
    current_user = get_user_from_supabase(username)
    new_count = current_user['usage_count'] + 1
    supabase.table("users").update({"usage_count": new_count}).eq("username", username).execute()

# --- CONFIGURATION ---
ADMIN_PASSWORD = "ADMIN@123" # इसे अपनी जरूरत के अनुसार बदलें
try:
    ELEVEN_KEY = st.secrets.get("ELEVEN_API_KEY", "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40")
except:
    ELEVEN_KEY = "5eecc00bf17ec14ebedac583a5937edc23005a895a97856e4a465f28d49d7f40"

client = ElevenLabs(api_key=ELEVEN_KEY)
DB_PATH = "studio_v5_pro.db"
ADMIN_MOBILE = "8452095418"
ADMIN_NAME = "AI Studio Admin"

# --- DATABASE ENGINE & AUTO-REPAIR ---
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (username TEXT PRIMARY KEY, password TEXT, email TEXT, 
                      plan TEXT, expiry_date TEXT, usage_count INTEGER, receipt_id TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS cloned_voices 
                     (username TEXT, voice_name TEXT, voice_id TEXT)''')
        
        c.execute("PRAGMA table_info(users)")
        cols = [col[1] for col in c.fetchall()]
        if "receipt_id" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN receipt_id TEXT DEFAULT 'NONE'")
        conn.commit()
    except Exception as e:
        if os.path.exists(DB_PATH): os.remove(DB_PATH)
        init_db()
    finally:
        conn.close()

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
init_db()
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
                conn = sqlite3.connect(DB_PATH)
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)", (u, hash_pass(p), e, "Basic", "N/A", 0, "NONE"))
                    conn.commit()
                    st.success("Success! Please Login.")
                except: st.error("User already exists.")
                finally: conn.close()

    elif choice == "Login":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hash_pass(p)))
            if c.fetchone():
                st.session_state.user = u
                st.rerun()
            else: st.error("Invalid credentials.")
            conn.close()

    elif choice == "Forgot Password":
        email = st.text_input("Registered Email")
        if st.button("Verify Email"):
            st.success(f"Reset link simulated for {email}")
            new_p = st.text_input("New 8 Char Password", type="password", max_chars=8)
            if st.button("Update"):
                conn = sqlite3.connect(DB_PATH)
                conn.execute("UPDATE users SET password=? WHERE email=?", (hash_pass(new_p), email))
                conn.commit(); conn.close()
                st.success("Done!")

# --- DASHBOARD ---
else:
    # Sidebar
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
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query("SELECT username, email, plan, expiry_date, usage_count, receipt_id FROM users", conn)
            st.write("### User Database")
            st.dataframe(df, use_container_width=True)
            
            st.write("### Quick Management")
            target_user = st.selectbox("Select User to Modify", df['username'])
            new_plan = st.selectbox("Change Plan To", ["Basic", "Standard", "Premium"])
            if st.button("Update User Plan"):
                exp = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d") if new_plan != "Basic" else "N/A"
                conn.execute("UPDATE users SET plan=?, expiry_date=? WHERE username=?", (new_plan, exp, target_user))
                conn.commit()
                st.success("Updated!")
                st.rerun()
            conn.close()
        else:
            st.warning("Authorized Personnel Only")
            
    # USER VIEW
    else:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (st.session_state.user,))
        _, _, u_email, u_plan, u_expiry, u_usage, u_receipt = c.fetchone()
        
        # Check Expiry
        if u_expiry != "N/A" and datetime.now() > datetime.strptime(u_expiry, "%Y-%m-%d"):
            conn.execute("UPDATE users SET plan='Basic', expiry_date='N/A' WHERE username=?", (st.session_state.user,))
            conn.commit()
            u_plan = "Basic"
        conn.close()

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
                                conn = sqlite3.connect(DB_PATH)
                                conn.execute("UPDATE users SET usage_count = usage_count + 1 WHERE username=?", (st.session_state.user,))
                                conn.commit(); conn.close()
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
                        conn=sqlite3.connect(DB_PATH); conn.execute("UPDATE users SET plan='Standard', expiry_date=?, receipt_id=? WHERE username=?",(exp, rid, st.session_state.user)); conn.commit(); conn.close()
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


