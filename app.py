import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์
st.set_page_config(page_title="Trading Home", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0f172a; }
    
    /* ปรับแต่งตัวหนังสือและ Metrics ให้ชัดเจนที่สุด */
    [data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-size: 28px !important;
    }
    [data-testid="stMetricLabel"] {
        color: #fbbf24 !important;
        font-size: 16px !important;
        font-weight: normal !important;
    }
    
    [data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #334155;
        text-align: center;
    }
    
    /* ช่อง Focus Ticker ตัวใหญ่กึ่งกลาง */
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

    h1 { color: #fbbf24 !important; font-weight: normal !important; text-align: center; margin-top: -20px; }
    h3 { color: #fbbf24 !important; font-weight: normal !important; }
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

# 2. ส่วนแสดงรูปภาพ Banner (รูปเท่ๆ ด้านบน)
st.image("https://images.unsplash.com/photo-1611974714851-eb605161882c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", 
         use_container_width=True)

# 3. Header (เปลี่ยนชื่อเป็น Trading Home)
st.markdown("<h1>📈 TRADING HOME</h1>", unsafe_allow_html=True)

tz_th = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz_th)
st.write(f"<p style='text-align: center; color: #94a3b8;'>📅 {now.strftime('%A, %d %B %Y')} | 🕒 {now.strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
st.write("---")

# 4. Market Status Section
st.subheader("🌐 Market Status")
m_col1, m_col2, m_col3 = st.columns(3)

def get_set_status(now):
    if now.weekday() >= 5: return "CLOSED 🔴"
    t = now.hour * 100 + now.minute
    return "OPENING 🟢" if (1000 <= t <= 1230) or (1430 <= t <= 1630) else "CLOSED 🔴"

def get_us_status(now):
    if now.weekday() >= 5: return "CLOSED 🔴"
    return "OPENING 🟢" if (now.hour >= 20) or (now.hour <= 4) else "CLOSED 🔴"

with m_col1:
    st.metric("SET (Thailand)", get_set_status(now))
with m_col2:
    st.metric("US Market", get_us_status(now))
with m_col3:
    st.markdown('<div class="focus-box">FOCUS TICKERS</div>', unsafe_allow_html=True)

st.write("##")

# 5. Quick Navigation
st.subheader("🚀 Quick Navigation")
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

with row1_col1:
    if st.button("📈 Charts Thai Stocks"): st.switch_page("pages/2_Charts.py")
with row1_col2:
    if st.button("📊 Charts US Stocks"): st.switch_page("pages/4_US_Charts.py")
with row2_col1:
    if st.button("🔍 Scan Thai Stocks"): st.switch_page("pages/1_Scanner.py")
with row2_col2:
    if st.button("🇺🇸 Scan US Stocks"): st.switch_page("pages/3_US_Scanner.py")

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Precision Engineering & Trading")
