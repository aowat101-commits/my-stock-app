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
    
    /* บรรทัดที่ 1: Welcome (ขยายให้ใหญ่และห่างขึ้น) */
    .line-1 {
        color: #94a3b8 !important;
        text-align: center;
        font-size: clamp(32px, 10vw, 48px);
        margin-top: 40px;
        margin-bottom: 10px; /* เพิ่มระยะห่างข้างล่าง */
        letter-spacing: 8px;
        text-transform: uppercase;
        font-weight: 300;
    }

    /* บรรทัดที่ 2: TRADING HOME (ใหญ่ที่สุดเท่าที่จะใหญ่ได้ในมือถือ) */
    .line-2 {
        color: #fbbf24 !important;
        font-weight: 900 !important;
        text-align: center;
        /* ปรับ vw เป็น 18เพื่อให้เต็มจอโทรศัพท์ */
        font-size: clamp(58px, 18vw, 110px); 
        margin-top: 15px;
        margin-bottom: 20px; /* เพิ่มระยะห่างระหว่างบรรทัด */
        line-height: 1.2; /* เพิ่มความสูงบรรทัดป้องกันตัวหนังสือซ้อนกัน */
        text-shadow: 6px 6px 15px rgba(0,0,0,0.7);
        letter-spacing: -2px;
    }

    /* บรรทัดที่ 3: For Milk (ขยายให้เด่นและเว้นระยะห่าง) */
    .line-3 {
        font-family: 'Dancing Script', cursive;
        color: #f8fafc !important;
        text-align: center;
        font-size: clamp(52px, 14vw, 85px);
        margin-top: 20px;
        margin-bottom: 40px;
        text-shadow: 5px 5px 12px rgba(251, 191, 36, 0.6);
        line-height: 1.3;
    }

    /* ขยายขนาดหัวข้อ Subheader */
    h2, h3 { 
        font-size: clamp(32px, 8vw, 48px) !important; 
        color: #fbbf24 !important;
        font-weight: 800 !important;
        margin-top: 30px !important;
    }

    /* สไตล์ Metrics (ตัวเลขใหญ่สะใจ) */
    [data-testid="stMetricValue"] { 
        color: #f8fafc !important; 
        font-size: 48px !important; 
        font-weight: 900 !important; 
    }
    [data-testid="stMetricLabel"] { 
        color: #fbbf24 !important; 
        font-size: 24px !important; 
    }
    [data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 45px 20px;
        border-radius: 25px;
        border: 2px solid #334155;
        text-align: center;
    }
    
    /* ปรับขนาดปุ่มกดให้ใหญ่ยักษ์ */
    .stButton>button {
        width: 100%; 
        border-radius: 20px; 
        height: 5em;
        background-color: #1e293b; 
        color: #f8fafc;
        border: 2px solid #475569; 
        font-size: 32px !important; /* ใหญ่ขึ้นมาก */
        font-weight: 900 !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);
    }
    .stButton>button:hover { 
        border: 4px solid #fbbf24; 
        color: #fbbf24;
        transform: translateY(-5px);
        transition: 0.3s;
    }

    /* ปรับขนาดวันที่ */
    .date-text {
        text-align: center; 
        color: #94a3b8; 
        font-size: clamp(22px, 6vw, 28px);
        margin-top: 30px;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. ส่วนหัวทั้ง 3 บรรทัด (เวอร์ชัน BIG & BOLD)
st.markdown('<p class="line-1">Welcome</p>', unsafe_allow_html=True)
st.markdown('<p class="line-2">TRADING HOME</p>', unsafe_allow_html=True)
st.markdown('<p class="line-3">For Milk</p>', unsafe_allow_html=True)

# 3. ส่วนรูปกราฟ
col1, col2, col3 = st.columns([1, 2, 1]) 
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
        <div style='background-color: #1e293b; padding: 35px; border-radius: 25px; border: 2px solid #fbbf24; text-align: center; color: #fbbf24; font-size: 28px; font-weight: 900;'>
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
