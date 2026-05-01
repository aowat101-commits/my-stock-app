import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ: ล้างค่า page_icon เพื่อความคลีน 100%
st.set_page_config(layout="wide", page_title=" ", page_icon=" ") 

st.markdown("""
    <style>
    /* นำเข้า Font ชุดใหม่ที่สวยและเท่กว่าเดิม */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;800&family=Righteous&family=Dancing+Script:wght@700&display=swap');

    /* ซ่อน Header และไอคอนจิ๋ว */
    [data-testid="stHeader"], header, .stAppHeader {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    
    /* ดันเนื้อหาขึ้นให้สุดหน้าจอ */
    .main .block-container {
        padding-top: 0rem !important;
        margin-top: -60px !important; 
    }

    .main { background-color: #0f172a; }
    
    /* บรรทัดที่ 1: Welcome (ปรับให้ดู Minimal หรูหรา) */
    .line-1 {
        font-family: 'Montserrat', sans-serif;
        color: #f8fafc !important; 
        text-align: center;
        font-size: clamp(28px, 9vw, 45px);
        margin-top: 50px;
        margin-bottom: 5px; 
        letter-spacing: 12px; /* เว้นระยะให้ดูโปร่งและแพง */
        text-transform: uppercase;
        font-weight: 300;
        opacity: 0.9;
    }

    /* บรรทัดที่ 2: TRADING HOME (ใช้ Font สไตล์ Sci-Fi/Trading ให้ดูเท่) */
    .line-2 {
        font-family: 'Righteous', cursive;
        color: #fbbf24 !important;
        text-align: center;
        font-size: clamp(55px, 16vw, 110px); 
        margin-top: 15px;
        margin-bottom: 20px; 
        line-height: 1.1;
        letter-spacing: 6px; /* เพิ่มระยะห่างตัวอักษรตามที่คุณต้องการ */
        text-shadow: 0px 0px 20px rgba(251, 191, 36, 0.4); /* เพิ่มแสงเรืองรอง */
    }

    /* บรรทัดที่ 3: For Milk (พริ้วไหวแต่ชัดเจน) */
    .line-3 {
        font-family: 'Dancing Script', cursive;
        color: #f8fafc !important;
        text-align: center;
        font-size: clamp(52px, 13vw, 85px);
        margin-top: 15px;
        margin-bottom: 50px; /* เว้นระยะจากรูปภาพตามที่คุณวงไว้ */
        text-shadow: 4px 4px 10px rgba(0,0,0,0.5);
    }

    /* หัวข้อสถานะและทางลัด */
    h2, h3 { 
        font-size: clamp(30px, 7vw, 40px) !important; 
        color: #fbbf24 !important;
        font-weight: 800 !important;
        font-family: 'Montserrat', sans-serif;
    }

    /* สไตล์ Metrics */
    [data-testid="stMetricValue"] { 
        color: #f8fafc !important; 
        font-size: 45px !important; 
        font-weight: 900 !important; 
    }
    [data-testid="stMetricLabel"] { color: #fbbf24 !important; font-size: 22px !important; }
    [data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 40px 20px;
        border-radius: 25px;
        border: 2px solid #334155;
        text-align: center;
    }
    
    /* ปุ่มกด Giant Size */
    .stButton>button {
        width: 100%; 
        border-radius: 20px; 
        height: 4.8em;
        background-color: #1e293b; 
        color: #f8fafc;
        border: 2px solid #475569; 
        font-size: 30px !important;
        font-weight: 900 !important;
        font-family: 'Montserrat', sans-serif;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    .stButton>button:hover { 
        border: 4px solid #fbbf24; 
        color: #fbbf24;
        transform: scale(1.02);
    }

    .date-text {
        text-align: center; 
        color: #94a3b8; 
        font-size: clamp(22px, 5.5vw, 28px);
        margin-top: 30px;
        font-family: 'Montserrat', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. แสดงผลส่วนหัว 3 บรรทัด (ฟอนต์ใหม่ทั้งหมด)
st.markdown('<p class="line-1">Welcome</p>', unsafe_allow_html=True)
st.markdown('<p class="line-2">TRADING HOME</p>', unsafe_allow_html=True)
st.markdown('<p class="line-3">For Milk</p>', unsafe_allow_html=True)

# 3. ส่วนรูปภาพ
col1, col2, col3 = st.columns([0.1, 5, 0.1]) 
with col2:
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80", use_container_width=True)

# 4. วันที่และเวลา
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
