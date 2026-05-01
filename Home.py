import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ: ล้างค่า page_icon เพื่อความคลีน 100%
st.set_page_config(layout="wide", page_title=" ", page_icon=" ") 

st.markdown("""
    <style>
    /* ซ่อน Header และไอคอนจิ๋วที่มุมซ้ายแบบถอนรากถอนโคน */
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
        font-size: clamp(16px, 4vw, 24px);
        margin-top: 20px;
        margin-bottom: -10px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* ปรับแต่งชื่อ TRADING HOME ให้เด่นและพอดีหน้าจอมือถือ */
    .responsive-title {
        color: #fbbf24 !important;
        font-weight: bold !important;
        text-align: center;
        font-size: clamp(24px, 8vw, 42px); 
        margin-bottom: 5px;
        line-height: 1.2;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
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
        width: 100%; border-radius: 10px; height: 3.5em;
        background-color: #1e293b; color: #f8fafc;
        border: 1px solid #475569; font-size: 16px;
    }
    .stButton>button:hover { border: 1px solid #fbbf24; color: #fbbf24; }
    </style>
    """, unsafe_allow_html=True)

# 2. ส่วนหัว: Welcome และ TRADING HOME
st.markdown('<p class="welcome-text">Welcome</p>', unsafe_allow_html=True)
st.markdown('<p class="responsive-title">TRADING HOME</p>', unsafe_allow_html=True)

# 3. ส่วนรูปกราฟขนาดเล็กลง 50% อยู่ตรงกลาง
col1, col2, col3 = st.columns([1, 2, 1]) 
with col2:
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=600&q=80", use_container_width=True)

# 4. แสดงวันที่และเวลา
tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
st.write(f"<p style='text-align: center; color: #94a3b8; margin-top: 5px;'>📅 {now.strftime('%A, %d %B %Y')} | 🕒 {now.strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
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
        <div style='background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #fbbf24; text-align: center; color: #fbbf24; font-size: 16px; font-weight: bold;'>
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
