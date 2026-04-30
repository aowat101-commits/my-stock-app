import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="SET100 Hull Suite 24H", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 10px; border-radius: 8px;
        text-align: center; font-size: 13px; margin-bottom: 15px; border: 1px solid #334155;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 11px !important; }
    [data-testid="stDataFrame"] td { font-size: 11px !important; text-align: center !important; font-weight: normal !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น SET100 ครบถ้วน
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
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 4. ฟังก์ชันสแกนหาจุดตัดและสถานะ
def scan_signals(df, ticker):
    if len(df) < 35: return None
    
    tz = pytz.timezone('Asia/Bangkok')
    df['hma'] = get_hma(df['Close'], 30)
    df['trend'] = np.where(df['hma'] > df['hma'].shift(1), "UP", "DOWN")
    
    # 24H Limit
    now = datetime.now(tz)
    limit_24h = now - timedelta(hours=24)
    
    # เช็คจุดตัด (Signal)
    df['change'] = (df['trend'] != df['trend'].shift(1))
    signals = df[(df['change']) & (df.index >= limit_24h)]
    
    current_status = "เขียว (ขึ้น)" if df['trend'].iloc[-1] == "UP" else "แดง (ลง)"
    
    if not signals.empty:
        last_sig = signals.iloc[-1]
        sig_type = "🚀 ซื้อ" if last_sig['trend'] == "UP" else "🔻 ขาย"
        # บังคับเวลาให้เป็นไทย
        actual_time = last_sig.name.astimezone(tz)
        
        return {
            "Ticker": ticker.replace('.BK', ''),
            "ราคา": f"{last_sig['Close']:,.2f}",
            "Signal": sig_type,
            "เวลาจริง": actual_time.strftime("%H:%M:%S"),
            "วันที่": actual_time.strftime("%d/%m/%y"),
            "สถานะปัจจุบัน": current_status,
            "raw_time": actual_time
        }
    return None

# 5. การแสดงผลแบบ Auto-Scan ทุก 10 นาที
@st.fragment(run_every="10m")
def dashboard_runtime():
    tz = pytz.timezone('Asia/Bangkok')
    current_bkk = datetime.now(tz).strftime("%d/%m/%y %H:%M:%S")
    st.markdown(f'<div class="time-status">🕒 เวลาปัจจุบัน (BKK): {current_bkk} | สแกนย้อนหลัง 24 ชม.</div>', unsafe_allow_html=True)
    
    all_res = []
    for t in set100_tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="3d", interval="1h") # ดึง 3 วันเพื่อให้ครอบคลุมจุดตัดที่อาจเกิดต้นวัน
            if not hist.empty:
                res = scan_signals(hist, t)
                if res: all_res.append(res)
        except: continue

    if all_res:
        df = pd.DataFrame(all_res).sort_values(by="raw_time", ascending=False)
        
        # ฟังก์ชันจัดสีทั้งแถว
        def style_row(row):
            color = '#10b981' if "ซื้อ" in row['Signal'] else '#ef4444'
            return [f'color: {color};'] * len(row)

        st.dataframe(
            df.drop(columns=['raw_time']).style.apply(style_row, axis=1),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=70),
                "ราคา": st.column_config.TextColumn("ราคาที่เกิด", width=60),
                "Signal": st.column_config.TextColumn("Signal", width=70),
                "เวลาจริง": st.column_config.TextColumn("เวลาจริง", width=75),
                "วันที่": st.column_config.TextColumn("วันที่", width=65),
                "สถานะปัจจุบัน": st.column_config.TextColumn("Status", width=90),
            },
            use_container_width=True, height=750, hide_index=True
        )
    else:
        st.info("🔎 ไม่พบสัญญาณเปลี่ยนสี (HMA 30) ใน 24 ชม. ล่าสุด")

# 6. รัน
st.subheader("🛰️ Hull Suite Intelligence Dashboard")
dashboard_runtime()

if st.button("🔄 Force Scan Now", use_container_width=True):
    st.rerun()
