import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# 1. Page Configuration & Style
st.set_page_config(page_title="Debug Mode: Signal Hunter", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #0f172a; }
    .stStatusWidget {display: none !important;}
    .debug-log {
        background-color: #1e293b; color: #94a3b8; padding: 10px; 
        border-radius: 5px; font-family: monospace; font-size: 11px;
        height: 150px; overflow-y: auto; border: 1px solid #334155; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Ticker List (คัดเฉพาะตัวหลักเพื่อความชัวร์ในการ Test)
test_list = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'KBANK.BK', 'PTT.BK', 'SCB.BK', 'GULF.BK', 'HANA.BK', 'KCE.BK', 'JTS.BK', 'DITTO.BK', 'COCOCO.BK', 'MASTER.BK']

# 3. Indicator Functions
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

def get_wavetrend(df):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ta.ema(ap, length=10)
    d = ta.ema(abs(ap - esa), length=10)
    ci = (ap - esa) / (0.015 * d)
    wt1 = ta.ema(ci, length=21)
    wt2 = ta.sma(wt1, length=4)
    return wt1, wt2

# 4. Scanner Logic
def scan_debug(ticker):
    try:
        # ใช้ข้อมูล 7 วัน (รายชั่วโมง) เพื่อความรวดเร็วในการ Debug
        df = yf.download(ticker, period="7d", interval="1h", progress=False)
        if df.empty: return "No Data"

        df['hma'] = get_hma(df['Close'], 24)
        wt1, wt2 = get_wavetrend(df)
        df['wt1'], df['wt2'] = wt1, wt2
        
        # เงื่อนไข: Hull เขียว + WT ตัดขึ้น (ไม่จำกัดโซน)
        df['hull_up'] = df['hma'] > df['hma'].shift(1)
        df['wt_cross'] = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2'])
        
        signals = df[df['hull_up'] & df['wt_cross']].copy()
        
        if not signals.empty:
            last_sig = signals.iloc[-1]
            return {
                "Ticker": ticker,
                "Price": last_sig['Close'],
                "Time": last_sig.name.strftime("%d/%m %H:%M"),
                "WT1": round(last_sig['wt1'], 2)
            }
        return "No Signal"
    except Exception as e:
        return f"Error: {str(e)}"

# 5. Dashboard UI
st.subheader("🛠️ Debug Scanner: Finding Any Signal")

if st.button("🚀 Start Debug Scan", use_container_width=True):
    log_area = st.empty()
    results = []
    
    # ส่วนของ Log เพื่อดูว่าระบบกำลังทำอะไร
    debug_content = "🔍 Starting Debug Process...\n"
    
    for t in test_list:
        debug_content += f"Scanning {t}... "
        res = scan_debug(t)
        
        if isinstance(res, dict):
            results.append(res)
            debug_content += "✅ FOUND SIGNAL\n"
        else:
            debug_content += f"❌ {res}\n"
            
        log_area.markdown(f'<div class="debug-log">{debug_content}</div>', unsafe_allow_html=True)
    
    if results:
        st.success(f"พบหุ้นที่มีสัญญาณทั้งหมด {len(results)} ตัว")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("ไม่พบสัญญาณใดๆ ในหุ้นทดสอบ 14 ตัวนี้")

st.info("โหมดนี้ใช้เพื่อเช็คว่าระบบดึงข้อมูลจาก Yahoo ได้ปกติหรือไม่ โดยใช้หุ้นตัวอย่างเพียงไม่กี่ตัว")
