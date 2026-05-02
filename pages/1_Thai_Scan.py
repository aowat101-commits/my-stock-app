import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import pytz

# --- 1. ตั้งค่าหน้าจอและสไตล์ Loft แบบเดิม (Strictly Original) ---
st.set_page_config(page_title="Market Intelligence Dashboard", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 10px; border-radius: 6px;
        text-align: center; font-size: 13px; margin-bottom: 15px; border: 1px solid #334155;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 11px !important; }
    [data-testid="stDataFrame"] td { font-size: 11px !important; text-align: center !important; font-weight: normal !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันคำนวณ Technical (คงเดิม) ---
def get_hma(series, length=30):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

def calculate_wavetrend(df, ch_len=9, avg_len=12):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ta.ema(ap, length=ch_len)
    d = ta.ema(abs(ap - esa), length=ch_len)
    ci = (ap - esa) / (0.015 * d)
    tci = ta.ema(ci, length=avg_len)
    wt1 = tci
    wt2 = ta.sma(wt1, length=4)
    return wt1, wt2

# --- 3. ฟังก์ชันสแกนหา 10 ตัวล่าสุดที่เข้าเงื่อนไข ---
def get_last_signal(df, ticker):
    if len(df) < 60: return None
    tz = pytz.timezone('Asia/Bangkok')
    
    df['ema8'] = ta.ema(df['Close'], length=8)
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['hma'] = get_hma(df['Close'], 30)
    df['wt1'], df['wt2'] = calculate_wavetrend(df, 9, 12)
    df['vma5'] = df['Volume'].rolling(window=5).mean()
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 🚩 เงื่อนไข: Value > 10M และ Vol > 1.5x
    daily_value = curr['Close'] * curr['Volume']
    vol_confirm = (daily_value > 10_000_000) and (curr['Volume'] > curr['vma5'] * 1.5)
    
    # เช็คสัญญาณจุดตัด (ย้อนหลัง 1-3 แท่งเพื่อให้เจอ 10 ตัว)
    hma_up = curr['hma'] > prev['hma']
    wt_cross_up = (prev['wt1'] < prev['wt2']) and (curr['wt1'] > curr['wt2'])
    above_ema = (curr['Close'] > curr['ema8']) and (curr['Close'] > curr['ema20'])

    # คำนวณ R:R
    target = curr['Close'] * 1.05
    stop_loss = curr['ema20']
    risk = curr['Close'] - stop_loss
    rr_ratio = (target - curr['Close']) / risk if risk > 0 else 0

    if hma_up and wt_cross_up and above_ema and vol_confirm:
        actual_time = df.index[-1].astimezone(tz)
        return {
            "Ticker": ticker.replace('.BK', ''),
            "ราคา": curr['Close'],
            "Signal": "🚀 ซื้อ",
            "R:R": round(rr_ratio, 2),
            "Vol(M)": round(daily_value / 1_000_000, 1),
            "เวลา": actual_time.strftime("%H:%M:%S"),
            "วันที่": actual_time.strftime("%d/%m/%y"),
            "raw_time": actual_time,
            "hist": df.tail(30)
        }
    return None

# --- 4. การจัดการรายชื่อหุ้น (Dynamic List) ---
# ในส่วนนี้คุณสามารถใส่รายชื่อ SET100 + sSET/MAI ทั้งหมดที่คุณมีได้เลยครับ
full_scan_list = [
    'ADVANC.BK', 'CPALL.BK', 'AOT.BK', 'WHA.BK', 'DELTA.BK', 'PTT.BK', 'BDMS.BK', 'GULF.BK',
    'AU.BK', 'SABINA.BK', 'SPA.BK', 'TKN.BK', 'XO.BK', 'DITTO.BK', 'BE8.BK', 'BBIK.BK', 'MASTER.BK'
] # ตัวอย่างบางส่วน

st.subheader("🛰️ Market Intelligence: Top 10 Active Signals")

@st.fragment(run_every="10m")
def dashboard_runtime():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Last Update: {datetime.now(tz).strftime("%H:%M:%S")} | SET100 + sSET + MAI</div>', unsafe_allow_html=True)
    
    results = []
    for t in full_scan_list:
        try:
            hist = yf.Ticker(t).history(period="10d", interval="1h")
            res = get_last_signal(hist, t)
            if res: results.append(res)
        except: continue
    
    if results:
        # คัดเฉพาะ 10 ตัวล่าสุด
        df = pd.DataFrame(results).sort_values(by="raw_time", ascending=False).head(10)
        
        st.dataframe(
            df.drop(columns=['raw_time', 'hist']).style.apply(lambda x: ["color: #10b981"] * len(x), axis=1)
            .format({"ราคา": "{:,.2f}"}),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=70),
                "ราคา": st.column_config.NumberColumn("ราคา", width=65, format="%.2f"),
                "Signal": st.column_config.TextColumn("Signal", width=75),
                "R:R": st.column_config.NumberColumn("R:R", width=50),
                "Vol(M)": st.column_config.NumberColumn("Vol(M)", width=60),
            },
            use_container_width=True, hide_index=True
        )

        # 🚩 กราฟ Interactive (Interactive Chart)
        selected_ticker = st.selectbox("🔍 เลือกหุ้นเพื่อดูกราฟ Interactive", df['Ticker'])
        selected_row = df[df['Ticker'] == selected_ticker].iloc[0]
        
        fig = go.Figure(data=[go.Candlestick(x=selected_row['hist'].index,
                                open=selected_row['hist']['Open'], high=selected_row['hist']['High'],
                                low=selected_row['hist']['Low'], close=selected_row['hist']['Close'])])
        fig.update_layout(height=400, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

dashboard_runtime()
