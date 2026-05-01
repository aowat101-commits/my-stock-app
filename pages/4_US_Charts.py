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

# 2. จัดการ Watchlist ด้วย Session State (เพื่อให้หุ้นที่เพิ่มไม่หาย)
if 'my_watchlist' not in st.session_state:
    st.session_state.my_watchlist = [
        'IONQ', 'IREN', 'EOSE', 'SMX', 'ONDS', 'NVDA', 'TSLA', 'AAPL', 
        'AMD', 'MSFT', 'GOOGL', 'AMZN', 'META', 'MARA', 'RIOT', 'SPY', 'QQQ', 'BTC-USD'
    ]

# 3. ส่วนการเพิ่มหุ้น (Input Box)
st.subheader("🛠️ Manage Your Watchlist")
col_input, col_btn = st.columns([3, 1])
with col_input:
    new_ticker = st.text_input("พิมพ์ชื่อ Ticker ใหม่ (เช่น MSTR, CLSK):").upper().strip()
with col_btn:
    st.write("##")
    if st.button("➕ เพิ่มหุ้น", use_container_width=True):
        if new_ticker and new_ticker not in st.session_state.my_watchlist:
            st.session_state.my_watchlist.append(new_ticker)
            st.rerun()

# ช่อง Multiselect สำหรับดูและลบหุ้น
updated_watchlist = st.multiselect(
    "หุ้นในลิสต์ปัจจุบัน (กด x เพื่อลบออก):",
    options=st.session_state.my_watchlist,
    default=st.session_state.my_watchlist
)
st.session_state.my_watchlist = updated_watchlist

st.write("---")

# 4. ส่วนการวิเคราะห์หุ้นรายตัว (Search Box)
if updated_watchlist:
    selected_ticker = st.selectbox("วิเคราะห์รายละเอียดรายตัว:", sorted(updated_watchlist))
    if selected_ticker:
        try:
            stock = yf.Ticker(selected_ticker)
            hist = stock.history(period="5d", interval="1h")
            if not hist.empty:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                pct = ((curr - prev) / prev) * 100
                col1, col2, col3 = st.columns(3)
                with col1: st.metric(f"{selected_ticker}", f"{curr:,.2f}", f"{pct:+.2f}%")
                with col2: st.write(f"**High (5D):** {hist['High'].max():,.2f}")
                with col3: st.write(f"**Low (5D):** {hist['Low'].min():,.2f}")
        except: st.error("ไม่สามารถดึงข้อมูลได้")

st.write("---")

# 5. ฟังก์ชันดึงข้อมูลภาพรวม (RSI + Change)
@st.cache_data(ttl=600) # Cache 10 นาทีเพื่อความลื่นไหล
def get_us_summary_data(tickers):
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

# 6. การแสดงผลตาราง Market Monitor (Auto-Refresh 5 นาที)
@st.fragment(run_every="5m")
def show_us_market_table():
    st.subheader("📊 US Market Monitor")
    if updated_watchlist:
        df = get_us_summary_data(updated_watchlist)
        if not df.empty:
            # สไตล์เฉพาะช่อง RSI
            def style_rsi_col(val):
                color = '#ef4444' if val < 30 else '#888888'
                return f'color: {color}; font-weight: normal;'

            # สไตล์ช่องทั่วไป
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
            st.caption(f"Refreshed: {now_th} (Thai Time) | Auto 5m | RSI < 30 ตัวแดง")
    else:
        st.info("กรุณาเพิ่มหรือเลือกหุ้นใน Watchlist")

show_us_market_table()
