import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและ CSS
st.set_page_config(page_title="US Market Custom Watchlist", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        font-size: 11px !important;
        padding: 2px 4px !important;
        text-align: center !important;
        font-weight: normal !important;
    }
    .stMetric, .stSelectbox, .stMultiSelect, .stButton, p, span, div {
        font-weight: normal !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นพื้นฐาน (Default List)
default_us_list = [
    'IONQ', 'IREN', 'EOSE', 'SMX', 'ONDS', 'NVDA', 'TSLA', 'AAPL', 
    'AMD', 'MSFT', 'GOOGL', 'AMZN', 'META', 'MARA', 'RIOT', 'SPY', 'QQQ', 'BTC-USD'
]

# 3. ช่องสำหรับเพิ่ม/ลบ หุ้นในลิสต์ (Custom Watchlist)
st.subheader("🛠️ Manage Your Watchlist")
# ใช้ multiselect ที่ยอมให้พิมพ์ชื่อหุ้นใหม่ๆ เข้าไปได้เอง
updated_watchlist = st.multiselect(
    "พิมพ์ชื่อ Ticker (เช่น MSTR, CLSK) แล้วกด Enter เพื่อเพิ่มเข้าไปในตารางสแกน:",
    options=sorted(list(set(default_us_list))), # รายการเริ่มต้น
    default=default_us_list
)

st.write("---")

# 4. ส่วนการค้นหาหุ้นรายตัว (Search Box จากลิสต์ที่คุณเลือก)
if updated_watchlist:
    selected_ticker = st.selectbox("วิเคราะห์หุ้นรายตัว:", sorted(updated_watchlist))
    
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
                with col2:
                    st.write(f"**High (5D):** {hist['High'].max():,.2f}")
                with col3:
                    st.write(f"**Low (5D):** {hist['Low'].min():,.2f}")
        except:
            st.error("ไม่พบข้อมูล Ticker นี้ กรุณาตรวจสอบชื่อหุ้นอีกครั้ง")

st.write("---")

# 5. ฟังก์ชันดึงข้อมูลภาพรวม (RSI + Change)
@st.cache_data(ttl=1800)
def get_custom_market_data(tickers):
    data_list = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="30d")
            if not hist.empty and len(hist) >= 15:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff = curr - prev
                pct = (diff / prev) * 100 if prev != 0 else 0
                
                delta = hist['Close'].diff()
                up = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
                down = -delta.clip(upper=0).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (up / down))) if down != 0 else 100

                data_list.append({
                    "Ticker": t, "Price": curr, "Change": diff, "% Change": pct, "RSI (14)": rsi
                })
        except: continue
    return pd.DataFrame(data_list)

# 6. การแสดงผลตารางภาพรวม (Market Monitor)
@st.fragment(run_every="5m")
def show_custom_table():
    st.subheader("📊 US Market Monitor (Your Watchlist)")
    
    if updated_watchlist:
        df = get_custom_market_data(updated_watchlist)
        
        if not df.empty:
            def style_rsi_col(val):
                return f'color: #ef4444; font-weight: normal;' if val < 30 else 'color: #888888; font-weight: normal;'

            def style_general_cols(val):
                color = '#10b981' if val > 0 else '#ef4444' if val < 0 else '#888888'
                return f'color: {color}; font-weight: normal;'

            df_display = df.copy()
            df_display['Ticker'] = df_display.apply(lambda x: f"⚠️{x['Ticker']}" if x['RSI (14)'] < 30 else x['Ticker'], axis=1)
            df_display = df_display.sort_values(by="% Change", ascending=False)

            st.dataframe(
                df_display.style \
                        .map(style_general_cols, subset=['Change', '% Change']) \
                        .map(style_rsi_col, subset=['RSI (14)']) \
                        .format({"% Change": "{:+.2f}%", "Change": "{:+.2f}", "Price": "{:,.2f}", "RSI (14)": "{:.0f}"}),
                column_config={
                    "Ticker": st.column_config.TextColumn("Ticker", width=75),
                    "Price": st.column_config.NumberColumn("Price", width=60),
                    "Change": st.column_config.NumberColumn("Change", width=60),
                    "% Change": st.column_config.NumberColumn("% Change", width=70),
                    "RSI (14)": st.column_config.NumberColumn("RSI (14)", width=50),
                },
                use_container_width=True, height=600, hide_index=True
            )
            now_th = datetime.now(pytz.timezone('Asia/Bangkok')).strftime("%H:%M:%S")
            st.caption(f"Refreshed: {now_th} | Auto 5m | ช่อง RSI ตัวสีแดงเมื่อ < 30")
    else:
        st.info("กรุณาเลือกหรือพิมพ์ชื่อหุ้นในช่องด้านบนเพื่อเริ่มการสแกน")

show_custom_table()
