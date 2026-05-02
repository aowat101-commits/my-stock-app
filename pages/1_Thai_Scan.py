import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import pytz

# --- 1. ตั้งค่าหน้าจอและ CSS สำหรับ Mobile Floating Popup ---
st.set_page_config(page_title="Guardian Alpha Mobile", layout="wide")

st.markdown("""
    <style>
    /* สไตล์ Loft และการปรับแต่งตารางสำหรับมือถือ */
    .time-status { background-color: #1e293b; color: #10b981; padding: 10px; border-radius: 6px; text-align: center; font-size: 12px; }
    
    /* บังคับให้ตารางอ่านง่ายขึ้นบนจอเล็ก */
    [data-testid="stDataFrame"] td { font-size: 12px !important; }

    /* สร้าง Effect เหมือนป๊อปอัพลอยตัว (ใช้ Expander หรือ Container จำลอง) */
    .floating-card {
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 15px;
        background-color: #0f172a;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันคำนวณ (EMA, HMA, WT, Vol 10M+) ---
def get_guardian_logic(df, ticker):
    if len(df) < 60: return None
    tz = pytz.timezone('Asia/Bangkok')
    
    # คำนวณ Indicators
    df['ema8'] = ta.ema(df['Close'], length=8)
    df['ema20'] = ta.ema(df['Close'], length=20)
    # HMA 30 ตามต้นฉบับ
    weights = np.arange(1, 31)
    df['hma'] = df['Close'].rolling(30).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True) 
    
    # WaveTrend 9, 12
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ta.ema(ap, length=9)
    d = ta.ema(abs(ap - esa), length=9)
    ci = (ap - esa) / (0.015 * d)
    wt1 = ta.ema(ci, length=12)
    wt2 = ta.sma(wt1, length=4)
    
    # เช็คย้อนหลัง 10 วัน (ประมาณ 40 แท่งใน TF 1H)
    for i in range(1, 41):
        curr, prev = df.iloc[-i], df.iloc[-(i+1)]
        daily_val = curr['Close'] * curr['Volume']
        
        # เงื่อนไข: Vol > 10M และสอดคล้องกับ EMA/HMA/WT
        if (daily_val > 10_000_000 and curr['Close'] > curr['ema8'] and 
            curr['wt1'] > wt2.iloc[-i] and curr['hma'] > prev['hma']):
            
            # คำนยณ R:R (Target 5% / Stop EMA 20)
            rr = (curr['Close'] * 0.05) / (curr['Close'] - curr['ema20']) if curr['Close'] > curr['ema20'] else 0
            
            return {
                "Ticker": ticker.replace('.BK', ''),
                "Price": curr['Close'],
                "Signal": "🚀 BUY",
                "RR": round(rr, 2),
                "VolM": round(daily_val / 1_000_000, 1),
                "Time": curr.name.astimezone(tz).strftime("%d/%m %H:%M"),
                "hist": df.tail(48)
            }
    return None

# --- 3. ส่วนการทำงานหน้าจอ (Layout สำหรับมือถือ) ---
st.subheader("🛰️ Guardian Intelligence: Mobile")

if st.button("🔍 SCAN NOW (SET100 + sSET/MAI)", use_container_width=True):
    st.rerun()

# รายชื่อหุ้น (ชุดเดิมที่คุณต้องการสแกน)
full_list = ['ADVANC.BK', 'CPALL.BK', 'WHA.BK', 'AU.BK', 'SABINA.BK', 'SPA.BK', 'TKN.BK', 'XO.BK'] 

results = []
bar = st.progress(0)
for i, t in enumerate(full_list):
    try:
        hist = yf.Ticker(t).history(period="15d", interval="1h")
        res = get_guardian_logic(hist, t)
        if res: results.append(res)
    except: continue
    bar.progress((i + 1) / len(full_list))
bar.empty()

if results:
    df = pd.DataFrame(results).sort_values(by="Time", ascending=False).head(10)
    
    # แสดงตารางแบบย่อสำหรับมือถือ
    st.dataframe(
        df[['Ticker', 'Price', 'Signal', 'RR', 'VolM', 'Time']],
        column_config={
            "RR": st.column_config.NumberColumn("R:R", format="%.1f"),
            "VolM": "Vol(M)"
        },
        use_container_width=True, hide_index=True
    )

    # --- 🚩 ระบบป๊อปอัพลอยตัว (Floating Popup Simulation) ---
    st.write("---")
    selected = st.selectbox("🎯 แตะเลือกหุ้นเพื่อเปิดกราฟลอยตัว (Full-Screen Pop)", df['Ticker'])
    
    with st.container():
        st.markdown('<div class="floating-card">', unsafe_allow_html=True)
        row = df[df['Ticker'] == selected].iloc[0]
        
        # กราฟ Interactive ที่เลื่อนดูได้ (เหมาะกับนิ้วมือ)
        fig = go.Figure(data=[go.Candlestick(
            x=row['hist'].index, open=row['hist']['Open'], 
            high=row['hist']['High'], low=row['hist']['Low'], close=row['hist']['Close']
        )])
        fig.update_layout(
            height=350, template="plotly_dark", 
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_rangeslider_visible=False # ปิด slider เพื่อเพิ่มพื้นที่บนมือถือ
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # ข้อมูลสรุปท้ายป๊อปอัพ
        c1, c2 = st.columns(2)
        c1.metric("Risk:Reward", f"1 : {row['RR']}")
        c2.metric("Volume (24h)", f"{row['VolM']}M")
        
        st.markdown('</div>', unsafe_allow_html=True)
