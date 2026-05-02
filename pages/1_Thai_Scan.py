import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as os
from datetime import datetime, timedelta
import pytz

# --- 1. ฟังก์ชันคำนวณ WaveTrend (WT_LB) ---
def calculate_wavetrend(df, ch_len=9, avg_len=12):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ta.ema(ap, length=ch_len)
    d = ta.ema(abs(ap - esa), length=ch_len)
    ci = (ap - esa) / (0.015 * d)
    tci = ta.ema(ci, length=avg_len)
    wt1 = tci
    wt2 = ta.sma(wt1, length=4)
    return wt1, wt2

# --- 2. ฟังก์ชันคำนวณ HMA (Hull Suite) ---
def get_hma(series, length=55):
    return ta.hma(series, length=length)

# --- 3. ฟังก์ชันหลักในการสแกนและคำนวณ R:R ---
def scan_mai_hunter(ticker):
    try:
        stock = yf.Ticker(ticker)
        # ดึงข้อมูลย้อนหลังให้พอสำหรับคำนวณ HMA 55 และดูย้อนหลัง 48 ชม.
        df = stock.history(period="10d", interval="1h")
        if len(df) < 60: return None

        # คำนวณ Indicators
        df['ema8'] = ta.ema(df['Close'], length=8)
        df['ema20'] = ta.ema(df['Close'], length=20)
        df['hma'] = get_hma(df['Close'], 55)
        df['wt1'], df['wt2'] = calculate_wavetrend(df, 9, 12)
        df['vma5'] = df['Volume'].rolling(window=5).mean()
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # เงื่อนไข Volume 10M+ และ RVOL 1.5x
        daily_val = curr['Close'] * curr['Volume']
        vol_confirm = (daily_val > 10_000_000) and (curr['Volume'] > curr['vma5'] * 1.5)
        
        if not vol_confirm: return None

        # เช็คสัญญาณซื้อ (The Guardian Logic)
        wt_cross_up = (prev['wt1'] < prev['wt2']) and (curr['wt1'] > curr['wt2'])
        wt_low = curr['wt1'] < -53
        above_ema = (curr['Close'] > curr['ema8']) and (curr['Close'] > curr['ema20'])
        hull_green = curr['Close'] > curr['hma']

        status = "WAIT"
        rr_ratio = 0
        target = 0
        stop_loss = curr['ema20'] # ใช้ EMA 20 เป็นจุดคัด

        if wt_cross_up and wt_low and above_ema and hull_green:
            status = "🚀 BUY"
            # คำนวณ R:R (สมมติเป้ากำไรที่แนวต้านเดิม หรือ 3% จากจุดเข้า)
            target = curr['Close'] * 1.05 
            risk = curr['Close'] - stop_loss
            reward = target - curr['Close']
            rr_ratio = reward / risk if risk > 0 else 0

        return {
            "Ticker": ticker.replace('.BK', ''),
            "Price": curr['Close'],
            "Signal": status,
            "RR_Ratio": rr_ratio,
            "Target": target,
            "StopLoss": stop_loss,
            "Data": df.tail(48) # ข้อมูลย้อนหลัง 48 ชม. สำหรับกราฟ
        }
    except: return None

# --- 4. ส่วนแสดงผล Streamlit Dashboard ---
st.title("🛡️ The Guardian: MAI Alpha Hunter")

# จำลองรายชื่อหุ้น mai (ในโปรเจกต์จริงควรใช้ API ดึงรายชื่อทั้งหมด)
mai_list = ['AU.BK', 'SABINA.BK', 'SPA.BK', 'TKN.BK', 'XO.BK', 'DITTO.BK', 'BE8.BK'] 

results = []
for t in mai_list:
    res = scan_mai_hunter(t)
    if res: results.append(res)

if results:
    for item in results:
        with st.expander(f"{item['Ticker']} | Signal: {item['Signal']} | RR: {item['RR_Ratio']:.2f}"):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("Price", f"{item['Price']:.2f}")
                st.write(f"🎯 Target: {item['Target']:.2f}")
                st.write(f"🛑 Stop: {item['StopLoss']:.2f}")
                if item['RR_Ratio'] >= 2: st.success("💎 High Reward Ratio!")
            
            with col2:
                # กราฟ Interactive (Plotly)
                fig = os.Figure(data=[os.Candlestick(x=item['Data'].index,
                                        open=item['Data']['Open'], high=item['Data']['High'],
                                        low=item['Data']['Low'], close=item['Data']['Close'])])
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
