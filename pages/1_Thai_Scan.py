import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# 1. ตั้งค่าหน้าจอ
st.set_page_config(layout="wide", page_title="The Guardian Swing")

st.markdown("""
    <style>
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    .main { background-color: #0f172a; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ The Guardian Swing Scanner")

# รายชื่อหุ้น (เน้นตัวหลักๆ ก่อนเพื่อทดสอบ)
tickers = ["DELTA.BK", "ADVANC.BK", "PTT.BK", "CPALL.BK", "AOT.BK", "SCB.BK", "KBANK.BK"]

def scan_logic():
    results = []
    for ticker in tickers:
        try:
            # ดึงข้อมูล
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue

            # --- คำนวณตามสูตรคุณมิลค์ ---
            df['ema8'] = ta.ema(df['Close'], length=8)
            df['ema20'] = ta.ema(df['Close'], length=20)
            df['hull'] = ta.hma(df['Close'], length=55)
            
            # WaveTrend
            ap = (df['High'] + df['Low'] + df['Close']) / 3
            esa = ta.ema(ap, length=9)
            d = ta.ema(abs(ap - esa), length=9)
            ci = (ap - esa) / (0.015 * d)
            df['wt1'] = ta.ema(ci, length=12)
            df['wt2'] = ta.sma(df['wt1'], length=4)
            
            # Vol MA 5
            df['vma5'] = ta.sma(df['Volume'], length=5)

            # ค่าล่าสุด
            curr = df.iloc[-1]
            prev = df.iloc[-2]

            # เงื่อนไข Buy Alert
            wt_cross = (prev['wt1'] < prev['wt2']) and (curr['wt1'] >= curr['wt2'])
            wt_low = curr['wt1'] < -53
            trend_ok = (curr['Close'] > curr['ema8']) and (curr['Close'] > curr['ema20'])
            hull_up = curr['hull'] > prev['hull']
            vol_ok = curr['Volume'] > (curr['vma5'] * 1.5)

            signal = "Wait"
            if wt_cross and wt_low and trend_ok and hull_up and vol_ok:
                signal = "🔥 BUY: Strong Vol"
            elif curr['Close'] < curr['ema20'] or curr['hull'] < prev['hull']:
                signal = "⚠️ EXIT"

            results.append({
                "Ticker": ticker.replace(".BK", ""),
                "Price": round(float(curr['Close']), 2),
                "WT": round(float(curr['wt1']), 1),
                "Vol Ratio": round(float(curr['Volume']/curr['vma5']), 1),
                "Signal": signal
            })
        except:
            continue
    return pd.DataFrame(results)

if st.button("🔍 Start Scanning"):
    with st.spinner("Checking The Guardian Swing Strategy..."):
        data = scan_logic()
        if not data.empty:
            st.dataframe(data, use_container_width=True)
        else:
            st.write("No data found.")

if st.button("⬅️ Back"):
    st.switch_page("Home.py")
