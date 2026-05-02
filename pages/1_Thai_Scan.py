import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ (Wide Mode เพื่อให้ตารางดูง่ายเหมือนในรูป)
st.set_page_config(layout="wide", page_title="Thai Market Monitor")

# CSS ปรับแต่งหน้าตาให้เหมือนในรูปตัวอย่าง
st.markdown("""
    <style>
    [data-testid="stHeader"], header, .stAppHeader, [data-testid="stSidebar"], .stSidebar {
        display: none !important;
    }
    .main { background-color: #ffffff; }
    
    /* ปุ่ม Force Refresh */
    .stButton>button {
        width: 100% !important;
        background-color: #ffffff !important;
        color: #1e40af !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        height: 35px !important;
        font-size: 14px !important;
    }

    /* แถบสถานะสีดำ/น้ำเงินเข้มด้านบน */
    .status-bar {
        background-color: #1e293b;
        color: #fbbf24;
        text-align: center;
        padding: 8px;
        border-radius: 5px;
        font-size: 14px;
        font-weight: bold;
        margin-bottom: 20px;
    }

    /* ปรับแต่งตาราง */
    div[data-testid="stTable"] {
        font-size: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ส่วนควบคุมด้านบน ---
if st.button("🔄 Force Refresh Now"):
    st.rerun()

tz_th = pytz.timezone('Asia/Bangkok')
now_th = datetime.now(tz_th).strftime("%H:%M:%S")
st.markdown(f'<div class="status-bar">🇹🇭 Thai Time: {now_th} | ระบบกำลังสแกนทุกๆ 5 นาทีอัตโนมัติ</div>', unsafe_allow_html=True)

# รายชื่อหุ้นไทย (คุณมิลค์เพิ่มเพิ่มลดได้ที่นี่ครับ)
tickers = ["DELTA.BK", "ADVANC.BK", "PTT.BK", "CPALL.BK", "AOT.BK", "SCB.BK", "KBANK.BK", "GULF.BK", "KTB.BK", "BBL.BK"]

def guardian_logic():
    results = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue

            # คำนวณสูตร The Guardian Swing
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
            df['vma5'] = ta.sma(df['Volume'], length=5)

            curr = df.iloc[-1]
            prev = df.iloc[-2]

            # เงื่อนไข Signal
            wt_buy = (prev['wt1'] < prev['wt2']) and (curr['wt1'] >= curr['wt2']) and (curr['wt1'] < -53)
            trend_ok = (curr['Close'] > curr['ema8']) and (curr['Close'] > curr['ema20'])
            hull_ok = curr['hull'] > prev['hull']
            vol_ok = curr['Volume'] > (curr['vma5'] * 1.5)

            signal = "SELL" # Default
            if wt_buy and trend_ok and hull_ok and vol_ok:
                signal = "🚀 BUY"
            elif curr['Close'] < curr['ema20'] or curr['hull'] < prev['hull']:
                signal = "▼ SELL"
            else:
                signal = "HOLD"

            # คำนวณ % Change
            p_change = ((curr['Close'] - prev['Close']) / prev['Close']) * 100

            results.append({
                "Ticker": ticker.replace(".BK", ""),
                "Price": f"{curr['Close']:,.2f}",
                "% Chg": f"{p_change:+.22f}%",
                "Signal": signal,
                "เวลาไทย": now_th,
                "วันที่": datetime.now(tz_th).strftime("%d/%m")
            })
        except: continue
    return pd.DataFrame(results)

# แสดงผลตาราง
with st.spinner("Scanning..."):
    df_final = guardian_logic()
    if not df_final.empty:
        # ฟังก์ชันแต่งสีตัวหนังสือให้เหมือนในรูป
        def color_row(val):
            if "BUY" in str(val): return 'color: #10b981' # เขียว
            if "SELL" in str(val): return 'color: #ef4444' # แดง
            return 'color: #6b7280' # เทา

        st.table(df_final)

if st.button("⬅️ Back"):
    st.switch_page("Home.py")
