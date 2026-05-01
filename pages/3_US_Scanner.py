import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Dark Loft (เน้นดูง่ายบนมือถือ)
st.set_page_config(page_title="US Market Signals", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status {
        background-color: #1e293b; color: #38bdf8; padding: 10px; border-radius: 6px;
        text-align: center; font-size: 13px; margin-bottom: 15px; border: 1px solid #0ea5e9;
    }
    [data-testid="stDataFrame"] th { background-color: #0f172a !important; color: #38bdf8 !important; text-align: center !important; font-size: 11px !important; }
    [data-testid="stDataFrame"] td { font-size: 11px !important; text-align: center !important; font-weight: normal !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นสหรัฐฯ (ดึงเฉพาะตัวที่คุณติดตามและตัวหลักๆ)
us_tickers = ['IREN', 'IONQ', 'SMX', 'ONDS', 'TSLA', 'NVDA', 'AAPL', 'AMD', 'MARA', 'RIOT']

# 3. ฟังก์ชันคำนวณ HMA 30
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 4. ฟังก์ชันค้นหาสัญญาณล่าสุด (ปรับให้แม่นยำขึ้นสำหรับหุ้น US)
def get_us_signal(df, ticker):
    if len(df) < 35: return None
    # ใช้ Timezone นิวยอร์กสำหรับหุ้นสหรัฐฯ
    tz_us = pytz.timezone('US/Eastern')
    
    df['hma'] = get_hma(df['Close'], 30)
    df['trend'] = np.where(df['hma'] > df['hma'].shift(1), "UP", "DOWN")
    df['is_switch'] = df['trend'] != df['trend'].shift(1)
    
    switches = df[df['is_switch'] == True].copy()
    if not switches.empty:
        last_sig = switches.iloc[-1]
        # แปลงเวลาเป็นฝั่ง US เพื่อให้ตรงกับหน้ากราฟ TradingView
        actual_time = last_sig.name.astimezone(tz_us)
        
        return {
            "Ticker": ticker,
            "Price": last_sig['Close'],
            "Signal": "🚀 BUY" if last_sig['trend'] == "UP" else "🔻 SELL",
            "US Time": actual_time.strftime("%H:%M:%S"),
            "Date": actual_time.strftime("%d/%m"),
            "raw_time": last_sig.name # ใช้เรียงลำดับ
        }
    return None

# 5. ส่วนหัวและปุ่มรีเฟรช
st.subheader("🇺🇸 US Tech & Crypto Stocks (HMA 30)")

if st.button("🔄 Refresh US Market", use_container_width=True):
    st.rerun()

# 6. Dashboard Runtime (Auto-scan)
@st.fragment(run_every="5m") # หุ้น US วิ่งไว ปรับสแกนทุก 5 นาที
def us_dashboard():
    now_us = datetime.now(pytz.timezone('US/Eastern')).strftime("%H:%M:%S")
    st.markdown(f'<div class="time-status">🗽 NY Time: {now_us} | สแกนสัญญาณล่าสุดในตลาดสหรัฐฯ</div>', unsafe_allow_html=True)
    
    results = []
    bar = st.progress(0)
    
    for i, t in enumerate(us_tickers):
        try:
            stock = yf.Ticker(t)
            # ดึงย้อนหลัง 20 วัน เพื่อให้คำนวณ HMA ได้แน่นอน
            hist = stock.history(period="20d", interval="1h")
            if not hist.empty:
                res = get_us_signal(hist, t)
                if res: results.append(res)
        except: continue
        bar.progress((i + 1) / len(us_tickers))
    
    bar.empty()

    if results:
        df = pd.DataFrame(results).sort_values(by="raw_time", ascending=False)
        
        def style_row(row):
            color = '#10b981' if "BUY" in row['Signal'] else '#ef4444'
            return [f'color: {color};'] * len(row)

        st.dataframe(
            df.drop(columns=['raw_time']).style.apply(style_row, axis=1)
            .format({"Price": "{:,.2f}"}),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=70),
                "Price": st.column_config.NumberColumn("Price", width=70, format="%.2f"),
                "Signal": st.column_config.TextColumn("Signal", width=80),
                "US Time": st.column_config.TextColumn("US Time", width=80),
                "Date": st.column_config.TextColumn("Date", width=60),
            },
            use_container_width=True, height=500, hide_index=True
        )

us_dashboard()