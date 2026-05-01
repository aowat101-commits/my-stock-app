import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ: ล้างค่า page_icon เพื่อป้องกันรูปแตกค้างในระบบ
st.set_page_config(layout="wide", page_title=" ", page_icon=" ") 

st.markdown("""
    <style>
    /* ซ่อน Header และไอคอนจิ๋วที่มุมซ้ายแบบถอนรากถอนโคน */
    [data-testid="stHeader"], header, .stAppHeader {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    
    /* ดันเนื้อหาขึ้นไปทับพื้นที่ที่เคยเป็นไอคอนรูปแตก */
    .main .block-container {
        padding-top: 0rem !important;
        margin-top: -60px !important; 
    }

    .main { background-color: #0f172a; }
    
    /* สไตล์ Metrics */
    [data-testid="stMetricValue"] { color: #f8fafc !important; font-size: 28px !important; }
    [data-testid="stMetricLabel"] { color: #fbbf24 !important; font-size: 16px !important; }
    [data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #475569;
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
        font-weight: bold;
    }

    h1 { color: #fbbf24 !important; font-weight: bold !important; text-align: center; margin-bottom: 20px; }
    
    .stButton>button {
        width: 100%; border-radius: 10px; height: 4em;
        background-color: #1e293b; color: #f8fafc;
        border: 1px solid #475569; font-size: 16px;
    }
    .stButton>button:hover { border: 1px solid #fbbf24; color: #fbbf24; }
    </style>
    """, unsafe_allow_html=True)

# 2. ส่วนแสดงผลหลัก: เอาชื่อขึ้นก่อน
st.markdown("<h1>📊 TRADING HOME</h1>", unsafe_allow_html=True)

# 3. ตามด้วยรูปกราฟ Banner (ย้ายมาอยู่ใต้ชื่อ)
st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80", use_container_width=True)

# 4. แสดงวันที่และเวลา
tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
st.write(f"<p style='text-align: center; color: #94a3b8; margin-top: 15px;'>📅 {now.strftime('%A, %d %B %Y')} | 🕒 {now.strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
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
with m3: st.markdown('<div class="focus-box">FOCUS TICKERS</div>', unsafe_allow_html=True)

st.write("##")

# 6. Quick Navigation (เชื่อมไปยังไฟล์ชื่อเดิมใน GitHub)
st.subheader("🚀 Quick Navigation")
r1c1, r1c2 = st.columns(2)
r2c1, r2c2 = st.columns(2)

with r1c1:
    if st.button("📊 Charts"): 
        st.switch_page("pages/2_Charts.py")
with r1c2:
    if st.button("📈 US Charts"): 
        st.switch_page("pages/4_US_Charts.py")
with r2c1:
    if st.button("🔍 Scanner"): 
        st.switch_page("pages/1_Scanner.py")
with r2c2:
    if st.button("🇺🇸 US Scanner"): 
        st.switch_page("pages/3_US_Scanner.py")

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Industrial Automation & Trading Solutions")
