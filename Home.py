เข้าใจแล้วครับ! คือคุณต้องการเก็บรูปกราฟเอาไว้ แต่ย้ายตำแหน่งให้มันไปอยู่ข้างล่างถัดจากชื่อ (ไม่ให้มีรูปอะไรมาบังก่อนถึงชื่อ TRADING HOME) และกำจัดไอคอนจิ๋วที่เคยอยู่หน้าชื่อออกไป

ผมปรับโค้ดให้ใหม่ โดยเน้นให้ชื่อ TRADING HOME ขึ้นมาเป็นอันดับแรกสุดของหน้าจอ และมีขนาดที่พอดีกับมือถือครับ

📋 โค้ดฉบับแก้ไข: ชื่อขึ้นก่อน ตามด้วยรูปกราฟ
Python
import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ: ล้างค่า page_icon เพื่อป้องกันไอคอนรูปแตก
st.set_page_config(layout="wide", page_title=" ", page_icon=" ") 

st.markdown("""
    <style>
    /* ซ่อน Header และไอคอนจิ๋วที่มุมซ้ายแบบเด็ดขาด */
    [data-testid="stHeader"], header, .stAppHeader {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    
    /* ดันเนื้อหาขึ้นไปให้สุดหน้าจอ เพื่อให้ชื่ออยู่บนสุดจริงๆ */
    .main .block-container {
        padding-top: 0rem !important;
        margin-top: -60px !important; 
    }

    .main { background-color: #0f172a; }
    
    /* ปรับแต่งชื่อ TRADING HOME ให้พอดีหน้าจอมือถือ */
    .responsive-title {
        color: #fbbf24 !important;
        font-weight: bold !important;
        text-align: center;
        font-size: clamp(24px, 8vw, 48px); 
        margin-top: 10px;
        margin-bottom: 15px;
        line-height: 1.2;
    }

    /* สไตล์ Metrics */
    [data-testid="stMetricValue"] { color: #f8fafc !important; font-size: 24px !important; }
    [data-testid="stMetricLabel"] { color: #fbbf24 !important; font-size: 14px !important; }
    [data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #475569;
        text-align: center;
    }
    
    .stButton>button {
        width: 100%; border-radius: 10px; height: 4em;
        background-color: #1e293b; color: #f8fafc;
        border: 1px solid #475569; font-size: 16px;
    }
    .stButton>button:hover { border: 1px solid #fbbf24; color: #fbbf24; }
    </style>
    """, unsafe_allow_html=True)

# 2. อันดับ 1: แสดงชื่อ TRADING HOME ก่อนเลย
st.markdown('<p class="responsive-title">TRADING HOME</p>', unsafe_allow_html=True)

# 3. อันดับ 2: แสดงรูปกราฟตามลงมา (ใช้ลิงก์ที่เสถียรเพื่อไม่ให้แตก)
st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80", use_container_width=True)

# 4. แสดงวันที่และเวลา
tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
st.write(f"<p style='text-align: center; color: #94a3b8; margin-top: 10px;'>📅 {now.strftime('%A, %d %B %Y')} | 🕒 {now.strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
st.write("---")

# 5. Market Status
st.subheader("🌐 Market Status")
m1, m2, m3 = st.columns(3)

def get_status(market):
    now_th = datetime.now(tz_th)
    if now_th.weekday() >= 5: return "CLOSED 🔴"
    h = now_th.hour
    if market == 'SET':
        t = h * 100 + now_th.minute
        return "OPENING 🟢" if (1000 <= t <= 1230) or (1430 <= t <= 1630) else "CLOSED 🔴"
    else: # US
        return "OPENING 🟢" if (h >= 20) or (h <= 4) else "CLOSED 🔴"

with m1: st.metric("SET (Thailand)", get_status('SET'))
with m2: st.metric("US Market", get_status('US'))
with m3: 
    st.markdown("""
        <div style='background-color: #1e293b; padding: 22px; border-radius: 12px; border: 1px solid #fbbf24; text-align: center; color: #fbbf24; font-size: 18px; font-weight: bold;'>
            FOCUS TICKERS
        </div>
        """, unsafe_allow_html=True)

st.write("##")

# 6. Quick Navigation (ปุ่มทางลัดกลับไปใช้ชื่อไฟล์เดิม)
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
