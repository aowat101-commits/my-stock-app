import streamlit as st
from datetime import datetime
import pytz

# 1. บังคับตั้งค่าหน้าจอให้กว้างที่สุด (สำคัญมาก)
st.set_page_config(layout="wide", page_title="TRADING HOME", page_icon="📈") 

# 2. CSS ชุดใหญ่: จัดการเรื่องความกว้างและการซ่อน Sidebar
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@800&family=Kanit:wght@900&family=Dancing+Script:wght@700&display=swap');

    /* ซ่อน Header และ Sidebar ทิ้งทั้งหมดเพื่อให้ปุ่มไม่กองอยู่ฝั่งเดียว */
    [data-testid="stHeader"], header, .stAppHeader, [data-testid="stSidebar"], .stSidebar {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* ขยายเนื้อหาให้เต็มหน้าจอ PC และมือถือ */
    .main .block-container { 
        max-width: 950px !important; /* จำกัดความกว้างสูงสุดเพื่อให้ดูสวยบน PC แต่ยังกว้างพอสำหรับมือถือ */
        margin: 0 auto !important;
        padding-top: 2rem !important; 
    }
    
    .main { background-color: #0f172a; }
    
    /* สไตล์ตัวหนังสือหัวข้อ */
    .line-1 { font-family: 'Montserrat', sans-serif; color: #ffffff !important; text-align: center; font-size: clamp(30px, 8vw, 45px); letter-spacing: 10px; text-transform: uppercase; margin-bottom: 5px; }
    .line-2 { font-family: 'Kanit', sans-serif !important; color: #fbbf24 !important; text-align: center; font-size: clamp(55px, 15vw, 110px); margin-bottom: 10px; letter-spacing: 2px; font-weight: 900; text-shadow: 4px 4px 10px rgba(0,0,0,0.5); }
    .line-3 { font-family: 'Dancing Script', cursive; color: #f8fafc !important; text-align: center; font-size: clamp(50px, 12vw, 85px); margin-bottom: 40px; }
    
    /* ปรับปรุงปุ่มให้ใหญ่และสวยงาม */
    .stButton > button {
        width: 100% !important;
        border-radius: 20px !important;
        height: 4.5em !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 2px solid #475569 !important;
        font-size: clamp(20px, 5vw, 28px) !important; /* ปรับขนาดฟอนต์ตามขนาดหน้าจอ */
        font-weight: 900 !important;
        margin-bottom: 15px !important;
        transition: 0.3s;
    }
    .stButton > button:hover { 
        border-color: #fbbf24 !important; 
        color: #fbbf24 !important;
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.4);
    }
    
    /* จัดการระยะห่างของคอลัมน์ */
    [data-testid="stHorizontalBlock"] {
        gap: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ส่วนแสดงผลหลัก ---
st.markdown('<p class="line-1">Welcome</p>', unsafe_allow_html=True)
st.markdown('<p class="line-2">TRADING HOME</p>', unsafe_allow_html=True)
st.markdown('<p class="line-3">For Milk</p>', unsafe_allow_html=True)

# รูปภาพกราฟ
st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80", use_container_width=True)

# วันที่และเวลา
tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
st.markdown(f'<p style="text-align: center; color: #94a3b8; font-size: 22px; font-weight: bold; margin-top: 20px;">📅 {now.strftime("%A, %d %B %Y")} | 🕒 {now.strftime("%H:%M:%S")}</p>', unsafe_allow_html=True)

st.write("---")

# ส่วนปุ่มกดแบ่งเป็น 2 คอลัมน์ (จะดูดีทั้งใน PC และ มือถือ)
st.markdown("<h3 style='text-align: center; color: #fbbf24; font-family: Kanit;'>🚀 Quick Navigation</h3>", unsafe_allow_html=True)
c1, c2 = st.columns(2)

with c1:
    if st.button("📊 Charts"): st.switch_page("pages/2_Charts.py")
    if st.button("🔍 Scanner"): st.switch_page("pages/1_Scanner.py")

with c2:
    if st.button("📈 US Charts"): st.switch_page("pages/4_US_Charts.py")
    if st.button("🇺🇸 US Scanner"): st.switch_page("pages/3_US_Scanner.py")

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Trading Dashboard")
