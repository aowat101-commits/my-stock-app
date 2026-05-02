import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ
st.set_page_config(layout="wide")

# CSS บังคับระยะห่างและสีให้เหมือนรูปเป๊ะ
st.markdown("""
    <style>
    /* ซ่อน Header และ Sidebar */
    [data-testid="stHeader"], header, .stAppHeader, [data-testid="stSidebar"], .stSidebar {
        display: none !important;
    }
    
    .main .block-container {
        padding-top: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* เส้นขีดบางด้านบน */
    .top-line {
        border-top: 1px solid #e5e7eb;
        margin-bottom: 25px;
    }

    /* ปุ่ม Force Refresh แบบชิดซ้าย */
    .stButton>button {
        background-color: transparent !important;
        color: #3b82f6 !important;
        border: none !important;
        padding: 0 !important;
        font-size: 16px !important;
        font-weight: normal !important;
        text-align: left !important;
    }

    /* แถบสีน้ำเงินเข้มตัวหนังสือสีเหลือง */
    .status-bar {
        background-color: #1e293b;
        color: #fbbf24;
        text-align: center;
        padding: 12px;
        border-radius: 6px;
        font-size: 14px;
        margin-top: 20px;
        margin-bottom: 20px;
    }

    /* ตารางสะอาดๆ */
    div[data-testid="stTable"] {
        width: 100%;
        margin-top: 10px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th {
        color: #94a3b8 !important;
        font-weight: normal !important;
        text-align: left !important;
        border-bottom: 1px solid #f1f5f9 !important;
        padding: 10px !important;
    }
    td {
        padding: 10px !important;
        border-bottom: 1px solid #f1f5f9 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ลำดับการวางตามรูป 1777701446869.jpg ---

# 1. เส้นบางด้านบน
st.markdown('<div class="top-line"></div>', unsafe_allow_html=True)

# 2. ปุ่ม Force Refresh (ชิดซ้าย)
if st.button("🔄 Force Refresh Now"):
    st.rerun()

# 3. แถบสถานะสีเข้ม
tz_th = pytz.timezone('Asia/Bangkok')
now_th = datetime.now(tz_th)
st.markdown(f'<div class="status-bar">🇹🇭 Thai Time: {now_th.strftime("%H:%M:%S")} | ระบบกำลังสแกนทุกๆ 5 นาทีอัตโนมัติ</div>', unsafe_allow_html=True)

# 4. ปุ่ม Back (อยู่เหนือตาราง)
if st.button("⬅️ Back to Home"):
    st.switch_page("Home.py")

# --- ข้อมูลและสูตร The Guardian Swing ---
tickers = ["DELTA.BK", "ADVANC.BK", "PTT.BK", "CPALL.BK", "AOT.BK", "SCB.BK", "KBANK.BK", "GULF.BK"]

def get_data():
    results = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue
            
            # คำนวณสูตร Guardian
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

            c = df.iloc[-1]
            p = df.iloc[-2]
            
            # สัญญาณ BUY/SELL
            p_chg = ((c['Close'] - p['Close']) / p['Close']) * 100
            buy = (p['wt1'] < p['wt2']) and (c['wt1'] >= c['wt2']) and (c['wt1'] < -53) and \
                  (c['Close'] > c['ema8']) and (c['Close'] > c['ema20']) and \
                  (c['hull'] > p['hull']) and (c['Volume'] > (c['vma5'] * 1.5))
            
            sig = "🚀 BUY" if buy else ("▼ SELL" if (c['Close'] < c['ema20'] or c['hull'] < p['hull']) else "HOLD")

            results.append({
                "Ticker": ticker.replace(".BK", ""),
                "Price": f"{c['Close']:,.2f}",
                "% Chg": f"{p_chg:+.2f}%",
                "Signal": sig,
                "เวลาไทย": now_th.strftime("%H:%M:%S"),
                "วันที่": now_th.strftime("%d/%m")
            })
        except: continue
    return pd.DataFrame(results)

# 5. แสดงตาราง
with st.spinner(""):
    res_df = get_data()
    if not res_df.empty:
        st.table(res_df)
