import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ (เน้นตัวหนังสือปกติและโทน Dark)
st.set_page_config(page_title="US Stock Analysis", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    /* ตั้งค่าตัวหนังสือทั้งหมดให้เป็นตัวธรรมดา (Normal Weight) */
    .main, .stText, .stMarkdown, p, div, span {
        font-weight: normal !important;
    }
    .metric-container {
        background-color: #1e293b; padding: 15px; border-radius: 10px; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นสหรัฐฯ ทั้งหมด (Full List)
us_full_list = [
    'IONQ', 'IREN', 'EOSE', 'SMX', 'ONDS', 'PLTR', 'SOUN', 'BBAI', 'RGTI',
    'NVDA', 'AMD', 'TSM', 'INTC', 'ARM', 'MU', 'AVGO', 'ASML',
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA',
    'MARA', 'RIOT', 'CLSK', 'HIVE', 'COIN', 'MSTR',
    'SPY', 'QQQ', 'SOXX', 'BTC-USD'
]

# 3. ส่วนหัวและแถบเลือกหุ้น
st.subheader("🇺🇸 US Individual Stock Analysis")

selected_ticker = st.selectbox("ค้นหาหรือเลือกหุ้นที่คุณต้องการ:", sorted(us_full_list))

if st.button("🔄 Refresh Data", use_container_width=True):
    st.rerun()

# 4. ฟังก์ชันดึงข้อมูลและแสดงผล
def show_us_analysis(ticker):
    try:
        stock = yf.Ticker(ticker)
        # ดึงข้อมูลย้อนหลัง 30 วัน (Timeframe 1h)
        df = stock.history(period="30d", interval="1h")
        
        if not df.empty:
            # ราคาปัจจุบันและส่วนต่าง
            current_price = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            change = current_price - prev_close
            pct_change = (change / prev_close) * 100

            # ส่วนการแสดงราคา (Metrics)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Price (Current)", f"{current_price:,.2f}", f"{pct_change:+.2f}%")
            with col2:
                st.metric("High (30D)", f"{df['High'].max():,.2f}")
            with col3:
                st.metric("Low (30D)", f"{df['Low'].min():,.2f}")

            st.write("---")
            
            # ตารางข้อมูลย้อนหลัง 20 แท่งล่าสุด
            st.write(f"📊 Recent 1-Hour Candles: {ticker}")
            
            # เตรียมตารางสำหรับแสดงผล
            df_display = df.tail(20).copy()
            # แปลงเวลาเป็นเวลาไทย (GMT+7)
            tz_th = pytz.timezone('Asia/Bangkok')
            df_display.index = df_display.index.tz_convert(tz_th)
            
            # แสดงตารางข้อมูลแบบตัวธรรมดา
            st.dataframe(
                df_display[['Open', 'High', 'Low', 'Close', 'Volume']].sort_index(ascending=False).style.format("{:,.2f}"),
                use_container_width=True,
                height=450
            )
            
            st.caption(f"Refreshed at: {datetime.now(tz_th).strftime('%H:%M:%S')} (Thai Time)")
        else:
            st.warning("ไม่พบข้อมูลสำหรับหุ้นตัวนี้ในขณะนี้")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")

# เรียกใช้งานฟังก์ชัน
if selected_ticker:
    show_us_analysis(selected_ticker)