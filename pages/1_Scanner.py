import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="Hull Suite Intelligence", layout="wide")

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
    /* หัวตาราง */
    [data-testid="stDataFrame"] th { 
        background-color: #1e293b !important; 
        color: #94a3b8 !important; 
        text-align: center !important; 
        font-size: 11px !important; 
    }
    /* เนื้อหาตารางตัวธรรมดาและจัดกลาง */
    [data-testid="stDataFrame"] td { 
        font-size: 11px !important; 
        text-align: center !important; 
        font-weight: normal !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นที่ติดตาม (อ้างอิงจากความสนใจในเทคโนโลยีและพลังงาน)
watch_list = [
    'IONQ', 'IREN', 'ONDS', 'SMX', 'DELTA.BK', 'GULF.BK', 'ADVANC.BK', 
    'PTT.BK', 'KBANK.BK', 'SCB.BK', 'CPALL.BK', 'AOT.BK', 'PTTEP.BK', 'HANA.BK'
]

# 3. ฟังก์ชันคำนวณ HMA (Length=30 ตามความต้องการใช้งาน)
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length = int(length / 2)
    sqrt_length = int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 4. ฟังก์ชันวิเคราะห์สัญญาณ (แดงเป็นเขียว = ซื้อ / เขียวเป็นแดง = ขาย)
def identify_hull_signal(df):
    if len(df) < 3: return None, None
    df['hma'] = get_hma(df['Close'], 30)
    curr_hma = df['hma'].iloc[-1]
    prev_hma = df['hma'].iloc[-2]
    prev2_hma = df['hma'].iloc[-3]

    curr_trend = "UP" if curr_hma > prev_hma else "DOWN"
    prev_trend = "UP" if prev_hma > prev2_hma else "DOWN"

    tz = pytz.timezone('Asia/Bangkok')
    now_time = datetime.now(tz).strftime("%H:%M:%S")

    # บังคับใส่ลูกศรลงในข้อความ Signal โดยตรง
    if prev_trend == "DOWN" and curr_trend == "UP":
        return "🚀 ซื้อ", now_time
    elif prev_trend == "UP" and curr_trend == "DOWN":
        return "🔻 ขาย", now_time
    return None, None

# 5. ฟังก์ชันดึงข้อมูล
@st.cache_data(ttl=600)
def get_actionable_data():
    action_list = []
    for t in watch_list:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="60d")
            if not hist.empty:
                sig, sig_time = identify_hull_signal(hist)
                if sig: # ตรวจสอบว่ามีสัญญาณ (ซื้อ/ขาย) หรือไม่
                    curr_p = hist['Close'].iloc[-1]
                    prev_p = hist['Close'].iloc[-2]
                    action_list.append({
                        "หุ้น (Ticker)": t.replace('.BK', ''),
                        "ราคาปัจจุบัน": f"{curr_p:,.2f}",
                        "Chg%": ((curr_p - prev_p) / prev_p) * 100,
                        "Signal": sig, # จะมีลูกศรติดไปในข้อความนี้เสมอ
                        "เวลาแจ้งเตือน": sig_time
                    })
        except: continue
    return pd.DataFrame(action_list)

# 6. การแสดงผล
tz = pytz.timezone('Asia/Bangkok')
st.markdown(f'<div class="time-status">🕒 เวลาปัจจุบัน (BKK): {datetime.now(tz).strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
st.subheader("🛰️ Hull Suite Dashboard")

df_filtered = get_actionable_data()

if not df_filtered.empty:
    # ฟังก์ชันกำหนดสีตัวอักษรทั้งแถวตามสัญลักษณ์ที่ปรากฏใน Signal
    def style_entire_row(row):
        # เช็คจากตัวอักษรลูกศรในคอลัมน์ Signal
        if "🚀" in row['Signal']:
            color = '#10b981' # สีเขียว
        else:
            color = '#ef4444' # สีแดง
        return [f'color: {color}; font-weight: normal;'] * len(row)

    st.dataframe(
        df_filtered.style.apply(style_entire_row, axis=1).format({"Chg%": "{:+.2f}%"}),
        column_config={
            "หุ้น (Ticker)": st.column_config.TextColumn("Ticker", width=70),
            "ราคาปัจจุบัน": st.column_config.TextColumn("ราคา", width=60),
            "Chg%": st.column_config.NumberColumn("%", width=50),
            "Signal": st.column_config.TextColumn("Signal", width=70),
            "เวลาแจ้งเตือน": st.column_config.TextColumn("เวลา", width=75),
        },
        use_container_width=True,
        height=500,
        hide_index=True
    )
else:
    st.info("🔎 ยังไม่พบสัญญาณการเปลี่ยนสีของเส้น Hull (ซื้อ/ขาย) ในขณะนี้")

if st.button("🔄 สแกนตลาดใหม่", use_container_width=True):
    st.rerun()
