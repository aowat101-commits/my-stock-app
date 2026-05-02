import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. ตั้งค่าสไตล์ Loft และ CSS สำหรับ Mobile Pop-up ---
st.set_page_config(page_title="Guardian Alpha Mobile", layout="wide")
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status { background-color: #1e293b; color: #10b981; padding: 10px; border-radius: 6px; text-align: center; font-size: 12px; margin-bottom: 15px; border: 1px solid #334155; }
    [data-testid="stDataFrame"] td { font-size: 12px !important; }
    .floating-popup { border: 1px solid #334155; border-radius: 12px; padding: 10px; background-color: #0f172a; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันคำนวณ Technical (HMA 30 + WT_LB + RR) ---
def calculate_all_metrics(df, ticker):
    if len(df) < 60: return None
    tz = pytz.timezone('Asia/Bangkok')
    
    # Technical Indicators
    df['ema8'] = ta.ema(df['Close'], length=8)
    df['ema20'] = ta.ema(df['Close'], length=20)
    # HMA 30
    weights = np.arange(1, 31)
    df['hma'] = df['Close'].rolling(30).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    
    # WaveTrend
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ta.ema(ap, length=9)
    d = ta.ema(abs(ap - esa), length=9)
    ci = (ap - esa) / (0.015 * d)
    df['wt1'] = ta.ema(ci, length=12)
    df['wt2'] = ta.sma(df['wt1'], length=4)
    df['vma5'] = df['Volume'].rolling(window=5).mean()

    # ตรวจสอบย้อนหลัง 10 วัน (ประมาณ 40-50 แท่งใน TF 1H) เพื่อหาจุดสัญญาณ
    found_signals = []
    for i in range(1, 50):
        curr = df.iloc[-i]
        prev = df.iloc[-(i+1)]
        
        val_m = (curr['Close'] * curr['Volume']) / 1_000_000
        # เงื่อนไข: Vol > 10M + EMA + HMA Up + WT Cross Up
        if (val_m > 10 and curr['Close'] > curr['ema8'] and 
            curr['wt1'] > curr['wt2'] and prev['wt1'] <= prev['wt2'] and 
            curr['hma'] > prev['hma']):
            
            target = curr['Close'] * 1.05
            risk = curr['Close'] - curr['ema20']
            rr = (target - curr['Close']) / risk if risk > 0 else 0
            
            found_signals.append({
                "Ticker": ticker.replace('.BK', ''),
                "ราคาที่ตัด": curr['Close'],
                "Signal": "🚀 ซื้อ",
                "R:R": round(rr, 2),
                "Vol(M)": round(val_m, 1),
                "เวลา": curr.name.astimezone(tz).strftime("%H:%M"),
                "วันที่": curr.name.astimezone(tz).strftime("%d/%y"),
                "raw_time": curr.name,
                "hist": df.tail(60)
            })
            break # เอาสัญญาณล่าสุดตัวเดียว
    return found_signals[0] if found_signals else None

# --- 3. ส่วนการแสดงผลและปุ่มสแกน ---
st.subheader("🛰️ Market Intelligence: Mobile Alpha")

if st.button("🔍 START SCAN (SET100 + sSET/MAI)", use_container_width=True):
    st.rerun()

# รายชื่อหุ้นสแกน (ตัวอย่างครอบคลุมกลุ่มที่คุณสนใจ)
full_list = ['ADVANC.BK', 'CPALL.BK', 'WHA.BK', 'DELTA.BK', 'AU.BK', 'SABINA.BK', 'SPA.BK', 'TKN.BK', 'XO.BK', 'BE8.BK', 'BBIK.BK', 'MASTER.BK']

@st.fragment(run_every="10m")
def mobile_runtime():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Last Update: {datetime.now(tz).strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
    
    results = []
    progress = st.progress(0, text="สแกนหาจังหวะย้อนหลัง 10 วัน...")
    
    for i, t in enumerate(full_list):
        try:
            hist = yf.Ticker(t).history(period="20d", interval="1h")
            res = calculate_all_metrics(hist, t)
            if res: results.append(res)
        except: continue
        progress.progress((i + 1) / len(full_list))
    progress.empty()

    if results:
        # แสดง 30 ตัวล่าสุดที่เข้าเงื่อนไข (เพื่อเป็นตัวอย่างตามคำขอ)
        df_display = pd.DataFrame(results).sort_values(by="raw_time", ascending=False).head(30)
        
        st.dataframe(
            df_display.drop(columns=['raw_time', 'hist']).style.apply(lambda x: ["color: #10b981"] * len(x), axis=1)
            .format({"ราคาที่ตัด": "{:,.2f}"}),
            use_container_width=True, hide_index=True
        )

        # --- 🚩 ป๊อปอัพลอยตัว (Mobile Popup Simulation) ---
        st.write("---")
        selected = st.selectbox("🎯 แตะเลือกหุ้นเพื่อเปิดกราฟลอยตัว (Full-Screen Pop)", df_display['Ticker'])
        
        with st.container():
            st.markdown('<div class="floating-popup">', unsafe_allow_html=True)
            row = df_display[df_display['Ticker'] == selected].iloc[0]
            
            fig = go.Figure(data=[go.Candlestick(
                x=row['hist'].index, open=row['hist']['Open'], 
                high=row['hist']['High'], low=row['hist']['Low'], close=row['hist']['Close']
            )])
            fig.update_layout(height=350, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            c1, c2, c3 = st.columns(3)
            c1.metric("R:R Ratio", row['R:R'])
            c2.metric("Value", f"{row['Vol(M)']}M")
            c3.metric("Entry Time", row['เวลา'])
            st.markdown('</div>', unsafe_allow_html=True)

mobile_runtime()
