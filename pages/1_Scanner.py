import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="SET100 Hull Intelligence", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 8px; border-radius: 6px;
        text-align: center; font-size: 12px; margin-bottom: 15px; border: 1px solid #334155;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 11px !important; }
    [data-testid="stDataFrame"] td { font-size: 11px !important; text-align: center !important; font-weight: normal !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น SET100
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

# เตรียม session_state สำหรับเก็บประวัติสัญญาณ
if 'signal_history' not in st.session_state:
    st.session_state.signal_history = {} 

# 3. ฟังก์ชันคำนวณ HMA (Length=30)
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 4. ฟังก์ชันวิเคราะห์สัญญาณ (ซื้อ/ขาย)
def identify_hull_signal(df, ticker):
    if len(df) < 35: return None
    df['hma'] = get_hma(df['Close'], 30)
    curr, prev, prev2 = df['hma'].iloc[-1], df['hma'].iloc[-2], df['hma'].iloc[-3]
    
    curr_trend = "UP" if curr > prev else "DOWN"
    prev_trend = "UP" if prev > prev2 else "DOWN"
    
    new_sig = None
    if prev_trend == "DOWN" and curr_trend == "UP": new_sig = "🚀 ซื้อ"
    elif prev_trend == "UP" and curr_trend == "DOWN": new_sig = "🔻 ขาย"

    if new_sig:
        tz = pytz.timezone('Asia/Bangkok')
        now = datetime.now(tz)
        if ticker not in st.session_state.signal_history or st.session_state.signal_history[ticker]["Signal"] != new_sig:
            st.session_state.signal_history[ticker] = {
                "Signal": new_sig,
                "Date": now.strftime("%d/%m/%y"),
                "Time": now.strftime("%H:%M:%S")
            }
        return st.session_state.signal_history[ticker]
    else:
        if ticker in st.session_state.signal_history:
            del st.session_state.signal_history[ticker]
        return None

# 5. ส่วนแสดงผลแบบ Auto-Scan ทุก 10 นาที
@st.fragment(run_every="10m")
def set100_intelligence():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Last Update: {datetime.now(tz).strftime("%d/%m/%y %H:%M:%S")}</div>', unsafe_allow_html=True)
    
    signals = []
    for t in set100_tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="60d")
            if not hist.empty:
                sig_data = identify_hull_signal(hist, t)
                if sig_data:
                    curr_p = hist['Close'].iloc[-1]
                    signals.append({
                        "Ticker": t.replace('.BK', ''),
                        "ราคา": f"{curr_p:,.2f}", 
                        "Signal": sig_data["Signal"],
                        "เวลา": sig_data["Time"], # สลับเอาเวลาขึ้นก่อน
                        "วันที่": sig_data["Date"]
                    })
        except: continue
    
    if signals:
        df = pd.DataFrame(signals)
        st.dataframe(
            df.style.apply(lambda row: [f'color: {"#10b981" if "ซื้อ" in row["Signal"] else "#ef4444"};'] * len(row), axis=1),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=70),
                "ราคา": st.column_config.TextColumn("ราคา", width=60), 
                "Signal": st.column_config.TextColumn("Signal", width=70),
                "เวลา": st.column_config.TextColumn("เวลา", width=70),
                "วันที่": st.column_config.TextColumn("วันที่", width=60)
            },
            use_container_width=True, height=700, hide_index=True
        )
    else:
        st.info("🔎 ยังไม่พบสัญญาณเปลี่ยนสีในแท่งราคาล่าสุด")

# 6. รัน Dashboard
st.subheader("🛰️ SET100 Hull Suite Intelligence")
set100_intelligence()

if st.button("🔄 Force Scan Now", use_container_width=True):
    st.rerun()
