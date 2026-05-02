import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# 1. ตั้งค่าหน้าจอ (กลับมาใช้แบบเดิม)
st.set_page_config(layout="wide", page_title="Thai Scan")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@800&family=Kanit:wght@900&family=Dancing+Script:wght@700&display=swap');

    /* ซ่อน Header และ Sidebar */
    [data-testid="stHeader"], header, .stAppHeader, [data-testid="stSidebar"], .stSidebar {
        display: none !important;
    }
    
    .main .block-container {
        max-width: 900px !important; 
        margin: 0 auto !important;
        padding-top: 1rem !important;
    }

    .main { background-color: #0f172a; }
    
    /* สไตล์บรรทัดหัวข้อเดิม */
    .line-1 { font-family: 'Montserrat', sans-serif; color: #ffffff !important; text-align: center; font-size: 32px; margin-top: 20px; letter-spacing: 5px; font-weight: 800; }
    .line-2 { font-family: 'Kanit', sans-serif !important; color: #fbbf24 !important; text-align: center; font-size: 60px; font-weight: 900; line-height: 1.1; }

    /* ปุ่มกดสีเทาเข้มขนาดใหญ่แบบเดิม */
    .stButton>button {
        width: 100% !important;
        border-radius: 20px !important;
        height: 4.5em !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 2px solid #475569 !important;
        font-size: 26px !important; 
        font-weight: 900 !important;
        margin-top: 20px;
    }
    
    /* สไตล์ตารางให้เข้ากับโหมดมืด */
    div[data-testid="stDataFrame"] { background-color: #1e293b; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# ส่วนหัวหน้าสแกน
st.markdown('<p class="line-1">STRATEGY</p>', unsafe_allow_html=True)
st.markdown('<p class="line-2">GUARDIAN SCAN</p>', unsafe_allow_html=True)

# รายชื่อหุ้น SET100 หลักๆ
tickers = ["DELTA.BK", "ADVANC.BK", "PTT.BK", "CPALL.BK", "AOT.BK", "SCB.BK", "KBANK.BK", "GULF.BK", "KTB.BK"]

def guardian_scan():
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

            # เงื่อนไข Buy Signal ตามสูตรเป๊ะๆ
            wt_cross = (prev['wt1'] < prev['wt2']) and (curr['wt1'] >= curr['wt2'])
            wt_low = curr['wt1'] < -53
            trend_ok = (curr['Close'] > curr['ema8']) and (curr['Close'] > curr['ema20'])
            hull_green = curr['hull'] > prev['hull']
            vol_ok = curr['Volume'] > (curr['vma5'] * 1.5)

            signal = "Wait"
            if wt_cross and wt_low and trend_ok and hull_green and vol_ok:
                signal = "🔥 BUY"
            elif curr['Close'] < curr['ema20'] or curr['hull'] < prev['hull']:
                signal = "⚠️ EXIT"

            results.append({
                "หุ้น": ticker.replace(".BK", ""),
                "ราคา": f"{curr['Close']:.2f}",
                "WT": f"{curr['wt1']:.1f}",
                "Vol": f"{curr['Volume']/curr['vma5']:.1f}x",
                "สัญญาณ": signal
            })
        except: continue
    return pd.DataFrame(results)

# ปุ่มกดเดิมๆ ที่คุ้นเคย
if st.button("🚀 เริ่มสแกนหุ้น"):
    with st.spinner("Guardian is checking..."):
        data = guardian_scan()
        if not data.empty:
            st.dataframe(data, use_container_width=True)
        else:
            st.write("ไม่พบข้อมูล")

if st.button("⬅️ กลับหน้าหลัก"):
    st.switch_page("Home.py")
