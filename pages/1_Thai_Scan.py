import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# ตั้งค่าหน้าจอแบบ Wide Mode ที่คุณมิลค์ใช้เมื่อวาน
st.set_page_config(layout="wide")

st.markdown("""
    <style>
    /* ซ่อน Header และ Sidebar ทั้งหมดตามสไตล์ที่คุณมิลค์ชอบ */
    [data-testid="stHeader"], header, .stAppHeader, [data-testid="stSidebar"], .stSidebar {
        display: none !important;
    }
    
    .main .block-container {
        padding-top: 2rem !important;
    }

    /* ปุ่ม Force Refresh Now ชิดซ้าย ไม่หนา */
    .stButton>button {
        background-color: transparent !important;
        color: #3b82f6 !important;
        border: none !important;
        padding: 0 !important;
        font-size: 16px !important;
        text-align: left !important;
    }

    /* แถบสถานะสีน้ำเงินเข้มตัวหนังสือสีเหลืองกึ่งกลาง */
    .status-bar {
        background-color: #1e293b;
        color: #fbbf24;
        text-align: center;
        padding: 12px;
        border-radius: 4px;
        font-size: 14px;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 1. ปุ่ม Force Refresh ชิดซ้าย
if st.button("🔄 Force Refresh Now"):
    st.rerun()

# 2. แถบแสดงเวลาไทย
tz_th = pytz.timezone('Asia/Bangkok')
now_th = datetime.now(tz_th)
st.markdown(f'<div class="status-bar">🇹🇭 Thai Time: {now_th.strftime("%H:%M:%S")} | ระบบกำลังสแกนทุกๆ 5 นาทีอัตโนมัติ</div>', unsafe_allow_html=True)

# 3. ปุ่ม Back to Home
if st.button("⬅️ Back to Home"):
    st.switch_page("Home.py")

# 4. รายชื่อหุ้น SET100 ดั้งเดิม (อ้างอิงจาก Dashboard ของคุณมิลค์)
tickers = ["DELTA.BK", "ADVANC.BK", "PTT.BK", "CPALL.BK", "AOT.BK", "SCB.BK", "KBANK.BK", "GULF.BK"]

def original_scan():
    results = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1mo", interval="1d", progress=False)
            if df.empty: continue
            
            # คำนวณ RSI 14 แบบดั้งเดิมที่ใช้เมื่อวาน
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            p_chg = ((curr['Close'] - prev['Close']) / prev['Close']) * 100
            
            # สัญญาณ BUY/SELL แบบดั้งเดิม (RSI 30/70)
            rsi_val = curr['RSI']
            if rsi_val < 30: signal = "🚀 BUY"
            elif rsi_val > 70: signal = "▼ SELL"
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

# 5. แสดงตารางแบบคลีน
with st.spinner(""):
    df_results = original_scan()
    if not df_results.empty:
        st.table(df_results)
