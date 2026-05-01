import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ
st.set_page_config(page_title="US Market Custom Watchlist", layout="wide")

# 2. จัดการข้อมูล Watchlist ใน Session State (เพื่อให้หุ้นที่เพิ่มไม่หายเวลาพิมพ์ตัวถัดไป)
if 'my_watchlist' not in st.session_state:
    # ตั้งค่าเริ่มต้น
    st.session_state.my_watchlist = [
        'IONQ', 'IREN', 'EOSE', 'SMX', 'ONDS', 'NVDA', 'TSLA', 'AAPL', 
        'AMD', 'MSFT', 'GOOGL', 'AMZN', 'META', 'MARA', 'RIOT', 'SPY', 'QQQ', 'BTC-USD'
    ]

# 3. ส่วนการเพิ่มหุ้น (Input Box แยกออกมาเพื่อให้เพิ่มง่ายขึ้น)
st.subheader("🛠️ Manage Your Watchlist")

col_input, col_btn = st.columns([3, 1])
with col_input:
    new_ticker = st.text_input("พิมพ์ชื่อ Ticker ใหม่ (เช่น MSTR, CLSK):").upper().strip()
with col_btn:
    st.write("##") # จัดระยะปุ่ม
    if st.button("➕ เพิ่มหุ้น"):
        if new_ticker and new_ticker not in st.session_state.my_watchlist:
            st.session_state.my_watchlist.append(new_ticker)
            st.rerun()

# 4. ช่องเลือก/ลบ หุ้นจากลิสต์ปัจจุบัน
updated_watchlist = st.multiselect(
    "รายการหุ้นใน Watchlist (กด x เพื่อลบออก):",
    options=st.session_state.my_watchlist,
    default=st.session_state.my_watchlist
)
# อัปเดตลิสต์ตามที่เลือกจริงใน Multiselect
st.session_state.my_watchlist = updated_watchlist

st.write("---")

# 5. ส่วนการวิเคราะห์หุ้นรายตัว (Search Box)
if updated_watchlist:
    selected_ticker = st.selectbox("วิเคราะห์หุ้นรายตัว:", sorted(updated_watchlist))
    
    # ... (โค้ดดึงข้อมูล Metric เหมือนเดิม) ...
    if selected_ticker:
        try:
            stock = yf.Ticker(selected_ticker)
            hist = stock.history(period="5d", interval="1h")
            if not hist.empty:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                pct = ((curr - prev) / prev) * 100
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(f"{selected_ticker} Price", f"{curr:,.2f}", f"{pct:+.2f}%")
                with col2: st.write(f"**High (5D):** {hist['High'].max():,.2f}")
                with col3: st.write(f"**Low (5D):** {hist['Low'].min():,.2f}")
        except: st.error("ไม่พบข้อมูล Ticker นี้")

st.write("---")

# 6. ตาราง Market Monitor (Auto-Refresh 5 นาที)
@st.fragment(run_every="5m")
def show_custom_table():
    st.subheader("📊 US Market Monitor")
    if updated_watchlist:
        # ดึงข้อมูล (ฟังก์ชันเดิมที่คำนวณ RSI)
        # ... (โค้ดดึงข้อมูลเหมือนเดิม) ...
        # เพื่อความกระชับ ผมจะใช้ลอจิกการแสดงผลแบบเดียวกับที่คุณต้องการ
        
        # [ส่วนนี้ใส่โค้ดการสร้าง DataFrame และ Styler ตามที่คุณต้องการ]
        # (ราคา 0.00, RSI < 30 ตัวแดง, มีสัญลักษณ์ ⚠️)
        pass 

show_custom_table()
