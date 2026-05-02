import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# 1. ตั้งค่าหน้าจอแบบกึ่งกลาง PC (เหมือนหน้าแรกที่คุณชอบ)
st.set_page_config(layout="wide", page_title="Thai Scan")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@800&family=Kanit:wght@900&family=Dancing+Script:wght@700&display=swap');

    /* ซ่อนส่วนเกินเพื่อให้ดูคลีนที่สุด */
    [data-testid="stHeader"], header, .stAppHeader, [data-testid="stSidebar"], .stSidebar {
        display: none !important;
    }
    
    /* บังคับเนื้อหาให้อยู่ตรงกลางเหมือนหน้า Home */
    .main .block-container {
        max-width: 800px !important; 
        margin: 0 auto !important;
        padding-top: 2rem !important;
    }

    .main { background-color: #0f172a; }
    
    /* หัวข้อใช้สไตล์เดิมเป๊ะ */
    .line-title {
        font-family: 'Kanit', sans-serif;
        color: #fbbf24 !important;
        text-align: center;
        font-size: clamp(45px, 12vw, 85px);
        font-weight: 900;
        margin-bottom: 30px;
    }

    /* ปุ่มกดสีเทาเข้ม Spencer Fit สไตล์เดิม */
    .stButton>button {
        width: 100% !important;
        border-radius: 20px !important;
        height: 4.8em !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 2px solid #475569 !important;
        font-size: 28px !important; 
        font-weight: 900 !important;
        margin-bottom: 20px !important;
    }
    
    /* ปรับแต่งตารางให้ดูง่ายในมือถือ */
    div[data-testid="stDataFrame"] {
        background-color: #1e293b;
        border-radius: 15px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ส่วนแสดงผลหน้าตาเดิม ---
st.markdown('<p class="line-title">THAI SCAN</p>', unsafe_allow_html=True)

# รายชื่อหุ้น (SET100)
tickers = ["DELTA.BK", "ADVANC.BK", "PTT.BK", "CPALL.BK", "AOT.BK", "SCB.BK", "KBANK.BK", "GULF.BK", "KTB.BK"]

def guardian_logic():
    results = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue

            # สูตร The Guardian Swing
            df['ema8'] = ta.ema(df['Close'], length=8)
            df['ema20'] = ta.ema(df['Close'], length=20)
            df['hull'] = ta.hma(df['Close'], length=55)
            
            # WaveTrend (9, 12)
            ap = (df['High'] + df['Low'] + df['Close']) / 3
            esa = ta.ema(ap, length=9)
            d = ta.ema(abs(ap - esa), length=9)
            ci = (ap - esa) / (0.015 * d)
            df['wt1'] = ta.ema(ci, length=12)
            df['wt2'] = ta.sma(df['wt1'], length=4)
            df['vma5'] = ta.sma(df['Volume'], length=5)

            curr = df.iloc[-1]
            prev = df.iloc[-2]

            # เช็คเงื่อนไขตามสูตร
            wt_buy = (prev['wt1'] < prev['wt2']) and (curr['wt1'] >= curr['wt2']) and (curr['wt1'] < -53)
            trend_buy = (curr['Close'] > curr['ema8']) and (curr['Close'] > curr['ema20'])
            hull_buy = curr['hull'] > prev['hull']
            vol_buy = curr['Volume'] > (curr['vma5'] * 1.5)

            signal = "-"
            if wt_buy and trend_buy and hull_buy and vol_buy:
                signal = "🔥 BUY"
            elif curr['Close'] < curr['ema20'] or curr['hull'] < prev['hull']:
                signal = "⚠️ EXIT"

            results.append({
                "STOCK": ticker.replace(".BK", ""),
                "PRICE": f"{curr['Close']:.2f}",
                "SIGNAL": signal
            })
        except: continue
    return pd.DataFrame(results)

# ปุ่มกดที่หน้าตาเหมือนเดิม
if st.button("🚀 เริ่มสแกนหุ้นไทย"):
    with st.spinner("กำลังสแกน..."):
        data = guardian_logic()
        if not data.empty:
            st.dataframe(data, use_container_width=True, hide_index=True)
        else:
            st.write("ไม่พบข้อมูล")

if st.button("⬅️ กลับหน้าหลัก"):
    st.switch_page("Home.py")
