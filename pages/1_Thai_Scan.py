import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import pytz

# --- 1. การตั้งค่าหน้าจอและสไตล์ Loft (คงเดิม) ---
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

# --- 2. ฟังก์ชันคำนวณ WaveTrend (WT_LB) และ R:R ---
def calculate_wavetrend(df, ch_len=9, avg_len=12):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ta.ema(ap, length=ch_len)
    d = ta.ema(abs(ap - esa), length=ch_len)
    ci = (ap - esa) / (0.015 * d)
    tci = ta.ema(ci, length=avg_len)
    wt1 = tci
    wt2 = ta.sma(wt1, length=4)
    return wt1, wt2

def get_hma(series, length=30): # ใช้ค่า 30 ตามที่คุณตั้งไว้เดิม
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# --- 3. ฟังก์ชันสแกนและคำนวณเงื่อนไขใหม่ ---
def get_guardian_signal(df, ticker):
    if len(df) < 35: return None
    tz = pytz.timezone('Asia/Bangkok')
    
    # คำนวณ Indicators
    df['ema8'] = ta.ema(df['Close'], length=8)
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['hma'] = get_hma(df['Close'], 30)
    df['wt1'], df['wt2'] = calculate_wavetrend(df, 9, 12)
    df['vma5'] = df['Volume'].rolling(window=5).mean()
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # เงื่อนไข Volume 10M+ และ RVOL 1.5x
    daily_val = curr['Close'] * curr['Volume']
    vol_confirm = (daily_val > 10_000_000) and (curr['Volume'] > curr['vma5'] * 1.5)
    
    # เงื่อนไขสัญญาณ (EMA/HMA/WT)
    wt_cross_up = (prev['wt1'] < prev['wt2']) and (curr['wt1'] > curr['wt2'])
    above_ema = (curr['Close'] > curr['ema8']) and (curr['Close'] > curr['ema20'])
    hma_up = curr['hma'] > df['hma'].shift(1).iloc[-1]

    # คำนวณ R:R (Target 5% / Stop Loss ที่ EMA 20)
    target = curr['Close'] * 1.05
    stop_loss = curr['ema20']
    risk = curr['Close'] - stop_loss
    rr_ratio = (target - curr['Close']) / risk if risk > 0 else 0

    actual_time = df.index[-1].astimezone(tz)
    
    return {
        "Ticker": ticker.replace('.BK', ''),
        "ราคา": curr['Close'],
        "Signal": "🚀 ซื้อ" if (wt_cross_up and above_ema and hma_up and vol_confirm) else "🔻 ขาย" if not above_ema else "WAIT",
        "R:R": f"{rr_ratio:.2f}",
        "Volume": f"{(daily_val/1_000_000):.1f}M",
        "เวลา": actual_time.strftime("%H:%M:%S"),
        "raw_time": actual_time,
        "hist": df.tail(24) # ส่งข้อมูลไปทำกราฟ Interactive
    }

# --- 4. ส่วน Dashboard (คงรูปแบบตารางเดิม) ---
st.subheader("🛰️ Market Intelligence: MAI Alpha Hunter")

# (รายชื่อหุ้น full_scan_list เดิมของคุณ)
full_scan_list = ['AU.BK', 'SABINA.BK', 'SPA.BK', 'TKN.BK', 'XO.BK', 'DITTO.BK', 'BE8.BK', 'WHA.BK'] # ตัวอย่าง

@st.fragment(run_every="10m")
def dashboard_runtime():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Last Update: {datetime.now(tz).strftime("%H:%M:%S")} | สแกนหุ้น mai (Value > 10M)</div>', unsafe_allow_html=True)
    
    results = []
    for t in full_scan_list:
        try:
            hist = yf.Ticker(t).history(period="10d", interval="1h")
            res = get_guardian_signal(hist, t)
            if res: results.append(res)
        except: continue

    if results:
        df_display = pd.DataFrame(results).sort_values(by="raw_time", ascending=False)
        
        # แสดงตารางหลัก (คงรูปแบบเดิม)
        st.dataframe(
            df_display.drop(columns=['raw_time', 'hist']).style.apply(lambda x: [f"color: {'#10b981' if 'ซื้อ' in str(x['Signal']) else '#ef4444' if 'ขาย' in str(x['Signal']) else '#94a3b8'}"] * len(x), axis=1)
            .format({"ราคา": "{:,.2f}"}),
            use_container_width=True, hide_index=True
        )

        # เพิ่มกราฟ Interactive ด้านล่างตารางเมื่อคลิกเลือกหุ้น
        selected_ticker = st.selectbox("🔍 เลือกหุ้นเพื่อดูรายละเอียดและกราฟ Interactive", df_display['Ticker'])
        selected_data = df_display[df_display['Ticker'] == selected_ticker].iloc[0]
        
        fig = go.Figure(data=[go.Candlestick(x=selected_data['hist'].index,
                                open=selected_data['hist']['Open'], high=selected_data['hist']['High'],
                                low=selected_data['hist']['Low'], close=selected_data['hist']['Close'])])
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
