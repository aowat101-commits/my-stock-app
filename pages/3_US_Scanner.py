import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์
st.set_page_config(page_title="US Stocks (Thai Time)", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status {
        background-color: #1e293b; color: #fbbf24; padding: 10px; border-radius: 6px;
        text-align: center; font-size: 13px; margin-bottom: 15px; border: 1px solid #d97706;
    }
    [data-testid="stDataFrame"] th { background-color: #0f172a !important; color: #fbbf24 !important; text-align: center !important; font-size: 11px !important; }
    [data-testid="stDataFrame"] td { font-size: 12px !important; text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นสหรัฐฯ
us_tickers = ['IREN', 'IONQ', 'SMX', 'ONDS', 'TSLA', 'NVDA', 'AAPL', 'AMD', 'MARA', 'RIOT']

# 3. ฟังก์ชันคำนวณ HMA 30
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 4. ฟังก์ชันค้นหาสัญญาณล่าสุด (แปลงเป็นเวลาไทย)
def get_us_signal_th_time(df, ticker):
    if len(df) < 35: return None
    # กำหนด Timezone ไทย
    tz_th = pytz.timezone('Asia/Bangkok')
    
    df['hma'] = get_hma(df['Close'], 30)
    df['trend'] = np.where(df['hma'] > df['hma'].shift(1), "UP", "DOWN")
    df['is_switch'] = df['trend'] != df['trend'].shift(1)
    
    switches = df[df['is_switch'] == True].copy()
    if not switches.empty:
        last_sig = switches.iloc[-1]
        # แปลงจากเวลาตลาด (UTC) มาเป็นเวลาไทย
        actual_time_th = last_sig.name.astimezone(tz_th)
        
        return {
            "Ticker": ticker,
            "Price": last_sig['Close'],
            "Signal": "🚀 BUY" if last_sig['trend'] == "UP" else "🔻 SELL",
            "เวลาไทย": actual_time_th.strftime("%H:%M:%S"),
            "วันที่": actual_time_th.strftime("%d/%m"),
            "raw_time": last_sig.name 
        }
    return None

# 5. ส่วนหัวและปุ่มรีเฟรช
st.subheader("🇺🇸 US Market Monitor (Thai Timezone)")

if st.button("🔄 Refresh US Market", use_container_width=True):
    st.rerun()

# 6. Dashboard Runtime
@st.fragment(run_every="5m")
def us_dashboard_th():
    now_th = datetime.now(pytz.timezone('Asia/Bangkok')).strftime("%H:%M:%S")
    st.markdown(f'<div class="time-status">🇹🇭 Current Thai Time: {now_th} | สัญญาณหุ้น US ในเวลาไทย</div>', unsafe_allow_html=True)
    
    results = []
    bar = st.progress(0)
    
    for i, t in enumerate(us_tickers):
        try:
            stock = yf.Ticker(t)
            # ดึงข้อมูลย้อนหลัง 20 วัน เพื่อความแม่นยำของ HMA
            hist = stock.history(period="20d", interval="1h")
            if not hist.empty:
                res = get_us_signal_th_time(hist, t)
                if res: results.append(res)
        except: continue
        bar.progress((i + 1) / len(us_tickers))
    
    bar.empty()

    if results:
        df = pd.DataFrame(results).sort_values(by="raw_time", ascending=False)
        
        def style_row(row):
            color = '#10b981' if "BUY" in row['Signal'] else '#ef4444'
            return [f'color: {color}; font-weight: bold;'] * len(row)

        st.dataframe(
            df.drop(columns=['raw_time']).style.apply(style_row, axis=1)
            .format({"Price": "{:,.2f}"}),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=70),
                "Price": st.column_config.NumberColumn("Price", width=70, format="%.2f"),
                "Signal": st.column_config.TextColumn("Signal", width=80),
                "เวลาไทย": st.column_config.TextColumn("เวลาไทย", width=85),
                "วันที่": st.column_config.TextColumn("วันที่", width=60),
            },
            use_container_width=True, height=500, hide_index=True
        )

us_dashboard_th()
