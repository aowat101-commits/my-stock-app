import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# 1. การตั้งค่าหน้าจอแบบดั้งเดิมที่คุณใช้
st.set_page_config(layout="wide")

# CSS ตัวเดิมเป๊ะๆ ที่คุณใช้ในวันที่ 1
st.markdown("""
    <style>
    [data-testid="stHeader"], header, .stAppHeader, [data-testid="stSidebar"], .stSidebar {
        display: none !important;
    }
    .main .block-container {
        padding-top: 1rem !important;
    }
    .refresh-box {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        margin-bottom: 10px;
    }
    .stButton>button {
        background-color: transparent !important;
        color: #3b82f6 !important;
        border: none !important;
        font-size: 15px !important;
    }
    .status-bar {
        background-color: #1e293b;
        color: #fbbf24;
        text-align: center;
        padding: 10px;
        border-radius: 4px;
        font-size: 13px;
        margin-bottom: 15px;
    }
    /* สไตล์ตารางดั้งเดิม */
    div[data-testid="stTable"] th {
        background-color: #f8fafc !important;
        color: #64748b !important;
        font-size: 13px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ส่วนบนสุด: ปุ่ม Refresh ในกรอบ ---
st.markdown('<div class="refresh-box">', unsafe_allow_html=True)
if st.button("🔄 Force Refresh Now"):
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- แถบเวลา ---
tz_th = pytz.timezone('Asia/Bangkok')
now_th = datetime.now(tz_th)
st.markdown(f'<div class="status-bar">🇹🇭 Thai Time: {now_th.strftime("%H:%M:%S")} | ระบบกำลังสแกนทุกๆ 5 นาทีอัตโนมัติ</div>', unsafe_allow_html=True)

# --- ปุ่ม Back ---
if st.button("⬅️ Back to Home"):
    st.switch_page("Home.py")

# --- ข้อมูลหุ้น SET100 ---
tickers = ["DELTA.BK", "ADVANC.BK", "PTT.BK", "CPALL.BK", "AOT.BK", "SCB.BK", "KBANK.BK", "GULF.BK", "KTB.BK", "BBL.BK"]

def get_scan_data():
    results = []
    for ticker in tickers:
        try:
            # ดึงข้อมูล 1 ปี เพื่อความแม่นยำของ Hull และ EMA
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue

            # สูตร Guardian Swing (เพิ่มเข้าไปในไส้ในของวันที่ 1)
            df['ema8'] = ta.ema(df['Close'], length=8)
            df['ema20'] = ta.ema(df['Close'], length=20)
            df['hull'] = ta.hma(df['Close'], length=55)
            
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
            p_chg = ((curr['Close'] - prev['Close']) / prev['Close']) * 100
            
            # เช็ค Buy Signal ครบทุกข้อ
            is_buy = (prev['wt1'] < prev['wt2']) and (curr['wt1'] >= curr['wt2']) and (curr['wt1'] < -53) and \
                     (curr['Close'] > curr['ema8']) and (curr['Close'] > curr['ema20']) and \
                     (curr['hull'] > prev['hull']) and (curr['Volume'] > (curr['vma5'] * 1.5))
            
            if is_buy:
                signal = "🚀 BUY"
            elif curr['Close'] < curr['ema20'] or curr['hull'] < prev['hull']:
                signal = "▼ SELL"
            else:
                signal = "HOLD"

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

# --- แสดงผลตาราง ---
with st.spinner(""):
    data = get_scan_data()
    if not data.empty:
        st.table(data)
