import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอแบบ Wide ตามเดิม
st.set_page_config(layout="wide")

# CSS บังคับโครงสร้างให้เหมือนรูป 1777693897312.jpg เป๊ะๆ
st.markdown("""
    <style>
    /* ซ่อน Header และ Sidebar */
    [data-testid="stHeader"], header, .stAppHeader, [data-testid="stSidebar"], .stSidebar {
        display: none !important;
    }
    
    .main .block-container {
        padding-top: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }

    /* กรอบสี่เหลี่ยมโค้งมนด้านบนสุด */
    .top-outline {
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        height: 45px;
        margin-bottom: 20px;
    }

    /* ปุ่ม Force Refresh ชิดซ้าย ไม่มีกรอบ */
    .stButton>button {
        background-color: transparent !important;
        color: #3b82f6 !important;
        border: none !important;
        padding: 0 !important;
        font-size: 14px !important;
        font-weight: normal !important;
        text-align: left !important;
        display: flex !important;
        align-items: center !important;
    }

    /* แถบสถานะสีน้ำเงินเข้มตัวหนังสือสีเหลืองกึ่งกลาง */
    .status-bar {
        background-color: #1e293b;
        color: #fbbf24;
        text-align: center;
        padding: 15px;
        border-radius: 6px;
        font-size: 13px;
        margin-top: 25px;
        margin-bottom: 20px;
        letter-spacing: 0.5px;
    }

    /* สไตล์ตารางแบบคลีน */
    div[data-testid="stTable"] {
        margin-top: 10px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th {
        color: #94a3b8 !important;
        font-weight: normal !important;
        border-bottom: 1px solid #f1f5f9 !important;
        padding: 12px 8px !important;
    }
    td {
        padding: 12px 8px !important;
        border-bottom: 1px solid #f1f5f9 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ลำดับการแสดงผลตามรูป 1777693897312.jpg ---

# 1. กรอบโค้งมนบนสุด
st.markdown('<div class="top-outline"></div>', unsafe_allow_html=True)

# 2. ปุ่ม Force Refresh Now
if st.button("🔄 Force Refresh Now"):
    st.rerun()

# 3. แถบสถานะสีเข้ม
tz_th = pytz.timezone('Asia/Bangkok')
now_th = datetime.now(tz_th)
st.markdown(f'<div class="status-bar">🇹🇭 Thai Time: {now_th.strftime("%H:%M:%S")} | ระบบกำลังสแกนทุกๆ 5 นาทีอัตโนมัติ</div>', unsafe_allow_html=True)

# 4. ปุ่ม Back to Home (ชิดซ้าย)
if st.button("⬅️ Back to Home"):
    st.switch_page("Home.py")

# --- ส่วนข้อมูลและการคำนวณ (The Guardian Swing) ---
# รายชื่อหุ้นในพอร์ตที่คุณสนใจ
tickers = ["DELTA.BK", "ADVANC.BK", "PTT.BK", "CPALL.BK", "AOT.BK", "SCB.BK", "KBANK.BK", "GULF.BK"]

def fetch_guardian_signals():
    results = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue
            
            # คำนวณอินดิเคเตอร์ตามสูตร Guardian Swing
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
            
            # เช็คเงื่อนไข Buy/Sell
            p_chg = ((curr['Close'] - prev['Close']) / prev['Close']) * 100
            
            buy_condition = (prev['wt1'] < prev['wt2']) and (curr['wt1'] >= curr['wt2']) and (curr['wt1'] < -53) and \
                            (curr['Close'] > curr['ema8']) and (curr['Close'] > curr['ema20']) and \
                            (curr['hull'] > prev['hull']) and (curr['Volume'] > (curr['vma5'] * 1.5))
            
            if buy_condition:
                sig = "🚀 BUY"
            elif curr['Close'] < curr['ema20'] or curr['hull'] < prev['hull']:
                sig = "▼ SELL"
            else:
                sig = "HOLD"

            results.append({
                "Ticker": ticker.replace(".BK", ""),
                "Price": f"{curr['Close']:,.2f}",
                "% Chg": f"{p_chg:+.2f}%",
                "Signal": sig,
                "เวลาไทย": now_th.strftime("%H:%M:%S"),
                "วันที่": now_th.strftime("%d/%m")
            })
        except: continue
    return pd.DataFrame(results)

# 5. แสดงผลตารางแบบคลีน
with st.spinner(""):
    scan_df = fetch_guardian_signals()
    if not scan_df.empty:
        st.table(scan_df)
