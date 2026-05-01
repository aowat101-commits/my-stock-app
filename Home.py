import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ
st.set_page_config(layout="wide", page_title="TRADING HOME", page_icon="📈") 

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@800&family=Kanit:wght@900&family=Dancing+Script:wght@700&display=swap');

    [data-testid="stHeader"], header, .stAppHeader, [data-testid="stSidebar"], .stSidebar {
        display: none !important;
        visibility: hidden !important;
    }
    
    .main .block-container {
        max-width: 900px !important; 
        margin: 0 auto !important;
        padding-top: 1rem !important;
    }

    .main { background-color: #0f172a; }
    
    .line-1 { font-family: 'Montserrat', sans-serif; color: #ffffff !important; text-align: center; font-size: clamp(32px, 9vw, 48px); margin-top: 40px; margin-bottom: 5px; letter-spacing: 10px; text-transform: uppercase; font-weight: 800; }
    .line-2 { font-family: 'Kanit', sans-serif !important; color: #fbbf24 !important; text-align: center; font-size: clamp(55px, 17vw, 115px); margin-top: 10px; margin-bottom: 15px; line-height: 1.1; letter-spacing: 2px; font-weight: 900; text-shadow: 4px 4px 12px rgba(0,0,0,0.6); }
    .line-3 { font-family: 'Dancing Script', cursive; color: #f8fafc !important; text-align: center; font-size: clamp(52px, 14vw, 95px); margin-bottom: 55px; text-shadow: 4px 4px 10px rgba(0,0,0,0.5); }

    .stButton>button {
        width: 100% !important;
        border-radius: 20px !important;
        height: 4.8em !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 2px solid #475569 !important;
        font-size: 28px !important; 
        font-weight: 900 !important;
        margin-bottom: 10px !important;
    }
    .stButton>button:hover { border-color: #fbbf24 !important; color: #fbbf24 !important; }
    
    .date-text { text-align: center; color: #94a3b8; font-size: clamp(20px, 5.5vw, 26px); margin-top: 25px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- หัวข้อหลัก ---
st.markdown('<p class="line-1">Welcome</p>', unsafe_allow_html=True)
st.markdown('<p class="line-2">TRADING HOME</p>', unsafe_allow_html=True)
st.markdown('<p class="line-3">For Milk</p>', unsafe_allow_html=True)

st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80", use_container_width=True)

tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
st.markdown(f'<p class="date-text">📅 {now.strftime("%A, %d %B %Y")} | 🕒 {now.strftime("%H:%M:%S")}</p>', unsafe_allow_html=True)

st.write("---")
st.subheader("🚀 Quick Navigation")

# --- ปรับชื่อไฟล์ให้ตรงกับ GitHub ของคุณเป๊ะๆ ---
c1, c2 = st.columns(2)
with c1:
    if st.button("📊 Charts"):
        st.switch_page("pages/2_Thai_Charts.py") # ตรงตามรูป
    if st.button("🔍 Scanner"):
        st.switch_page("pages/1_Thai_Scan.py")   # ตรงตามรูป
with c2:
    if st.button("📈 US Charts"):
        st.switch_page("pages/4_US_Charts.py")   # ตรงตามรูป
    if st.button("🇺🇸 US Scanner"):
        st.switch_page("pages/3_US_Scan.py")     # ตรงตามรูป

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd.")
