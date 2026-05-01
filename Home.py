import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและล้างไอคอนเดิม
st.set_page_config(layout="wide", page_title="TRADING HOME", page_icon="📈") 

st.markdown("""
    <style>
    /* ดึงฟอนต์ Righteous มาใช้สำหรับบรรทัดที่ 2 โดยเฉพาะ */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;800&family=Righteous&family=Dancing+Script:wght@700&display=swap');

    /* ซ่อน Header และส่วนเกิน */
    [data-testid="stHeader"], header, .stAppHeader {
        display: none !important;
        visibility: hidden !important;
    }
    
    .main .block-container {
        padding-top: 0rem !important;
        margin-top: -60px !important; 
    }

    .main { background-color: #0f172a; }
    
    /* บรรทัดที่ 1: Welcome */
    .line-1 {
        font-family: 'Montserrat', sans-serif;
        color: #ffffff !important; 
        text-align: center;
        font-size: clamp(30px, 9vw, 48px);
        margin-top: 50px;
        margin-bottom: 10px; 
        letter-spacing: 12px;
        text-transform: uppercase;
        font-weight: 800;
    }

    /* บรรทัดที่ 2: TRADING HOME (บังคับใช้ Righteous) */
    .line-2 {
        font-family: 'Kanit', sans-serif !important; 
        color: #fbbf24 !important;
        text-align: center;
        font-size: clamp(50px, 16vw, 100px); 
        margin-top: 10px !important;
        margin-bottom: 15px !important; 
        line-height: 1.1 !important;
        letter-spacing: 2px !important; /* ลดระยะห่างลงให้อ่านง่ายขึ้น */
        font-weight: 900 !important; /* เพิ่มความหนา */
        text-shadow: 3px 3px 10px rgba(0,0,0,0.5);
    }

    /* บรรทัดที่ 3: For Milk */
    .line-3 {
        font-family: 'Dancing Script', cursive;
        color: #f8fafc !important;
        text-align: center;
        font-size: clamp(52px, 14vw, 90px);
        margin-top: 20px;
        margin-bottom: 60px; /* เว้นระยะเหนือรูปภาพตามวงสีแดง */
        text-shadow: 4px 4px 10px rgba(0,0,0,0.5);
    }

    /* ปุ่มและ Metrics */
    [data-testid="stMetricValue"] { color: #f8fafc !important; font-size: 45px !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] { color: #fbbf24 !important; font-size: 22px !important; }
    [data-testid="stMetric"] { background-color: #1e293b; padding: 40px 20px; border-radius: 25px; border: 2px solid #334155; text-align: center; }
    
    .stButton>button {
        width: 100%; border-radius: 20px; height: 4.8em;
        background-color: #1e293b; color: #f8fafc;
        border: 2px solid #475569; font-size: 30px !important;
        font-weight: 900 !important;
    }
    
    .date-text { text-align: center; color: #94a3b8; font-size: clamp(22px, 5.5vw, 28px); margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# แสดงผลส่วนหัว
st.markdown('<p class="line-1">Welcome</p>', unsafe_allow_html=True)
st.markdown('<p class="line-2">TRADING HOME</p>', unsafe_allow_html=True)
st.markdown('<p class="line-3">For Milk</p>', unsafe_allow_html=True)

# ส่วนรูปภาพ (บีบขนาดให้สวย)
col1, col2, col3 = st.columns([0.1, 5, 0.1]) 
with col2:
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80", use_container_width=True)

# วันที่และเวลา
tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
st.markdown(f'<p class="date-text">📅 {now.strftime("%A, %d %B %Y")} | 🕒 {now.strftime("%H:%M:%S")}</p>', unsafe_allow_html=True)
st.write("---")

# ส่วนที่เหลือ (Market Status & Navigation)
st.subheader("🌐 Market Status")
m1, m2, m3 = st.columns(3)
def get_status(market):
    now_th = datetime.now(tz_th)
    if now_th.weekday() >= 5: return "CLOSED 🔴"
    h = now_th.hour
    if market == 'SET':
        t = h * 100 + now_th.minute
        return "OPENING 🟢" if (1000 <= t <= 1230) or (1430 <= t <= 1630) else "CLOSED 🔴"
    else: return "OPENING 🟢" if (h >= 20) or (h <= 4) else "CLOSED 🔴"

with m1: st.metric("SET (Thailand)", get_status('SET'))
with m2: st.metric("US Market", get_status('US'))
with m3: st.markdown('<div style="background-color: #1e293b; padding: 32px; border-radius: 20px; border: 2px solid #fbbf24; text-align: center; color: #fbbf24; font-size: 26px; font-weight: 900;">FOCUS TICKERS</div>', unsafe_allow_html=True)

st.write("##")
st.subheader("🚀 Quick Navigation")
r1c1, r1c2 = st.columns(2)
r2c1, r2c2 = st.columns(2)
with r1c1:
    if st.button("📊 Charts"): st.switch_page("pages/2_Charts.py")
with r1c2:
    if st.button("📈 US Charts"): st.switch_page("pages/4_US_Charts.py")
with r2c1:
    if st.button("🔍 Scanner"): st.switch_page("pages/1_Scanner.py")
with r2c2:
    if st.button("🇺🇸 US Scanner"): st.switch_page("pages/3_US_Scanner.py")
st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Trading Dashboard")
