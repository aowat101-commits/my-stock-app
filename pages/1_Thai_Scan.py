import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอแบบ Wide Mode
st.set_page_config(layout="wide")

# CSS ดั้งเดิมของวันที่ 1 (อ้างอิงจากรูป 1777693897312.jpg)
st.markdown("""
    <style>
    [data-testid="stHeader"], header, .stAppHeader, [data-testid="stSidebar"], .stSidebar {
        display: none !important;
    }
    
    .main .block-container {
        padding-top: 2rem !important;
    }

    /* กรอบเส้นบางด้านบนสุด */
    .top-outline {
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        height: 45px;
        margin-bottom: 20px;
    }

    /* ปุ่ม Force Refresh ชิดซ้าย */
    .stButton>button {
        background-color: transparent !important;
        color: #3b82f6 !important;
        border: none !important;
        padding: 0 !important;
        font-size: 14px !important;
        text-align: left !important;
    }

    /* แถบสถานะสีน้ำเงินเข้มตัวหนังสือสีเหลือง */
    .status-bar {
        background-color: #1e293b;
        color: #fbbf24;
        text-align: center;
        padding: 12px;
        border-radius: 6px;
        font-size: 13px;
        margin-top: 20px;
        margin-bottom: 20px;
    }

    /* สไตล์ตารางแบบคลีนดั้งเดิม */
    div[data-testid="stTable"] {
        margin-top: 10px;
    }
    th {
        color: #94a3b8 !important;
        font-weight: normal !important;
        border-bottom: 1px solid #f1f5f9 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- โครงสร้างหน้าจอวันที่ 1 ---

st.markdown('<div class="top-outline"></div>', unsafe_allow_html=True)

if st.button("🔄 Force Refresh Now"):
    st.rerun()

tz_th = pytz.timezone('Asia/Bangkok')
now_th = datetime.now(tz_th)
st.markdown(f'<div class="status-bar">🇹🇭 Thai Time: {now_th.strftime("%H:%M:%S")} | ระบบกำลังสแกนทุกๆ 5 นาทีอัตโนมัติ</div>', unsafe_allow_html=True)

if st.button("⬅️ Back to Home"):
    st.switch_page("Home.py")

# รายชื่อหุ้น (SET100 เดิม)
tickers = ["DELTA.BK", "ADVANC.BK", "PTT.BK", "CPALL.BK", "AOT.BK", "SCB.BK", "KBANK.BK", "GULF.BK"]

def get_original_scan():
    results = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1mo", interval="1d", progress=False)
            if df.empty: continue
            
            # การคำนวณเดิม (RSI 14)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            p_chg = ((curr['Close'] - prev['Close']) / prev['Close']) * 100
            
            # สัญญาณแบบเดิม
            rsi_val = curr['RSI']
            if rsi_val < 30: signal = "🟢 BUY (Oversold)"
            elif rsi_val > 70: signal = "🔴 SELL (Overbought)"
            else: signal = "HOLD"

            results.append({
                "Ticker": ticker.replace(".BK", ""),
                "Price": f"{curr['Close']:,.2f}",
                "% Chg": f"{p_chg:+.2f}%",
                "Signal": signal,
                "เวลาไทย": now_th.strftime("%H:%M:%S"),
                "วันที่": now_th.strftime("%d/%m")
            })
        except: continue
    return pd.DataFrame(results)

# แสดงตาราง
with st.spinner(""):
    df = get_original_scan()
    if not df.empty:
        st.table(df)
