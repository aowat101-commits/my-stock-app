import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="Hull Suite Dashboard", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status {
        background-color: #1e293b;
        color: #10b981;
        padding: 8px;
        border-radius: 6px;
        text-align: center;
        font-size: 12px;
        margin-bottom: 15px;
        border: 1px solid #334155;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 11px !important; }
    [data-testid="stDataFrame"] td { font-size: 11px !important; text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นที่ติดตาม (อิงตามความสนใจของคุณ)
watch_list = [
    'IONQ', 'IREN', 'ONDS', 'SMX', 'DELTA.BK', 'GULF.BK', 'ADVANC.BK', 
    'PTT.BK', 'KBANK.BK', 'SCB.BK', 'CPALL.BK', 'AOT.BK', 'PTTEP.BK', 'HANA.BK'
]

# 3. ฟังก์ชันคำนวณ HMA (Length=30 ตามรูป 1777557236322.jpg)
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length = int(length / 2)
    sqrt_length = int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 4. ฟังก์ชันวิเคราะห์สัญญาณ (แดง->เขียว = ควรซื้อ / เขียว->แดง = ควรขาย)
def identify_hull_signal(df):
    if len(df) < 3: return None, None
    df['hma'] = get_hma(df['Close'], 30)
    curr_hma, prev_hma, prev2_hma = df['hma'].iloc[-1], df['hma'].iloc[-2], df['hma'].iloc[-3]

    curr_trend = "UP" if curr_hma > prev_hma else "DOWN"
    prev_trend = "UP" if prev_hma > prev2_hma else "DOWN"

    # แจ้งเตือนเฉพาะตอนเปลี่ยนสีเส้น HMA
    if prev_trend == "DOWN" and curr_trend == "UP":
        return "ควรซื้อ", datetime.now().strftime("%H:%M:%S")
    elif prev_trend == "UP" and curr_trend == "DOWN":
        return "ควรขาย", datetime.now().strftime("%H:%M:%S")
    return None, None

# 5. ดึงข้อมูลและกรองเฉพาะตัวที่มีสัญญาณ
@st.cache_data(ttl=600)
def get_actionable_data():
    action_list = []
    for t in watch_list:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="60d")
            if not hist.empty:
                sig, sig_time = identify_hull_signal(hist)
                if sig:
                    curr_p, prev_p = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                    action_list.append({
                        "หุ้น (Ticker)": t.replace('.BK', ''),
                        "ราคาปัจจุบัน": f"{curr_p:,.2f}",
                        "Chg%": ((curr_p - prev_p) / prev_p) * 100,
                        "Signal": sig,
                        "เวลา": sig_time
                    })
        except: continue
    return pd.DataFrame(action_list)

# 6. แสดงผล
st.markdown(f'<div class="time-status">🕒 Last Scan: {datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
st.subheader("🛰️ Hull Suite Dashboard")

df_filtered = get_actionable_data()

if not df_filtered.empty:
    def style_rows(row):
        s_color = '#10b981' if row['Signal'] == "ควรซื้อ" else '#ef4444'
        return ['', '', '', f'color: {s_color}; font-weight: bold;', 'color: #888888;']

    st.dataframe(
        df_filtered.style.apply(style_rows, axis=1).format({"Chg%": "{:+.2f}%"}),
        column_config={
            "หุ้น (Ticker)": st.column_config.TextColumn("Ticker", width=70),
            "ราคาปัจจุบัน": st.column_config.TextColumn("ราคา", width=60),
            "Chg%": st.column_config.NumberColumn("%", width=50),
            "Signal": st.column_config.TextColumn("Signal", width=80),
            "เวลา": st.column_config.TextColumn("เวลา", width=65),
        },
        use_container_width=True,
        height=500,
        hide_index=True
    )
else:
    st.info("🔎 ยังไม่พบสัญญาณเปลี่ยนสีในขณะนี้")

if st.button("🔄 สแกนใหม่", use_container_width=True):
    st.rerun()
