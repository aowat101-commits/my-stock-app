import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ: ล้างค่า page_icon เพื่อความคลีน 100%
st.set_page_config(layout="wide", page_title=" ", page_icon=" ") 

st.markdown("""
    <style>
    /* นำ Font สวยๆ มาใช้สำหรับบรรทัดที่ 3 */
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
        margin-top: -70px !important; 
    }

    .main { background-color: #0f172a; }
    
    /* บรรทัดที่ 1: WELCOME (ใหญ่และกว้าง) */
    .line-1 {
        color: #94a3b8 !important;
        text-align: center;
        font-size: clamp(28px, 8vw, 42px);
        margin-top: 35px;
        margin-bottom: -25px;
        letter-spacing: 6px;
        text-transform: uppercase;
        font-weight: 300;
    }

    /* บรรทัดที่ 2: TRADING HOME (ใหญ่ที่สุดระดับ Maximum) */
    .line-2 {
        color: #fbbf24 !important;
        font-weight: 900 !important;
        text-align: center;
        font-size: clamp(52px, 15vw, 95px); 
        margin-bottom: -20px;
        line-height: 1.0;
        text-shadow: 5px 5px 12px rgba(0,0,0,0.6);
        letter-spacing: -2px;
    }

    /* บรรทัดที่ 3: FOR MILK (ใหญ่และเท่) */
    .line-3 {
        font-family: 'Dancing Script', cursive;
        color: #f8fafc !important;
        text-align: center;
        font-size: clamp(45px, 12vw, 75px);
        margin-top: 15px;
        margin-bottom: 30px;
        text-shadow: 4px 4px 10px rgba(251, 191, 36, 0.6);
    }

    /* ขยายขนาดหัวข้อ Subheader */
    h2, h3 { 
        font-size: clamp(30px, 7vw, 42px) !important; 
        color: #fbbf24 !important;
        font-weight: 800 !important;
    }

    /* สไตล์ Metrics (ตัวเลขใหญ่พิเศษ) */
    [data-testid="stMetricValue"] { 
        color: #f8fafc !important; 
        font-size: 42px !important; 
        font-weight: 900 !important; 
    }
    [data-testid="stMetricLabel"] { 
        color: #fbbf24 !important; 
        font-size: 22px !important; 
    }
    [data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 40px;
        border-radius: 20px;
        border: 2px solid #334155;
        text-align: center;
    }
    
    /* ปรับขนาดปุ่มกดให้ใหญ่และหนาที่สุด */
    .stButton>button {
        width: 100%; 
        border-radius: 18px; 
        height: 4.8em;
        background-color: #1e293b; 
        color: #f8fafc;
        border: 2px solid #475569; 
        font-size: 28px !important;
        font-weight: 900 !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    }
    .stButton>button:hover { 
        border: 3px solid #fbbf24; 
        color: #fbbf24;
        transform: scale(1.03);
        transition: 0.3s;
    }

    /* ปรับขนาดวันที่ */
    .date-text {
        text-align: center; 
        color: #94a3b8; 
        font-size: clamp(20px, 5vw, 26px);
        margin-top: 25px;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. ส่วนหัวทั้ง 3 บรรทัด (ปรับใหม่ให้ใหญ่กว่าเดิม)
st.markdown('<p class="line-1">Welcome</p>', unsafe_allow_html=True)
st.markdown('<p class="line-2">TRADING HOME</p>', unsafe_allow_html=True)
st.markdown('<p class="line-3">For Milk</p>', unsafe_allow_html=True)

# 3. ส่วนรูปกราฟ (รักษาความสมดุล)
col1, col2, col3 = st.columns([1, 1.8, 1]) 
with col2:
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=600&q=80", use_container_width=True)

# 4. แสดงวันที่และเวลา
tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
st.markdown(f'<p class="date-text">📅 {now.strftime("%A, %d %B %Y")} | 🕒 {now.strftime("%H:%M:%S")}</p>', unsafe_allow_html=True)
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
        <div style='background-color: #1e293b; padding: 32px; border-radius: 20px; border: 2px solid #fbbf24; text-align: center; color: #fbbf24; font-size: 26px; font-weight: 900;'>
            FOCUS TICKERS
        </div>
        """, unsafe_allow_html=True)

st.write("##")

# 6. Quick Navigation (ปุ่มใหญ่พิเศษที่สุด)
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
st.caption("Por Piang Electric Plus Co., Ltd. | Trading Systems")
