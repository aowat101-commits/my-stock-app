import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ (Wide Mode)
st.set_page_config(layout="wide", page_title="TRADING HOME", page_icon="📈") 

# 2. CSS จัดการหน้าจอให้เป๊ะทั้ง PC และ มือถือ
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@800&family=Kanit:wght@900&family=Dancing+Script:wght@700&display=swap');

    /* ซ่อน Header และ Sidebar */
    [data-testid="stHeader"], header, .stAppHeader, [data-testid="stSidebar"], .stSidebar {
        display: none !important;
    }
    
    /* จัดเนื้อหาให้อยู่ตรงกลางหน้าจอ */
    .main .block-container { 
        max-width: 900px !important; 
        margin: 0 auto !important;
        padding-top: 2rem !important; 
    }
    
    .main { background-color: #0f172a; }
    
    /* ตัวหนังสือ 3 บรรทัดบน */
    .line-1 { font-family: 'Montserrat', sans-serif; color: #ffffff !important; text-align: center; font-size: clamp(32px, 8vw, 48px); letter-spacing: 10px; text-transform: uppercase; margin-bottom: 5px; }
    .line-2 { font-family: 'Kanit', sans-serif !important; color: #fbbf24 !important; text-align: center; font-size: clamp(55px, 15vw, 100px); margin-bottom: 10px; letter-spacing: 2px; font-weight: 900; text-shadow: 4px 4px 12px rgba(0,0,0,0.6); line-height: 1.2; }
    .line-3 { font-family: 'Dancing Script', cursive; color: #f8fafc !important; text-align: center; font-size: clamp(48px, 11vw, 80px); margin-bottom: 45px; }
    
    /* ปุ่มกดต้องใหญ่และแบ่งฝั่งชัดเจน */
    .stButton > button {
        width: 100% !important;
        border-radius: 20px !important;
        height: 4.8em !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 2px solid #475569 !important;
        font-size: 26px !important; 
        font-weight: 900 !important;
        margin-bottom: 10px !important;
        transition: 0.3s;
    }
    .stButton > button:hover { border-color: #fbbf24 !important; color: #fbbf24 !important; }
    
    /* บังคับช่องว่างคอลัมน์ */
    [data-testid="stHorizontalBlock"] { gap: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- แสดงผล ---
st.markdown('<p class="line-1">Welcome</p>', unsafe_allow_html=True)
st.markdown('<p class="line-2">TRADING HOME</p>', unsafe_allow_html=True)
st.markdown('<p class="line-3">For Milk</p>', unsafe_allow_html=True)

# รูปภาพกราฟ
st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80", use_container_width=True)

# วันที่
tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
st.markdown(f'<p style="text-align: center; color: #94a3b8; font-size: 22px; font-weight: bold; margin-bottom: 20px;">📅 {now.strftime("%A, %d %B %Y")} | 🕒 {now.strftime("%H:%M:%S")}</p>', unsafe_allow_html=True)

st.write("---")

# แบ่ง 2 คอลัมน์ให้สมดุล (เหมาะทั้ง PC และ มือถือ)
col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Charts"): st.switch_page("pages/2_Charts.py")
    if st.button("🔍 Scanner"): st.switch_page("pages/1_Scanner.py")

with col2:
    if st.button("📈 US Charts"): st.switch_page("pages/4_US_Charts.py")
    if st.button("🇺🇸 US Scanner"): st.switch_page("pages/3_US_Scanner.py")

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Trading Dashboard")
