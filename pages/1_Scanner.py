import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft (อ้างอิง User Summary: Japanese Vintage & Loft)
st.set_page_config(page_title="HMA Last Signal Tracker", layout="wide")

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

# 2. รายชื่อหุ้น SET100 (ดึงข้อมูลตลาดหุ้นไทยตามความสนใจ)
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

# 3. ฟังก์ชันคำนวณ HMA (Length=30 ตามไฟล์ 1777558595938.jpg)
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 4. ฟังก์ชันค้นหาสัญญาณล่าสุด (ย้อนกลับไปจนกว่าจะเจอจุดตัด)
def find_last_switch(df, ticker):
    if len(df) < 40: return None
    
    tz = pytz.timezone('Asia/Bangkok')
    df['hma'] = get_hma(df['Close'], 30)
    df['trend'] = np.where(df['hma'] > df['hma'].shift(1), "UP", "DOWN")
    
    # ค้นหาจุดที่มีการเปลี่ยน trend (Signal Change)
    df['change'] = df['trend'] != df['trend'].shift(1)
    switches = df[df['change']].copy()
    
    if not switches.empty:
        # ดึงแถวสุดท้ายที่มีการเปลี่ยนสี
        last_sig = switches.iloc[-1]
        sig_type = "🚀 ซื้อ" if last_sig['trend'] == "UP" else "🔻 ขาย"
        actual_time = last_sig.name.astimezone(tz)
        
        return {
            "Ticker": ticker.replace('.BK', ''),
            "ราคาที่เกิด": f"{last_sig['Close']:,.2f}",
            "Signal": sig_type,
            "เวลาจริง": actual_time.strftime("%H:%M:%S"),
            "วันที่": actual_time.strftime("%d/%m/%y"),
            "raw_time": actual_time # ใช้จัดลำดับ
        }
    return None

# 5. ส่วนการแสดงผล (Auto-Scan 10m)
@st.fragment(run_every="10m")
def dashboard_latest_signals():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Last Scan: {datetime.now(tz).strftime("%d/%m/%y %H:%M:%S")} | ดึงสัญญาณล่าสุดของหุ้นแต่ละตัว</div>', unsafe_allow_html=True)
    
    results = []
    for t in set100_tickers:
        try:
            # ดึงข้อมูลย้อนหลัง 7 วันเพื่อให้ชัวร์ว่าจะเจอจุดตัดล่าสุดของทุกตัว
            stock = yf.Ticker(t)
            hist = stock.history(period="7d", interval="1h")
            if not hist.empty:
                res = find_last_switch(hist, t)
                if res: results.append(res)
        except: continue

    if results:
        # เรียงตามเวลาที่เกิดสัญญาณจริง (ตัวที่เพิ่งเปลี่ยนสีล่าสุดจะอยู่บนสุด)
        df = pd.DataFrame(results).sort_values(by="raw_time", ascending=False)
        
        def style_row(row):
            color = '#10b981' if "ซื้อ" in row['Signal'] else '#ef4444'
            return [f'color: {color}; font-weight: normal;'] * len(row)

        st.dataframe(
            df.drop(columns=['raw_time']).style.apply(style_row, axis=1),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=70),
                "ราคาที่เกิด": st.column_config.TextColumn("ราคา", width=60),
                "Signal": st.column_config.TextColumn("Signal", width=70),
                "เวลาจริง": st.column_config.TextColumn("เวลา", width=75),
                "วันที่": st.column_config.TextColumn("วันที่", width=65),
            },
            use_container_width=True, height=800, hide_index=True
        )

# 6. รัน
st.subheader("🛰️ SET100 Hull Suite: Last Signal Tracker")
dashboard_latest_signals()

if st.button("🔄 Force Scan Now", use_container_width=True):
    st.rerun()
