import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ: ล้างค่า page_icon เพื่อความคลีน 100%
st.set_page_config(layout="wide", page_title=" ", page_icon=" ") 

st.markdown("""
    <style>
    /* นำ Font สวยๆ มาใช้สำหรับคำว่า For Milk */
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

    /* ซ่อน Header และไอคอนจิ๋วที่มุมซ้ายแบบเด็ดขาด */
    [data-testid="stHeader"], header, .stAppHeader {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    
    /* ดันเนื้อหาขึ้นไปให้สุดหน้าจอ */
    .main .block-container {
        padding-top: 0rem !important;
        margin-top: -60px !important; 
    }

    .main { background-color: #0f172a; }
    
    /* สไตล์สำหรับคำว่า Welcome */
    .welcome-text {
        color: #94a3b8 !important;
        text-align: center;
        font-size: clamp(18px, 5vw, 28px);
        margin-top: 20px;
        margin-bottom: -15px;
        letter-spacing: 3px;
        text-transform: uppercase;
    }

    /* ปรับแต่งชื่อ TRADING HOME ให้ใหญ่และเด่นชัด */
    .responsive-title {
        color: #fbbf24 !important;
        font-weight: bold !important;
        text-align: center;
        font-size: clamp(32px, 10vw, 56px); 
        margin-bottom: -5px;
        line-height: 1.1;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.4);
    }

    /* สไตล์พิเศษสำหรับ For Milk */
    .for-milk-text {
        font-family: 'Dancing Script', cursive;
        color: #f8fafc !important;
        text-align: center;
        font-size: clamp(28px, 7vw, 40px);
        margin-top: 0px;
        margin-bottom: 15px;
        text-shadow: 2px 2px 4px rgba(251, 191, 36, 0.4);
    }

    /* สไตล์ Metrics */
    [data-testid="stMetricValue"] { color: #f8fafc !important; font-size: 26px !important; }
    [data-testid="stMetricLabel"] { color: #fbbf24 !important; font-size: 16px !important; }
    [data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #475569;
        text-align: center;
    }
    
    .stButton>button {
        width: 100%; border-radius: 10px; height: 3.8em;
        background-color: #1e293b; color: #f8fafc;
        border: 1px solid #475569; font-size: 18px;
        font-weight: bold;
    }
    .stButton>button:hover { border: 1px solid #fbbf24; color: #fbbf24; }
    </style>
    """, unsafe_allow_html=True)

# 2. ส่วนหัว: Welcome -> TRADING HOME -> For Milk
st.markdown('<p class="welcome-text">Welcome</p>', unsafe_allow_html=True)
st.markdown('<p class="responsive-title">TRADING HOME</p>', unsafe_allow_html=True)
st.markdown('<p class="for-milk-text">For Milk</p>', unsafe_allow_html=True)

# 3. ส่วนรูปกราฟขนาดเล็กลง 50% อยู่ตรงกลาง
col1, col2, col3 = st.columns([1, 2, 1]) 
with col2:
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=600&q=80", use_container_width=True)

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
        <div style='background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #fbbf24; text-align: center; color: #fbbf24; font-size: 18px; font-weight: bold;'>
            FOCUS TICKERS
        </div>
        """, unsafe_allow_html=True)

st.write("##")

# 6. Quick Navigation
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
