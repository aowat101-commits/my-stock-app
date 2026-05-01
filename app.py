import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์
st.set_page_config(page_title="Control Center", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0f172a; }
    .stMetric {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #fbbf24;
    }
    h1, h2, h3 { color: #fbbf24 !important; font-weight: normal !important; }
    p, span, div { font-weight: normal !important; }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        font-size: 14px;
    }
    .stButton>button:hover {
        border: 1px solid #fbbf24;
        color: #fbbf24;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Header & Time
tz_th = pytz.timezone('Asia/Bangkok')
now_th = datetime.now(tz_th)

st.title("👨‍💻 Control Center")
st.write(f"วันที่ {now_th.strftime('%d/%m/%Y')} | เวลา {now_th.strftime('%H:%M')} น.")
st.write("---")

# 3. Quick Stats (Metrics)
col1, col2, col3, col4 = st.columns(4)
with col1:
    # ตลาดเมกาเปิด 20:30 (หรือ 21:30 หน้าหนาว) - 03:00/04:00
    is_us_open = 20 <= now_th.hour or now_th.hour <= 4
    st.metric("US Market", "OPEN 🟢" if is_us_open else "CLOSED 🔴")
with col2:
    # ตลาดไทยเปิด 10:00-12:30 และ 14:30-16:30
    is_th_open = (10 <= now_th.hour < 13) or (14 <= now_th.hour < 17)
    st.metric("Thai Market", "OPEN 🟢" if is_th_open else "CLOSED 🔴")
with col3:
    st.metric("Project", "Renovation")
with col4:
    st.metric("Focus Tickers", "IONQ / IREN")

st.write("##")

# 4. Quick Navigation (เพิ่มปุ่ม Charts หุ้นไทย)
st.subheader("🚀 Quick Navigation")
# แบ่งเป็น 2 แถว แถวละ 2 ปุ่ม เพื่อให้กดง่ายบนมือถือ
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

with row1_col1:
    if st.button("📈 Charts Thai Stocks"):
        # สมมติว่าไฟล์หน้า Charts หุ้นไทยชื่อ 2_Charts.py (ปรับชื่อตามจริงได้เลยครับ)
        st.switch_page("pages/2_Thai_Charts.py")
with row1_col2:
    if st.button("📊 Charts US Stocks"):
        st.switch_page("pages/4_US_Charts.py")

with row2_col1:
    if st.button("🔍 Scan Thai Stocks"):
        st.switch_page("pages/2_Thai_Scanner.py")
with row2_col2:
    if st.button("🇺🇸 Scan US Stocks"):
        st.switch_page("pages/3_US_Scanner.py")

st.write("---")

# 5. Engineering & Projects Section
st.subheader("🛠️ Engineering & Renovation")
p_col1, p_col2 = st.columns(2)

with p_col1:
    with st.expander("📍 Active Projects", expanded=True):
        st.write("- **Industrial Automation:** PLC System Maintenance")
        st.write("- **Renovation:** Japanese Vintage Loft Project")
        st.write("- **Infrastructure:** Office BOQ Preparation")

with p_col2:
    with st.expander("📝 To-do List", expanded=True):
        st.write("✅ ตรวจสอบ HMA 30 Signals (US Market)")
        st.write("⏳ เช็คหน้างานติดตั้งระบบไฟฟ้าโรงงาน")
        st.write("⏳ อัปเดตรายการหุ้นใน Watchlist")

st.caption("Developed by Por Piang Electric Plus Co., Ltd.")
