import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ (เน้นตัวหนังสือชัดเจน)
st.set_page_config(page_title="Trading Control Center", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0f172a; }
    
    /* แก้ปัญหาตัวหนังสือจาง: กำหนดสีขาวสว่างและสีทอง Loft ให้ชัดเจน */
    [data-testid="stMetricValue"] {
        color: #f8fafc !important; /* สีตัวเลข/สถานะหลัก */
        font-size: 24px !important;
    }
    [data-testid="stMetricLabel"] {
        color: #fbbf24 !important; /* สีหัวข้อ (สีทอง) */
        font-size: 16px !important;
        font-weight: normal !important;
    }
    
    /* ตกแต่งการ์ดสถานะ */
    [data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #334155;
        text-align: center;
    }
    
    /* ปรับแต่งช่อง Focus Ticker พิเศษ */
    .focus-box {
        background-color: #1e293b;
        padding: 40px 20px;
        border-radius: 12px;
        border: 1px solid #fbbf24;
        text-align: center;
        color: #fbbf24;
        font-size: 22px;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    h1, h2, h3 { color: #fbbf24 !important; font-weight: normal !important; }
    p, span, div { font-weight: normal !important; }
    
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 4em;
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #475569;
        font-size: 16px;
    }
    .stButton>button:hover {
        border: 1px solid #fbbf24;
        color: #fbbf24;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. คำนวณเวลาและสถานะตลาด (อิงจากประวัติการเทรดของคุณ)
tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
day_of_week = now.weekday() 

def get_set_status(now):
    if day_of_week >= 5: return "CLOSED 🔴"
    time_val = now.hour * 100 + now.minute
    if (1000 <= time_val <= 1230) or (1430 <= time_val <= 1630):
        return "OPENING 🟢"
    return "CLOSED 🔴"

def get_us_status(now):
    if day_of_week >= 5: return "CLOSED 🔴"
    h = now.hour
    if (h >= 20) or (h <= 4): 
        return "OPENING 🟢"
    return "CLOSED 🔴"

# 3. Header
st.title("👨‍💻 Trading Control Center")
st.write(f"📅 {now.strftime('%A, %d %B %Y')} | 🕒 {now.strftime('%H:%M:%S')}")
st.write("---")

# 4. Market Status Section
st.subheader("🌐 Market Status")
m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    st.metric("SET (Thailand)", get_set_status(now))
with m_col2:
    st.metric("US Market", get_us_status(now))
with m_col3:
    # แสดงตัวหนังสือ Focus Tickers ตัวใหญ่ตรงกลางช่องตามสั่ง
    st.markdown('<div class="focus-box">FOCUS TICKERS</div>', unsafe_allow_html=True)

st.write("##")

# 5. Quick Navigation (เชื่อมโยงตามโครงสร้างไฟล์ในเครื่องคุณ)
st.subheader("🚀 Quick Navigation")
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

with row1_col1:
    if st.button("📈 Charts Thai Stocks"):
        st.switch_page("pages/2_Charts.py")
with row1_col2:
    if st.button("📊 Charts US Stocks"):
        st.switch_page("pages/4_US_Charts.py")
with row2_col1:
    if st.button("🔍 Scan Thai Stocks"):
        st.switch_page("pages/1_Scanner.py")
with row2_col2:
    if st.button("🇺🇸 Scan US Stocks"):
        st.switch_page("pages/3_US_Scanner.py")

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd.")
