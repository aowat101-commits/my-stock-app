import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="SET100 Real-time Board", layout="wide")

# --- รายชื่อหุ้น SET100 ---
SET100_FULL = [
    'ADVANC.BK', 'AOT.BK', 'AWC.BK', 'BANPU.BK', 'BBL.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK',
    'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'EA.BK',
    'EGCO.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'INTUCH.BK', 'IRPC.BK', 'IVL.BK',
    'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'OSP.BK',
    'PLANB.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'RATCH.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK',
    'SIRI.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STGT.BK', 'TASCO.BK', 'TCAP.BK', 'TIDLOR.BK', 'TISCO.BK', 'TOP.BK',
    'TRUE.BK', 'TTB.BK', 'TU.BK', 'WHA.BK'
]

st.title("🇹🇭 SET100 Live Market Board")

# --- ส่วนควบคุมการอัปเดตอัตโนมัติ ---
st.sidebar.header("⏱️ Live Settings")
auto_refresh = st.sidebar.toggle("เปิดการอัปเดตอัตโนมัติ (30s)", value=True)
refresh_interval = 30

if "price_df" not in st.session_state:
    st.session_state.price_df = pd.DataFrame()
    st.session_state.last_refresh = "-"

# --- ฟังก์ชันดึงข้อมูลราคาและมูลค่า ---
def fetch_all_prices():
    all_data = []
    status_msg = st.empty()
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(SET100_FULL):
        status_msg.text(f"กำลังดึงข้อมูล: {ticker} ({i+1}/{len(SET100_FULL)})")
        progress_bar.progress((i + 1) / len(SET100_FULL))
        try:
            stock = yf.Ticker(ticker)
            # ดึงข้อมูล 2 วันล่าสุดเพื่อเอาราคาปิดวันก่อนหน้า
            hist = stock.history(period="2d")
            if len(hist) >= 1:
                current = hist['Close'].iloc[-1]
                # ราคาปิดวันก่อนหน้า (Previous Close)
                prev_close = stock.info.get('previousClose', hist['Open'].iloc[-1])
                
                change = current - prev_close
                p_change = (change / prev_close) * 100
                
                # มูลค่าการซื้อขาย (Volume * Price) หรือใช้ค่าจาก info
                volume = hist['Volume'].iloc[-1]
                turnover = (volume * current) / 1_000_000 # หน่วย: ล้านบาท
                
                all_data.append({
                    "Ticker": ticker.replace(".BK", ""),
                    "ราคาล่าสุด": round(current, 2),
                    "ราคาปิดก่อนหน้า": round(prev_close, 2),
                    "เปลี่ยนแปลง": f"{change:+.2f}",
                    "% เปลี่ยนแปลง": f"{p_change:+.2f}%",
                    "มูลค่า (ล้านบาท)": round(turnover, 2),
                    "เวลา": datetime.now().strftime("%H:%M:%S")
                })
        except:
            continue
            
    progress_bar.empty()
    status_msg.empty()
    return pd.DataFrame(all_data)

# --- ส่วนแสดงผล ---
if st.button("🔄 Manual Refresh") or st.session_state.price_df.empty:
    st.session_state.price_df = fetch_all_prices()
    st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")

st.write(f"อัปเดตล่าสุดเมื่อ: **{st.session_state.last_refresh}**")

if not st.session_state.price_df.empty:
    # ฟังก์ชันใส่สีตัวเลข
    def style_change(val):
        if isinstance(val, str):
            if '+' in val: return 'color: #00ff00'
            if '-' in val: return 'color: #ff4b4b'
        return 'color: white'

    # แสดงตาราง (จัดเรียงตามมูลค่าการซื้อขายจากมากไปน้อย)
    df_display = st.session_state.price_df.sort_values(by="มูลค่า (ล้านบาท)", ascending=False)
    
    st.dataframe(
        df_display.style.map(style_change, subset=['เปลี่ยนแปลง', '% เปลี่ยนแปลง']),
        use_container_width=True,
        hide_index=True,
        height=600
    )

# --- ระบบนับถอยหลัง ---
if auto_refresh:
    countdown = st.sidebar.empty()
    for i in range(refresh_interval, 0, -1):
        countdown.metric("อัปเดตใหม่ในอีก", f"{i} วินาที")
        time.sleep(1)
    
    st.session_state.price_df = fetch_all_prices()
    st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
    st.rerun()