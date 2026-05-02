import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอ (Wide Mode)
st.set_page_config(layout="wide", page_title="Market Monitor")

# CSS บังคับหน้าตาให้เหมือนรูป 1777693669717.jpg
st.markdown("""
    <style>
    /* ซ่อน Header และ Sidebar ทั้งหมด */
    [data-testid="stHeader"], header, .stAppHeader, [data-testid="stSidebar"], .stSidebar {
        display: none !important;
    }
    
    /* พื้นหลังสีขาวคลีน */
    .main { background-color: #ffffff; }

    /* กรอบปุ่ม Force Refresh */
    .refresh-container {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 15px;
        text-align: center;
    }
    
    .stButton>button {
        background-color: transparent !important;
        color: #3b82f6 !important;
        border: none !important;
        font-size: 16px !important;
    }

    /* แถบสถานะสีน้ำเงินเข้ม */
    .status-bar {
        background-color: #1e293b;
        color: #fbbf24;
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        font-size: 14px;
        margin-bottom: 20px;
    }

    /* ตารางแบบไม่มีเส้นขอบหนา */
    div[data-testid="stTable"] {
        border: none !important;
    }
    th {
        background-color: #f8fafc !important;
        color: #64748b !important;
        font-weight: normal !important;
        border-bottom: 1px solid #e5e7eb !important;
    }
    td {
        border-bottom: 1px solid #f1f5f9 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ส่วนปุ่มด้านบน ---
st.markdown('<div class="refresh-container">', unsafe_allow_html=True)
if st.button("🔄 Force Refresh Now"):
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- แถบสถานะเวลา ---
tz_th = pytz.timezone('Asia/Bangkok')
now_th = datetime.now(tz_th)
st.markdown(f'<div class="status-bar">🇹🇭 Thai Time: {now_th.strftime("%H:%M:%S")} | ระบบกำลังสแกนทุกๆ 5 นาทีอัตโนมัติ</div>', unsafe_allow_html=True)

# รายชื่อหุ้น SET100
tickers = ["DELTA.BK", "ADVANC.BK", "PTT.BK", "CPALL.BK", "AOT.BK", "SCB.BK", "KBANK.BK", "GULF.BK", "KTB.BK"]

def get_guardian_data():
    results = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue

            # คำนวณสูตร The Guardian Swing
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

            # Logic สัญญาณ
            buy_signal = (p['wt1'] < p['wt2']) and (c['wt1'] >= c['wt2']) and (c['wt1'] < -53) and \
                         (c['Close'] > c['ema8']) and (c['Close'] > c['ema20']) and \
                         (c['hull'] > p['hull']) and (c['Volume'] > (c['vma5'] * 1.5))
            
            p_chg = ((c['Close'] - p['Close']) / p['Close']) * 100
            
            # กำหนด Signal และสี
            if buy_signal:
                sig_text = "🚀 BUY"
            elif c['Close'] < c['ema20'] or c['hull'] < p['hull']:
                sig_text = "▼ SELL"
            else:
                sig_text = "HOLD"

            results.append({
                "Ticker": ticker.replace(".BK", ""),
                "Price": f"{c['Close']:,.2f}",
                "% Chg": f"{p_chg:+.2f}%",
                "Signal": sig_text,
                "เวลาไทย": now_th.strftime("%H:%M:%S"),
                "วันที่": now_th.strftime("%d/%m")
            })
        except: continue
    return pd.DataFrame(results)

# แสดงผลตารางแบบคลีนเป๊ะ
with st.spinner(""):
    final_df = get_guardian_data()
    if not final_df.empty:
        # ฟังก์ชันแต่งสีตัวหนังสือในตาราง
        def style_signal(val):
            if "BUY" in str(val): return 'color: #10b981' # เขียว
            if "SELL" in str(val): return 'color: #ef4444' # แดง
            return 'color: #64748b' # เทา

        # ใช้ st.table เพื่อให้หน้าตาเหมือนรูปตัวอย่างที่สุด
        st.table(final_df)

# ปุ่มกลับหน้าหลักแบบเรียบๆ
if st.button("⬅️ Back to Home"):
    st.switch_page("Home.py")
