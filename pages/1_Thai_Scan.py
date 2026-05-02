import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ (คงเดิม)
st.set_page_config(page_title="Guardian Intelligence", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status {
        background-color: #1e293b; color: #fbbf24; padding: 10px; border-radius: 6px;
        text-align: center; font-size: 13px; margin-bottom: 15px; border: 1px solid #334155;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 11px !important; }
    [data-testid="stDataFrame"] td { font-size: 11px !important; text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น (ใช้ลิสต์ที่คุณมิลค์ให้มา)
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'CPALL.BK', 'DELTA.BK', 'GULF.BK', 'KBANK.BK', 'PTT.BK', 'SCB.BK'] # ... (ย่อเพื่อประหยัดพื้นที่)
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

# 3. ฟังก์ชันคำนวณ WaveTrend (ตามสูตรคอมโบ)
def get_wt(df):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ta.ema(ap, length=10)
    d = ta.ema(abs(ap - esa), length=10)
    ci = (ap - esa) / (0.015 * d)
    wt1 = ta.ema(ci, length=21)
    wt2 = ta.sma(wt1, length=4)
    return wt1, wt2

# 4. ฟังก์ชันสแกนด้วยเงื่อนไข The Guardian Swing
def scan_guardian(df, ticker):
    if len(df) < 60: return None
    
    # คำนวณอินดิเคเตอร์
    df['ema8'] = ta.ema(df['Close'], length=8)
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['hull'] = ta.hma(df['Close'], length=55)
    df['wt1'], df['wt2'] = get_wt(df)
    df['vma5'] = ta.sma(df['Volume'], length=5)
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # เงื่อนไข Buy: WT ตัดขึ้น < -53 + ราคาเหนือ EMA + Hull เขียว + Vol 1.5x
    wt_cross = (prev['wt1'] < prev['wt2']) and (curr['wt1'] >= curr['wt2'])
    is_buy = wt_cross and (curr['wt1'] < -53) and \
             (curr['Close'] > curr['ema8']) and (curr['Close'] > curr['ema20']) and \
             (curr['hull'] > prev['hull']) and (curr['Volume'] > (curr['vma5'] * 1.5))
             
    # เงื่อนไข Sell: WT ตัดลง > 53 หรือ หลุด EMA20 หรือ Hull แดง
    is_sell = (curr['wt1'] > 53 and prev['wt1'] > prev['wt2'] and curr['wt1'] <= curr['wt2']) or \
              (curr['Close'] < curr['ema20']) or (curr['hull'] < prev['hull'])
    
    if is_buy or is_sell:
        tz = pytz.timezone('Asia/Bangkok')
        actual_time = curr.name.astimezone(tz)
        return {
            "Ticker": ticker.replace('.BK', ''),
            "Price": round(float(curr['Close']), 2),
            "Signal": "🚀 BUY" if is_buy else "🔻 SELL",
            "WT": round(float(curr['wt1']), 2),
            "Vol_Ratio": round(float(curr['Volume']/curr['vma5']), 2),
            "เวลา": actual_time.strftime("%H:%M:%S"),
            "raw_time": actual_time
        }
    return None

# 5. Dashboard Runtime (Fragment 10 นาที)
@st.fragment(run_every="10m")
def dashboard_runtime():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Last Update: {datetime.now(tz).strftime("%H:%M:%S")} | Strategy: The Guardian Swing</div>', unsafe_allow_html=True)
    
    results = []
    bar = st.progress(0, text="Guardian กำลังสแกนหาจังหวะที่เป๊ะที่สุด...")
    
    for i, t in enumerate(full_scan_list):
        try:
            hist = yf.download(t, period="60d", interval="1h", progress=False)
            if not hist.empty:
                res = scan_guardian(hist, t)
                if res: results.append(res)
        except: continue
        bar.progress((i + 1) / len(full_scan_list))
    
    bar.empty()

    if results:
        df = pd.DataFrame(results).sort_values(by="raw_time", ascending=False).head(30)
        
        def style_row(row):
            color = '#10b981' if "BUY" in row['Signal'] else '#ef4444'
            return [f'color: {color};'] * len(row)

        st.dataframe(
            df.drop(columns=['raw_time']).style.apply(style_row, axis=1)
            .format({"Price": "{:,.2f}", "WT": "{:,.2f}", "Vol_Ratio": "{:,.2f}x"}),
            use_container_width=True, height=600, hide_index=True
        )

dashboard_runtime()
