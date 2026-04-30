import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="SET100 24H Intelligence", layout="wide")

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

# 3. ฟังก์ชันคำนวณ HMA (Length=30)
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 4. ฟังก์ชันวิเคราะห์หาจุดเปลี่ยนสีในช่วง 24 ชม.
def scan_24h_signals(df, ticker):
    if len(df) < 35: return None
    
    df['hma'] = get_hma(df['Close'], 30)
    # หาจุดเปลี่ยนเทรนด์: เช็คว่าแท่งปัจจุบันต่างจากแท่งก่อนหน้าหรือไม่
    df['trend'] = np.where(df['hma'] > df['hma'].shift(1), "UP", "DOWN")
    df['prev_trend'] = df['trend'].shift(1)
    
    # กำหนดเงื่อนไขเวลา 24 ชม. ล่าสุด
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    limit_24h = now - timedelta(hours=24)
    
    # กรองเฉพาะจุดที่มีการสลับเทรนด์ (Signal Change)
    signals = df[(df['trend'] != df['prev_trend']) & (df.index >= limit_24h)].copy()
    
    if not signals.empty:
        # เลือกสัญญาณล่าสุดที่เกิดขึ้นใน 24 ชม.
        last_sig = signals.iloc[-1]
        sig_type = "🚀 ซื้อ" if last_sig['trend'] == "UP" else "🔻 ขาย"
        sig_time = last_sig.name.astimezone(tz)
        
        return {
            "Ticker": ticker.replace('.BK', ''),
            "ราคา": f"{last_sig['Close']:,.2f}",
            "Signal": sig_type,
            "เวลา": sig_time.strftime("%H:%M:%S"),
            "วันที่": sig_time.strftime("%d/%m/%y"),
            "raw_time": sig_time # ใช้สำหรับเรียงลำดับ
        }
    return None

# 5. ส่วนแสดงผลแบบ Auto-Scan
@st.fragment(run_every="10m")
def set100_24h_intelligence():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Scan Period: Last 24 Hours | Updated: {datetime.now(tz).strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
    
    all_signals = []
    # ใช้ progress bar เพราะสแกนย้อนหลังอาจใช้เวลาเล็กน้อย
    progress_text = "Scanning SET100 signals in last 24h..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, t in enumerate(set100_tickers):
        try:
            # ดึงข้อมูลรายชั่วโมง หรือ ราย 15 นาทีเพื่อให้ได้เวลาที่แม่นยำขึ้น
            stock = yf.Ticker(t)
            hist = stock.history(period="5d", interval="1h") # ใช้ interval 1h เพื่อดูจุดเปลี่ยนใน 24 ชม.
            if not hist.empty:
                res = scan_24h_signals(hist, t)
                if res:
                    all_signals.append(res)
        except: continue
        my_bar.progress((i + 1) / len(set100_tickers), text=progress_text)
    
    my_bar.empty()

    if all_signals:
        # เรียงลำดับตามเวลาที่เกิดจริง (ใหม่ล่าสุดอยู่บน)
        df = pd.DataFrame(all_signals).sort_values(by="raw_time", ascending=False)
        st.dataframe(
            df.drop(columns=['raw_time']).style.apply(lambda row: [f'color: {"#10b981" if "ซื้อ" in row["Signal"] else "#ef4444"};'] * len(row), axis=1),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=70),
                "ราคา": st.column_config.TextColumn("ราคาที่เกิด", width=65), 
                "Signal": st.column_config.TextColumn("Signal", width=70),
                "เวลา": st.column_config.TextColumn("เวลาจริง", width=75),
                "วันที่": st.column_config.TextColumn("วันที่", width=65)
            },
            use_container_width=True, height=750, hide_index=True
        )
    else:
        st.info("🔎 ไม่พบสัญญาณเปลี่ยนสี (HMA 30) ในช่วง 24 ชั่วโมงที่ผ่านมา")

# 6. รัน Dashboard
st.subheader("🛰️ SET100 Hull Suite: 24H Signal Tracker")
set100_24h_intelligence()

if st.button("🔄 Force Refresh Scan", use_container_width=True):
    st.rerun()
