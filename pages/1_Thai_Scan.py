ได้รับสูตรคอมโบ The Guardian Swing เรียบร้อยครับ ชุดอินดิเคเตอร์นี้ถือว่าครบถ้วนมากเพราะครอบคลุมทั้ง Trend (EMA, Hull), Momentum (WaveTrend) และที่สำคัญที่สุดคือ Confirmation (Volume) ครับ

เพื่อให้แอปสแกนหุ้นไทย (1_Thai_Scan.py) ทำงานตามกลยุทธ์นี้ได้แม่นยำ ผมได้ปรับปรุงโค้ดโดยใช้การคำนวณเชิงคณิตศาสตร์ตามสูตรที่คุณมิลค์ให้มาเป๊ะๆ ดังนี้ครับ:

🛠️ โค้ดใหม่สำหรับ pages/1_Thai_Scan.py (สูตร The Guardian Swing)
Python
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# ตั้งค่าหน้าจอ
st.set_page_config(layout="wide", page_title="The Guardian Swing Scanner")

# CSS ตกแต่งปุ่มและตาราง
st.markdown("""
    <style>
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    .main { background-color: #0f172a; color: white; }
    div[data-testid="stTable"] { background-color: #1e293b; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ The Guardian Swing Strategy")
st.write("EMA 8, 20 | Hull 55 | WaveTrend | Volume MA 5")

# รายชื่อหุ้นไทย SET100 (คุณมิลค์สามารถเพิ่มได้ตามต้องการ)
tickers = ["DELTA.BK", "ADVANC.BK", "PTT.BK", "CPALL.BK", "AOT.BK", "SCB.BK", "KBANK.BK", "GULF.BK", "KTB.BK", "BBL.BK"]

def scan_guardian_swing(ticker_list):
    results = []
    for ticker in ticker_list:
        try:
            # ดึงข้อมูลย้อนหลัง (ใช้ 1 ปีเพื่อให้ Hull 55 และ EMA คำนวณได้เสถียร)
            data = yf.download(ticker, period="1y", interval="1d", progress=False)
            if data.empty or len(data) < 60: continue
            
            # --- 1. คำนวณค่าตัวแปรหลัก (Inputs) ---
            # EMA 8 และ 20
            data['ema8'] = ta.ema(data['Close'], length=8)
            data['ema20'] = ta.ema(data['Close'], length=20)
            
            # Hull Suite (HMA 55)
            data['hull'] = ta.hma(data['Close'], length=55)
            
            # WaveTrend (WT_LB: 9, 12)
            # สูตร WT: ap = (h+l+c)/3 -> esa = ema(ap, 9) -> d = ema(abs(ap-esa), 9) -> ci = (ap-esa)/(0.015*d) -> tci = ema(ci, 12)
            ap = (data['High'] + data['Low'] + data['Close']) / 3
            esa = ta.ema(ap, length=9)
            d = ta.ema(abs(ap - esa), length=9)
            ci = (ap - esa) / (0.015 * d)
            data['wt1'] = ta.ema(ci, length=12) # TCI
            data['wt2'] = ta.sma(data['wt1'], length=4) # Signal Line
            
            # Volume MA 5
            data['vma5'] = ta.sma(data['Volume'], length=5)
            
            # --- 2. เช็คเงื่อนไขล่าสุด ---
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # เงื่อนไข WT: Bullish Cross ต่ำกว่า -53
            wt_cross_up = (prev['wt1'] < prev['wt2']) and (last['wt1'] >= last['wt2'])
            wt_oversold = last['wt1'] < -53
            
            # เงื่อนไข Trend: ราคา > EMA 8 และ EMA 20
            price_above_ema = (last['Close'] > last['ema8']) and (last['Close'] > last['ema20'])
            
            # เงื่อนไข Hull: สีเขียว (ราคาปิด > เส้น Hull หรือ Hull ขยับขึ้น)
            hull_green = last['hull'] > prev['hull']
            
            # เงื่อนไข Volume: มากกว่าค่าเฉลี่ย 5 วัน อย่างน้อย 1.5 เท่า
            volume_confirm = last['Volume'] > (last['vma5'] * 1.5)
            
            # --- ตรวจสอบเงื่อนไขการซื้อ (Buy Signal) ---
            signal = "Wait"
            if wt_cross_up and wt_oversold and price_above_ema and hull_green and volume_confirm:
                signal = "🔥 BUY: Strong Vol"
            elif price_above_ema and hull_green:
                signal = "Trending"
            
            # --- ตรวจสอบเงื่อนไขการขาย (Sell Alert) ---
            if (last['wt1'] > 53 and prev['wt1'] > prev['wt2'] and last['wt1'] <= last['wt2']) or \
               (last['Close'] < last['ema20']) or (last['hull'] < prev['hull']):
                if signal != "🔥 BUY: Strong Vol":
                    signal = "⚠️ EXIT"

            results.append({
                "Ticker": ticker.replace(".BK", ""),
                "Price": f"{last['Close']:.2f}",
                "RSI": f"{ta.rsi(data['Close'], length=14).iloc[-1]:.1f}",
                "WT": f"{last['wt1']:.1f}",
                "Vol/VMA5": f"{last['Volume']/last['vma5']:.1f}x",
                "Signal": signal
            })
        except:
            continue
    return pd.DataFrame(results)

# ปุ่มกดและแสดงผล
if st.button("🔍 Scan SET100 with Guardian Swing"):
    with st.spinner("Guardian is checking the market..."):
        df = scan_guardian_swing(tickers)
        if not df.empty:
            # ตกแต่งสีให้ Signal
            def color_signal(val):
                if "BUY" in val: color = '#22c55e' # เขียว
                elif "EXIT" in val: color = '#ef4444' # แดง
                else: color = 'white'
                return f'color: {color}; font-weight: bold'
            
            st.dataframe(df.style.applymap(color_signal, subset=['Signal']), use_container_width=True)
        else:
            st.error("Cannot fetch data.")

if st.button("⬅️ Back"):
    st.switch_page("Home.py")
