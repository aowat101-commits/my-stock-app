import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์
st.set_page_config(page_title="Trading Control Center", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0f172a; }
    
    /* การตกแต่ง Metrics ให้ดูทันสมัย */
    [data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        text-align: center;
    }
    
    /* ปรับสีตัวอักษรหัวข้อ */
    h1, h2, h3 { color: #fbbf24 !important; font-weight: normal !important; }
    p, span, div { font-weight: normal !important; }
    
    /* ปรับแต่งปุ่มกด Navigation */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 4em;
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #475569;
        font-size: 16px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        border: 1px solid #fbbf24;
        color: #fbbf24;
        background-color: #334155;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. คำนวณเวลาและสถานะตลาด
tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
day_of_week = now.weekday() # 0=Monday, 6=Sunday

# ฟังก์ชันเช็คสถานะตลาดไทย (10:00-12:30, 14:30-16:30 จันทร์-ศุกร์)
def get_set_status(now):
    if day_of_week >= 5: return "CLOSED (Weekend) 🔴"
    time_val = now.hour * 100 + now.minute
    if (1000 <= time_val <= 1230) or (1430 <= time_val <= 1630):
        return "OPENING 🟢"
    return "CLOSED 🔴"

# ฟังก์ชันเช็คสถานะตลาด US (20:30-03:00 จันทร์-ศุกร์ ตามเวลาไทย)
def get_us_status(now):
    if day_of_week >= 5: return "CLOSED (Weekend) 🔴"
    # ตลาด US เปิดคืนวันจันทร์ ถึงเช้ามืดวันเสาร์
    h = now.hour
    if (h >= 20) or (h <= 4): # ช่วงเวลาประมาณการเปิดตลาด US ในไทย
        return "OPENING 🟢"
    return "CLOSED 🔴"

# 3. Header Section
st.title("👨‍💻 Trading Control Center")
st.write(f"📅 {now.strftime('%A, %d %B %Y')} | 🕒 {now.strftime('%H:%M:%S')} (Thai Time)")
st.write("---")

# 4. Market Status Section (ขยายใหญ่ขึ้น)
st.subheader("🌐 Market Status")
m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    st.metric("SET (Thailand)", get_set_status(now))
with m_col2:
    st.metric("US Market", get_us_status(now))
with m_col3:
    st.metric("Focus Tickers", "IONQ / IREN")

st.write("##")

# 5. Quick Navigation Section (ลิ้งค์ตรงตามไฟล์ในเครื่องคุณ)
st.subheader("🚀 Quick Navigation")
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

with row1_col1:
    if st.button("📈 Charts Thai Stocks"):
        st.switch_page("pages/2_Charts.py") #

with row1_col2:
    if st.button("📊 Charts US Stocks"):
        st.switch_page("pages/4_US_Charts.py") #

with row2_col1:
    if st.button("🔍 Scan Thai Stocks"):
        st.switch_page("pages/1_Scanner.py") #

with row2_col2:
    if st.button("🇺🇸 Scan US Stocks"):
        st.switch_page("pages/3_US_Scanner.py") #

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Portfolio Management System")
