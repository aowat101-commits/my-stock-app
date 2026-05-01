import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและ CSS
st.set_page_config(page_title="US Market Monitor", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    
    /* ตัวหนังสือปกติและสไตล์ตาราง Mobile Optimized */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        font-size: 11px !important;
        padding: 2px 4px !important;
        text-align: center !important;
        font-weight: normal !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นสหรัฐฯ ทั้งหมด (Full List เท่าหน้า Scan)
us_full_list = [
    'IONQ', 'IREN', 'EOSE', 'SMX', 'ONDS', 'PLTR', 'SOUN', 'BBAI', 'RGTI',
    'NVDA', 'AMD', 'TSM', 'INTC', 'ARM', 'MU', 'AVGO', 'ASML',
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA',
    'MARA', 'RIOT', 'CLSK', 'HIVE', 'COIN', 'MSTR',
    'XOM', 'CVX', 'CAT', 'GE', 'BA',
    'SPY', 'QQQ', 'SOXX', 'BITO', 'BTC-USD', 'ETH-USD'
]

# 3. ฟังก์ชันดึงข้อมูลภาพรวมและคำนวณ RSI (14)
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
                
                # การคำนวณ RSI (14)
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

# 4. ส่วนการแสดงผลตาราง
@st.fragment(run_every="5m")
def show_us_market_table():
    st.subheader("📊 US Market Monitor (RSI Alert)")
    df = get_us_summary_data()
    
    if not df.empty:
        # ฟังก์ชันกำหนดสีสำหรับแถว (รองรับเงื่อนไข RSI < 30 เป็นสีแดงทั้งแถว)
        def style_rows(row):
            if row['RSI (14)'] < 30:
                # หาก RSI ต่ำกว่า 30 ให้แสดงตัวหนังสือสีแดงเข้มเพื่อแจ้งเตือน
                return ['color: #ef4444; font-weight: normal;'] * len(row)
            
            # กรณีปกติ ใช้สีตามทิศทางราคา (เขียว/แดงปกติ)
            color = '#10b981' if row['Change'] > 0 else '#ef4444' if row['Change'] < 0 else '#888888'
            return [f'color: {color}; font-weight: normal;'] * len(row)

        df_display = df.copy()
        # ใส่ ⚠️ หน้า Ticker สำหรับตัวที่ RSI < 30
        df_display['Ticker'] = df_display.apply(lambda x: f"⚠️{x['Ticker']}" if x['RSI (14)'] < 30 else x['Ticker'], axis=1)
        df_display = df_display.sort_values(by="% Change", ascending=False)

        st.dataframe(
            df_display.style.apply(style_rows, axis=1)
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
            use_container_width=True, height=750, hide_index=True
        )
        
        now_th = datetime.now(pytz.timezone('Asia/Bangkok')).strftime("%H:%M:%S")
        st.caption(f"Refreshed: {now_th} (Thai Time) | Auto 5m | RSI < 30 Alert Color")

show_us_market_table()
