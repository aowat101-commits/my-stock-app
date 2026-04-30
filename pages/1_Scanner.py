import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="Hull Suite Signal", layout="wide")

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
    [data-testid="stDataFrame"] td { font-size: 11px !important; text-align: center !important; border-bottom: 1px solid #1e293b !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นที่ติดตาม (อิงตาม User Summary)
watch_list = [
    'IONQ', 'IREN', 'ONDS', 'SMX', 'DELTA.BK', 'GULF.BK', 'ADVANC.BK', 
    'PTT.BK', 'KBANK.BK', 'SCB.BK', 'CPALL.BK', 'AOT.BK', 'PTTEP.BK', 'HANA.BK'
]

# 3. ฟังก์ชันคำนวณ Hull Moving Average (HMA)
def get_hma(series, length):
    # สูตร HMA: WMA(2*WMA(n/2) - WMA(n)), sqrt(n))
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

    half_length = int(length / 2)
    sqrt_length = int(np.sqrt(length))
    
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    hma = wma(raw_hma, sqrt_length)
    return hma

# 4. ฟังก์ชันวิเคราะห์สัญญาณ (ซื้อเมื่อแดง->เขียว / ขายเมื่อเขียว->แดง)
def identify_hull_signal(df):
    if len(df) < 2: return None, None
    
    # คำนวณ HMA ตามค่าในรูปภาพ (Length=30)
    df['hma'] = get_hma(df['Close'], 30)
    
    curr_hma = df['hma'].iloc[-1]
    prev_hma = df['hma'].iloc[-2]
    prev2_hma = df['hma'].iloc[-3] if len(df) > 2 else prev_hma

    # เช็คแนวโน้ม (เขียวคือขึ้น, แดงคือลง)
    curr_trend = "เขียว" if curr_hma > prev_hma else "แดง"
    prev_trend = "เขียว" if prev_hma > prev2_hma else "แดง"

    # แจ้งเตือนเมื่อเปลี่ยนสี
    if prev_trend == "แดง" and curr_trend == "เขียว":
        return "🚀 ซื้อ (แดง ➡️ เขียว)", datetime.now().strftime("%H:%M:%S")
    elif prev_trend == "เขียว" and curr_trend == "แดง":
        return "🔻 ขาย (เขียว ➡️ แดง)", datetime.now().strftime("%H:%M:%S")
    
    return None, None

# 5. ฟังก์ชันดึงข้อมูลและกรอง
@st.cache_data(ttl=600) # อัปเดตทุก 10 นาทีเพื่อความไวของสัญญาณ
def get_actionable_data():
    action_list = []
    for t in watch_list:
        try:
            stock = yf.Ticker(t)
            # ดึงข้อมูลย้อนหลัง 60 วันเพื่อให้เพียงพอต่อการคำนวณ HMA 30
            hist = stock.history(period="60d") 
            if not hist.empty:
                sig, sig_time = identify_hull_signal(hist)
                
                if sig:
                    curr_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    diff_pct = ((curr_price - prev_price) / prev_price) * 100
                    
                    action_list.append({
                        "หุ้น (Ticker)": t.replace('.BK', ''),
                        "ราคาปัจจุบัน": f"{curr_price:,.2f}",
                        "Chg%": diff_pct,
                        "สัญญาณ (Signal)": sig,
                        "เวลาแจ้งเตือน": sig_time
                    })
        except: continue
    return pd.DataFrame(action_list)

# 6. การแสดงผล
st.markdown(f'<div class="time-status">🕒 Hull Suite Monitor: {datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
st.subheader("🛰️ Hull Suite Intelligence Dashboard")

df_filtered = get_actionable_data()

if not df_filtered.empty:
    def style_rows(row):
        # สีเขียวสำหรับซื้อ สีแดงสำหรับขาย
        s_color = '#10b981' if "ซื้อ" in row['สัญญาณ (Signal)'] else '#ef4444'
        return ['', '', '', f'color: {s_color}; font-weight: bold;', 'color: #888888;']

    st.dataframe(
        df_filtered.style.apply(style_rows, axis=1)
                   .format({"Chg%": "{:+.2f}%"}),
        column_config={
            "หุ้น (Ticker)": st.column_config.TextColumn("Ticker", width=70),
            "ราคาปัจจุบัน": st.column_config.TextColumn("ราคา", width=60),
            "Chg%": st.column_config.NumberColumn("%", width=50),
            "สัญญาณ (Signal)": st.column_config.TextColumn("Signal", width=100),
            "เวลาแจ้งเตือน": st.column_config.TextColumn("เวลา", width=65),
        },
        use_container_width=True,
        height=500,
        hide_index=True
    )
else:
    st.info("🔎 ยังไม่พบการเปลี่ยนสีของ Hull Suite (แดง ↔️ เขียว) ในขณะนี้")

if st.button("🔄 สแกนสัญญาณเดี๋ยวนี้", use_container_width=True):
    st.rerun()
