import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและ CSS (ตัวหนังสือปกติ, สไตล์เดียวกับหุ้นไทย)
st.set_page_config(page_title="US Market & Search", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    
    /* ตัวหนังสือปกติ (Normal Weight) และสไตล์ตาราง Mobile Optimized */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        font-size: 11px !important;
        padding: 2px 4px !important;
        text-align: center !important;
        font-weight: normal !important;
    }
    
    .stMetric, .stSelectbox, .stButton, p, span, div {
        font-weight: normal !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นสหรัฐฯ ทั้งหมด
us_full_list = [
    'IONQ', 'IREN', 'EOSE', 'SMX', 'ONDS', 'PLTR', 'SOUN', 'BBAI', 'RGTI',
    'NVDA', 'AMD', 'TSM', 'INTC', 'ARM', 'MU', 'AVGO', 'ASML',
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA',
    'MARA', 'RIOT', 'CLSK', 'HIVE', 'COIN', 'MSTR',
    'SPY', 'QQQ', 'SOXX', 'BITO', 'BTC-USD', 'ETH-USD'
]

# 3. ส่วนการค้นหาหุ้นรายตัว (Search Box)
st.subheader("🔍 Search & Analyze US Stock")
selected_ticker = st.selectbox("เลือกชื่อหุ้นเพื่อดูรายละเอียด:", sorted(us_full_list))

# ฟังก์ชันแสดงผลการค้นหาแบบสรุป
def show_search_analysis(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d", interval="1h")
        if not hist.empty:
            curr = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            pct = ((curr - prev) / prev) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{ticker} Price", f"{curr:,.2f}", f"{pct:+.2f}%")
            with col2:
                st.write(f"**High (Last 5D):** {hist['High'].max():,.2f}")
            with col3:
                st.write(f"**Low (Last 5D):** {hist['Low'].min():,.2f}")
    except:
        st.error("ไม่สามารถโหลดข้อมูลการค้นหาได้")

if selected_ticker:
    show_search_analysis(selected_ticker)

st.write("---")

# 4. ส่วนตารางภาพรวม (Market Monitor)
st.subheader("📊 US Market Monitor (Thai Time)")

# ฟังก์ชันดึงข้อมูลภาพรวม (RSI + Change)
@st.cache_data(ttl=1800)
def get_us_summary_data():
    data_list = []
    for t in us_full_list:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="30d")
            if not hist.empty and len(hist) >= 15:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff = curr - prev
                pct = (diff / prev) * 100 if prev != 0 else 0
                
                # RSI Calculation
                delta = hist['Close'].diff()
                up = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
                down = -delta.clip(upper=0).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (up / down))) if down != 0 else 100

                data_list.append({
                    "Ticker": t,
                    "Price": curr,
                    "Change": diff,
                    "% Change": pct,
                    "RSI (14)": rsi
                })
        except: continue
    return pd.DataFrame(data_list)

# 5. การแสดงผลตารางแบบ Auto-Refresh
@st.fragment(run_every="5m")
def show_us_market_table():
    df = get_us_summary_data()
    
    if not df.empty:
        # Style setting (Normal weight)
        def style_general(val):
            color = '#10b981' if val > 0 else '#ef4444' if val < 0 else '#888888'
            return f'color: {color}; font-weight: normal;'

        def style_row_base(row):
            color = '#10b981' if row['Change'] > 0 else '#ef4444' if row['Change'] < 0 else '#888888'
            return [f'color: {color};', f'color: {color};', '', '', '']

        df_display = df.copy()
        # แจ้งเตือน RSI < 30
        df_display['Ticker'] = df_display.apply(lambda x: f"⚠️{x['Ticker']}" if x['RSI (14)'] < 30 else x['Ticker'], axis=1)
        df_display = df_display.sort_values(by="% Change", ascending=False)

        st.dataframe(
            df_display.style.apply(style_row_base, axis=1) \
                    .map(style_general, subset=['Change', '% Change']) \
                    .format({
                        "% Change": "{:+.2f}%", 
                        "Change": "{:+.2f}",
                        "Price": "{:,.2f}",
                        "RSI (14)": "{:.0f}"
                    }),
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
        st.caption(f"Refreshed: {now_th} (Thai Time) | Auto 5m | Decimal 0.00")

show_us_market_table()
