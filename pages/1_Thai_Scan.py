import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP ---
st.set_page_config(page_title="Guardian Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    /* Home Styling */
    .welcome-title { color: white; font-size: 26px; font-weight: bold; text-align: center; letter-spacing: 5px; margin-bottom: 0px; }
    .trading-home { color: #ffcc00; font-size: 22px; font-weight: bold; text-align: center; letter-spacing: 2px; margin-top: -10px; }
    .for-milk { color: white; font-style: italic; font-size: 18px; text-align: center; margin-bottom: 20px; font-family: 'Serif'; }
    
    .status-bar { color: #94a3b8; font-size: 14px; text-align: center; margin-top: 10px; }
    .market-status-head { color: white; font-size: 20px; font-weight: bold; display: flex; align-items: center; gap: 10px; margin-top: 20px; }

    /* Table Styling */
    .stDataFrame [data-testid="stTable"] td, .stDataFrame [data-testid="stTable"] th {
        color: #000000 !important; background-color: #ffffff !important; font-size: 13px !important;
    }

    /* Compact Buttons V6.4 Base */
    .stButton > button { height: 38px !important; font-size: 12px !important; border-radius: 6px !important; margin-bottom: -10px !important; }
    .block-container { padding-top: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCTION: THAI DATE ---
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
    st.markdown('<p class="for-milk">For Milk</p>', unsafe_allow_html=True)
    
    # กราฟหลักหน้า Home
    st.image("https://images.unsplash.com/photo-1611974717482-98aa007e690a?auto=format&fit=crop&q=80&w=1000", use_container_width=True)
    
    # วันที่และเวลาภาษาไทย
    st.markdown(f'<p class="status-bar">{t_date}  |  {t_time}</p>', unsafe_allow_html=True)
    
    st.markdown('<div class="market-status-head">🌐 Market Status</div>', unsafe_allow_html=True)
    st.write("---")
    st.info(f"สวัสดีครับคุณมิลค์ (Aowat Lukthong)\nบริษัท พอเพียง อิเล็คทริค พลัส จำกัด (PPE)")

elif cp == "Thai Scan":
    st.markdown(f'<div style="color:white; text-align:center; padding:10px;">🇹🇭 Thai Market Scan | {t_time}</div>', unsafe_allow_html=True)
    # ใส่ Engine สแกนหุ้นไทยที่นี่ (จาก V6.9)
    st.write("กำลังโหลดข้อมูลหุ้นไทย...")

elif cp == "Thai Charts":
    st.subheader("📊 Thai Charts")
    st.line_chart(yf.download("PTT.BK", period="1mo")['Close'])

elif cp == "US Scan":
    st.subheader("🇺🇸 US Scan")
    st.write("ข้อมูลหุ้น IONQ, IREN, NVDA...")

elif cp == "US Charts":
    st.subheader("📉 US Charts")
    st.line_chart(yf.download("IONQ", period="1mo")['Close'])

st.write("---")
st.caption(f"PPE Dashboard V7.1 | {t_date}")
