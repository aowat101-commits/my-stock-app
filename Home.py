import streamlit as st
from datetime import datetime
import pytz

# 1. บังคับตั้งค่าหน้าจอใหม่
st.set_page_config(layout="wide", page_title="TRADING HOME", page_icon="📈") 

# 2. CSS ชุดใหม่ (เน้นความหนาและระยะห่างที่ถูกต้อง)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@800&family=Kanit:wght@900&family=Dancing+Script:wght@700&display=swap');

    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    .main .block-container { padding-top: 2rem !important; }
    .main { background-color: #0f172a; }
    
    .line-1 {
        font-family: 'Montserrat', sans-serif;
        color: #ffffff !important; 
        text-align: center;
        font-size: clamp(30px, 8vw, 45px);
        letter-spacing: 10px;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .line-2 {
        font-family: 'Kanit', sans-serif !important; 
        color: #fbbf24 !important;
        text-align: center;
        font-size: clamp(50px, 15vw, 100px); 
        margin-bottom: 10px;
        letter-spacing: 2px;
        font-weight: 900;
        text-shadow: 4px 4px 10px rgba(0,0,0,0.5);
    }
    .line-3 {
        font-family: 'Dancing Script', cursive;
        color: #f8fafc !important;
        text-align: center;
        font-size: clamp(45px, 12vw, 80px);
        margin-bottom: 40px;
    }
    
    /* ปรับปุ่มให้กลับมาเป็น 2 คอลัมน์สวยๆ เหมือนเดิม */
    .stButton>button {
        width: 100%; border-radius: 15px; height: 4em;
        background-color: #1e293b; color: #f8fafc;
        border: 2px solid #475569; font-size: 22px !important;
        font-weight: 900 !important;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# แสดงหัวข้อ
st.markdown('<p class="line-1">Welcome</p>', unsafe_allow_html=True)
st.markdown('<p class="line-2">TRADING HOME</p>', unsafe_allow_html=True)
st.markdown('<p class="line-3">For Milk</p>', unsafe_allow_html=True)

# รูปภาพ
st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80", use_container_width=True)

# วันที่
tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
st.markdown(f'<p style="text-align: center; color: #94a3b8; font-size: 20px;">📅 {now.strftime("%A, %d %B %Y")} | 🕒 {now.strftime("%H:%M:%S")}</p>', unsafe_allow_html=True)

st.write("---")

# ปุ่มกด (ใช้ Columns เพื่อบังคับให้แบ่งฝั่ง ไม่ให้เป็นแถวเดี่ยว)
col1, col2 = st.columns(2)
with col1:
    if st.button("📊 Charts"): st.switch_page("pages/2_Charts.py")
    if st.button("🔍 Scanner"): st.switch_page("pages/1_Scanner.py")
with col2:
    if st.button("📈 US Charts"): st.switch_page("pages/4_US_Charts.py")
    if st.button("🇺🇸 US Scanner"): st.switch_page("pages/3_US_Scanner.py")
