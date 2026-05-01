import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ: ห้ามใส่ชื่อหน้าเว็บในส่วนนี้ชั่วคราวเพื่อเช็คว่าไอคอนมาจากชื่อไหม
st.set_page_config(layout="wide", page_title=" ") 

st.markdown("""
    <style>
    /* 1. ซ่อน Header และส่วนเกินแบบถอนรากถอนโคน */
    header, [data-testid="stHeader"], .stAppHeader {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    
    /* 2. บล็อกรูปภาพหรือไอคอนที่อาจจะหลุดมาที่มุมซ้ายบน */
    img[src*="data:image"], .st-emotion-cache-1avcm0n img {
        display: none !important;
    }

    /* 3. ดันเนื้อหาขึ้นไปทับพื้นที่ Header ทั้งหมด */
    .main .block-container {
        padding-top: 0rem !important;
        margin-top: -60px !important; /* ดันขึ้นไปปิดรอยต่อ */
    }

    .main { background-color: #0f172a; }
    
    /* สไตล์ Metrics */
    [data-testid="stMetricValue"] { color: #f8fafc !important; font-size: 28px !important; }
    [data-testid="stMetricLabel"] { color: #fbbf24 !important; font-size: 16px !important; }
    [data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #334155;
        text-align: center;
    }
    
    .focus-box {
        background-color: #1e293b;
        padding: 40px 20px;
        border-radius: 12px;
        border: 1px solid #fbbf24;
        text-align: center;
        color: #fbbf24;
        font-size: 24px;
        letter-spacing: 2px;
    }

    h1 { color: #fbbf24 !important; font-weight: normal !important; text-align: center; margin-top: 15px; }
    
    .stButton>button {
        width: 100%; border-radius: 10px; height: 4em;
        background-color: #1e293b; color: #f8fafc;
        border: 1px solid #475569; font-size: 16px;
    }
    .stButton>button:hover { border: 1px solid #fbbf24; color: #fbbf24; }
    </style>
    """, unsafe_allow_html=True)

# 2. Banner (ใช้รูปกราฟเท่ๆ บังไว้ด้านบนสุด)
st.image("https://images.unsplash.com/photo-1611974714851-eb605161882c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", use_container_width=True)

# 3. Header ใหม่ (ใช้ Emoji กราฟแท่งเทียนสไตล์โมเดิร์น 📊)
st.markdown("<h1>📊 TRADING HOME</h1>", unsafe_allow_html=True)

tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
st.write(f"<p style='text-align: center; color: #94a3b8;'>📅 {now.strftime('%A, %d %B %Y')} | 🕒 {now.strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
st.write("---")

# 4. Market Status
st.subheader("🌐 Market Status")
m_col1, m_col2, m_col3 = st.columns(3)

def get_set_status(now):
    if now.weekday() >= 5: return "CLOSED 🔴"
    t = now.hour * 100 + now.minute
    return "OPENING 🟢" if (1000 <= t <= 1230) or (1430 <= t <= 1630) else "CLOSED 🔴"

def get_us_status(now):
    if now.weekday() >= 5: return "CLOSED 🔴"
    return "OPENING 🟢" if (now.hour >= 20) or (now.hour <= 4) else "CLOSED 🔴"

with m_col1: st.metric("SET (Thailand)", get_set_status(now))
with m_col2: st.metric("US Market", get_us_status(now))
with m_col3: st.markdown('<div class="focus-box">FOCUS TICKERS</div>', unsafe_allow_html=True)

st.write("##")

# 5. Quick Navigation
st.subheader("🚀 Quick Navigation")
r1c1, r1c2 = st.columns(2)
r2c1, r2c2 = st.columns(2)

with r1c1:
    if st.button("📊 Charts Thai Stocks"): st.switch_page("pages/2_Charts.py")
with r1c2:
    if st.button("📈 Charts US Stocks"): st.switch_page("pages/4_US_Charts.py")
with r2c1:
    if st.button("🔍 Scan Thai Stocks"): st.switch_page("pages/1_Scanner.py")
with r2c2:
    if st.button("🇺🇸 Scan US Stocks"): st.switch_page("pages/3_US_Scanner.py")

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Trading Systems")
