import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP (Ultra Compact & Large Header) ---
st.set_page_config(page_title="Guardian Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    /* Home Styling - ปรับขนาดตัวอักษรให้ใหญ่ขึ้นตามสั่ง */
    .welcome-title { 
        color: white; 
        font-size: 36px; /* ขยายใหญ่ขึ้น */
        font-weight: 800; 
        text-align: center; 
        letter-spacing: 8px; 
        margin-top: 10px;
        margin-bottom: 5px; 
    }
    .trading-home { 
        color: #ffcc00; 
        font-size: 30px; /* ขยายใหญ่ขึ้น */
        font-weight: 800; 
        text-align: center; 
        letter-spacing: 3px; 
        margin-top: -5px;
        margin-bottom: 25px;
    }
    
    .status-bar { color: #ffffff; font-size: 15px; text-align: center; margin-top: 15px; font-weight: 500; }
    .market-status-head { color: white; font-size: 20px; font-weight: bold; display: flex; align-items: center; gap: 10px; margin-top: 25px; }

    /* Table Styling */
    .stDataFrame [data-testid="stTable"] td, .stDataFrame [data-testid="stTable"] th {
        color: #000000 !important; background-color: #ffffff !important; font-size: 13px !important;
    }

    /* Navigation Buttons */
    .stButton > button { height: 42px !important; font-size: 14px !important; border-radius: 8px !important; margin-bottom: -10px !important; }
    .block-container { padding-top: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCTION: THAI DATETIME ---
def get_thai_datetime():
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
    months = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    thai_date = f"📅 วัน{days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year + 543}"
    thai_time = f"🕒 {now.strftime('%H:%M:%S')}"
    return thai_date, thai_time

# --- 3. NAVIGATION ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Home'

if st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.current_page == 'Home' else "secondary"):
    st.session_state.current_page = 'Home'

c1, c2 = st.columns(2)
with c1:
    if st.button("📈 Thai Scan", use_container_width=True, type="primary" if st.session_state.current_page == 'Thai Scan' else "secondary"):
        st.session_state.current_page = 'Thai Scan'
with c2:
    if st.button("📊 Thai Charts", use_container_width=True, type="primary" if st.session_state.current_page == 'Thai Charts' else "secondary"):
        st.session_state.current_page = 'Thai Charts'

c3, c4 = st.columns(2)
with c3:
    if st.button("🇺🇸 US Scan", use_container_width=True, type="primary" if st.session_state.current_page == 'US Scan' else "secondary"):
        st.session_state.current_page = 'US Scan'
with c4:
    if st.button("📉 US Charts", use_container_width=True, type="primary" if st.session_state.current_page == 'US Charts' else "secondary"):
        st.session_state.current_page = 'US Charts'

# --- 4. PAGE CONTENT ---
cp = st.session_state.current_page
t_date, t_time = get_thai_datetime()

if cp == "Home":
    st.markdown('<p class="welcome-title">WELCOME</p>', unsafe_allow_html=True)
    st.markdown('<p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    
    # รูปภาพหน้าโฮม
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000&auto=format&fit=crop", use_container_width=True)
    
    # วันที่และเวลาภาษาไทย
    st.markdown(f'<p class="status-bar">{t_date}  |  {t_time}</p>', unsafe_allow_html=True)
    
    # Market Status Section
    st.markdown('<div class="market-status-head">🌐 Market Status</div>', unsafe_allow_html=True)
    st.write("---")

elif cp == "Thai Scan":
    st.markdown(f'<div style="color:white; text-align:center; padding:10px;">🇹🇭 Thai Market Scan | {t_time}</div>', unsafe_allow_html=True)
    st.info("กำลังโหลดข้อมูลหุ้นไทย...")

elif cp == "Thai Charts":
    st.subheader("📊 Thai Charts")
    st.line_chart(yf.download("PTT.BK", period="1mo")['Close'])

elif cp == "US Scan":
    st.subheader("🇺🇸 US Scan")
    st.info("กำลังโหลดข้อมูลหุ้น US...")

elif cp == "US Charts":
    st.subheader("📉 US Charts")
    st.line_chart(yf.download("IONQ", period="1mo")['Close'])
