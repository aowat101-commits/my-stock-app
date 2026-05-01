import streamlit as st
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอแบบกว้างและสไตล์ Dashboard
st.set_page_config(page_title="Engineer & Trader Control Center", layout="wide")

# 2. Custom CSS สำหรับตกแต่ง (ตัวหนังสือปกติ ไม่หนา)
st.markdown("""
    <style>
    /* พื้นหลังและโทนสี */
    .main { background-color: #0f172a; }
    
    /* การตกแต่งการ์ดสถานะ */
    .stMetric {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #fbbf24; /* สีทอง Loft */
    }
    
    /* ปรับแต่งหัวข้อและตัวหนังสือ */
    h1, h2, h3 { color: #fbbf24 !important; font-weight: normal !important; }
    p, span, div { font-weight: normal !important; }
    
    /* ปุ่มเมนูหน้าหลัก */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
    }
    .stButton>button:hover {
        border: 1px solid #fbbf24;
        color: #fbbf24;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. ส่วนหัว (Header)
tz_th = pytz.timezone('Asia/Bangkok')
now_th = datetime.now(tz_th)

st.title("👨‍💻 Control Center")
st.write(f"สวัสดีครับ! วันที่ {now_th.strftime('%d/%m/%Y')} | เวลา {now_th.strftime('%H:%M')} น.")

st.write("---")

# 4. ส่วนสรุปสถานะ (Quick Stats)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Market Status", "US OPENED" if 20 <= now_th.hour or now_th.hour <= 4 else "US CLOSED")
with col2:
    st.metric("Project Focus", "Renovation") # อิงจากงาน Loft/Japanese Vintage
with col3:
    st.metric("Main Holdings", "IONQ / IREN") # หุ้นหลักที่ติดตาม
with col4:
    st.metric("Trading Signal", "HMA 30 System") # ระบบที่คุณใช้

st.write("##")

# 5. ส่วนเมนูทางลัด (Shortcut Menus)
st.subheader("🚀 Quick Navigation")
m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    if st.button("📊 Scan Thai Stocks"):
        st.switch_page("pages/2_Thai_Scanner.py")
with m_col2:
    if st.button("🇺🇸 Scan US Stocks"):
        st.switch_page("pages/3_US_Scanner.py")
with m_col3:
    if st.button("📈 Market Charts"):
        st.switch_page("pages/4_US_Charts.py")

st.write("---")

# 6. ส่วนงานวิศวกรรมและโปรเจกต์ (Engineering & Projects Section)
st.subheader("🛠️ Engineering & Renovation")
p_col1, p_col2 = st.columns(2)

with p_col1:
    with st.expander("📍 Active Projects", expanded=True):
        st.write("- **Industrial Automation:** PLC System Maintenance")
        st.write("- **Renovation:** Japanese Vintage Loft Project")
        st.write("- **System:** Reverse Osmosis (RO) Unit 1&2")

with p_col2:
    with st.expander("📝 To-do List", expanded=True):
        st.write("✅ ตรวจสอบราคา IREN/IONQ (HMA 30)")
        st.write("⏳ เช็คสต็อกสี TOA Shield-1 Nano")
        st.write("⏳ เตรียม BOQ สำหรับโครงการอาคารสำนักงาน")

st.caption("Developed by Por Piang Electric Plus Co., Ltd.")
