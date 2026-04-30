import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft (อิงตามรูป 1777556027968.jpg)
st.set_page_config(page_title="Intelligence Dashboard", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status {
        background-color: #1e293b;
        color: #10b981;
        padding: 8px;
        border-radius: 6px;
        text-align: center;
        font-size: 12px;
        margin-bottom: 15px;
        border: 1px solid #334155;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 11px !important; }
    [data-testid="stDataFrame"] td { font-size: 11px !important; text-align: center !important; font-weight: normal !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นที่กำลังเฝ้าดู (Watchlist) และ SET100
watchlist = ['IONQ', 'IREN', 'ONDS', 'SMX', 'DELTA.BK', 'GULF.BK', 'ADVANC.BK', 'PTT.BK', 'KBANK.BK']

set100_tickers = [
    'AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK',
    'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK',
    'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK',
    'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK',
    'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK',
    'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK',
    'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK',
    'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK',
    'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK',
    'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK',
    'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK'
]

# 3. ฟังก์ชันคำนวณ HMA (Length=30 ตามรูป 1777558595938.jpg)
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length = int(length / 2)
    sqrt_length = int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 4. ฟังก์ชันวิเคราะห์สัญญาณ (อ้างอิงรูป 1777558595938.jpg)
def identify_hull_signal(df):
    if len(df) < 35: return None, None
    df['hma'] = get_hma(df['Close'], 30)
    curr, prev, prev2 = df['hma'].iloc[-1], df['hma'].iloc[-2], df['hma'].iloc[-3]
    curr_trend = "UP" if curr > prev else "DOWN"
    prev_trend = "UP" if prev > prev2 else "DOWN"
    tz = pytz.timezone('Asia/Bangkok')
    time_str = datetime.now(tz).strftime("%H:%M:%S")

    if prev_trend == "DOWN" and curr_trend == "UP": return "🚀 ซื้อ", time_str
    if prev_trend == "UP" and curr_trend == "DOWN": return "🔻 ขาย", time_str
    return None, None

# 5. ส่วนแสดงผลแบบ Auto-Scan ทุก 10 นาที
@st.fragment(run_every="10m")
def intelligence_dashboard():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Auto-Scan Every 10m: {datetime.now(tz).strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
    
    # ฟังก์ชันช่วยดึงข้อมูลและกรองสัญญาณ
    def fetch_signals(ticker_list, label):
        found = []
        for t in ticker_list:
            try:
                stock = yf.Ticker(t)
                hist = stock.history(period="60d")
                if not hist.empty:
                    sig, sig_time = identify_hull_signal(hist)
                    if sig:
                        curr_p, prev_p = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                        found.append({
                            "Ticker": t.replace('.BK', ''),
                            "ราคา": f"{curr_p:,.2f}",
                            "Chg%": ((curr_p - prev_p) / prev_p) * 100,
                            "Signal": sig,
                            "เวลา": sig_time
                        })
            except: continue
        return pd.DataFrame(found)

    # --- ส่วนที่ 1: หุ้นที่กำลังเฝ้าดู (Watchlist) ---
    st.subheader("⭐ Watchlist Alerts")
    df_watch = fetch_signals(watchlist, "Watchlist")
    if not df_watch.empty:
        st.dataframe(df_watch.style.apply(lambda row: [f'color: {"#10b981" if "ซื้อ" in row["Signal"] else "#ef4444"};'] * len(row), axis=1)
                     .format({"Chg%": "{:+.2f}%"}), use_container_width=True, hide_index=True)
    else:
        st.info("🔎 หุ้นที่เฝ้าดูยังไม่มีสัญญาณเปลี่ยนสีในขณะนี้")

    st.divider()

    # --- ส่วนที่ 2: หุ้น SET100 ทั้งหมด ---
    st.subheader("📊 SET100 Market Scan")
    df_set100 = fetch_signals(set100_tickers, "SET100")
    if not df_set100.empty:
        st.dataframe(df_set100.style.apply(lambda row: [f'color: {"#10b981" if "ซื้อ" in row["Signal"] else "#ef4444"};'] * len(row), axis=1)
                     .format({"Chg%": "{:+.2f}%"}), use_container_width=True, hide_index=True)
    else:
        st.info("🔎 ยังไม่พบสัญญาณใหม่จาก SET100")

# 6. รัน Dashboard
intelligence_dashboard()

if st.button("🔄 Force Scan Now", use_container_width=True):
    st.rerun()
