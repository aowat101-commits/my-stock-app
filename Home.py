import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ (ใส่ช่องว่างเพื่อล้างค่าเดิมของระบบ)
st.set_page_config(layout="wide", page_title=" ", page_icon=" ") 

st.markdown("""
    <style>
    /* ซ่อน Header และไอคอนจิ๋วที่มุมซ้ายแบบถอนรากถอนโคน */
    [data-testid="stHeader"], header, .stAppHeader {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* ดันเนื้อหาขึ้นไปทับพื้นที่ Header เพื่อปิดรอยโหว่ */
    .main .block-container {
        padding-top: 0rem !important;
        margin-top: -60px !important; 
    }

    .main { background-color: #0f172a; }
    
    /* ส่วนหัวโปรแกรมแบบใหม่ (ใช้ CSS แทนรูปภาพเพื่อป้องกันไอคอนแตก) */
    .banner-box {
        background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
        padding: 60px;
        border-radius: 15px;
        text-align: center;
        border-bottom: 3px solid #fbbf24;
        margin-bottom: 30px;
    }

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

    h1 { color: #fbbf24 !important; font-weight: bold !important; text-align: center; margin: 0; }
    
    .stButton>button {
        width: 100%; border-radius: 10px; height: 4em;
        background-color: #1e293b; color: #f8fafc;
        border: 1px solid #475569; font-size: 16px;
    }
    .stButton>button:hover { border: 1px solid #fbbf24; color: #fbbf24; }
    </style>
    """, unsafe_allow_html=True)

# 2. สร้าง Banner ด้วย Code (ไม่ใช้รูปภาพจากเน็ต เพื่อไม่ให้มีไอคอนแตก)
st.markdown("""
    <div class="banner-box">
        <h1>📊 TRADING HOME</h1>
        <p style='color: #94a3b8; margin-top: 10px;'>Por Piang Electric Plus Co., Ltd.</p>
    </div>
    """, unsafe_allow_html=True)

tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
st.write(f"<p style='text-align: center; color: #94a3b8;'>📅 {now.strftime('%A, %d %B %Y')} | 🕒 {now.strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
st.write("---")

# 3. Market Status
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
        <div style='background-color: #1e293b; padding: 25px; border-radius: 12px; border: 1px solid #fbbf24; text-align: center; color: #fbbf24; font-size: 20px;'>
            SCANNING SIGNALS...
        </div>
        """, unsafe_allow_html=True)

st.write("##")

# 4. Quick Navigation (ปุ่มทางลัดชื่อเดิม)
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
