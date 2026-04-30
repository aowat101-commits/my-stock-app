import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="HMA Signal Monitor", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 10px; border-radius: 6px;
        text-align: center; font-size: 13px; margin-bottom: 15px; border: 1px solid #334155;
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

# 3. ฟังก์ชันคำนวณ HMA (Length=30 ตามความต้องการ)
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 4. ฟังก์ชันค้นหาจุดเปลี่ยนสีล่าสุด (ต้องเป็นจุดตัดจริงเท่านั้น)
def get_actual_signal(df, ticker):
    if len(df) < 40: return None
    
    tz = pytz.timezone('Asia/Bangkok')
    df['hma'] = get_hma(df['Close'], 30)
    df['trend'] = np.where(df['hma'] > df['hma'].shift(1), "UP", "DOWN")
    
    # ตรวจสอบจุดที่เทรนด์มีการสลับฝั่ง (Color Switch)
    df['is_switch'] = df['trend'] != df['trend'].shift(1)
    
    # กรองเอาเฉพาะแถวที่มีการสลับสีจริง ๆ
    switches = df[df['is_switch'] == True].copy()
    
    if not switches.empty:
        # ดึงจุดตัดล่าสุดที่เกิดขึ้น
        last_sig = switches.iloc[-1]
        
        # ป้องกันกรณีที่จุดตัดเป็นจุดแรกของข้อมูลซึ่งไม่มีตัวเทียบ
        if pd.isna(last_sig['hma']): return None
        
        sig_type = "🚀 ซื้อ" if last_sig['trend'] == "UP" else "🔻 ขาย"
        actual_time = last_sig.name.astimezone(tz)
        
        return {
            "Ticker": ticker.replace('.BK', ''),
            "ราคา": f"{last_sig['Close']:,.2f}",
            "Signal": sig_type,
            "เวลา": actual_time.strftime("%H:%M:%S"),
            "วันที่": actual_time.strftime("%d/%m/%y"),
            "raw_time": actual_time # สำหรับ Sorting
        }
    return None

# 5. การแสดงผล (Auto-Scan ทุก 10 นาที)
@st.fragment(run_every="10m")
def live_signal_dashboard():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Last Scan: {datetime.now(tz).strftime("%H:%M:%S")} | แสดงเฉพาะหุ้นที่มีสัญญาณสลับสีล่าสุด</div>', unsafe_allow_html=True)
    
    signal_results = []
    
    # สแกน SET100
    for t in set100_tickers:
        try:
            stock = yf.Ticker(t)
            # ดึงข้อมูลย้อนหลัง 5 วันเพื่อให้ครอบคลุมจุดตัดล่าสุดของหุ้นทุกตัว
            hist = stock.history(period="5d", interval="1h")
            if not hist.empty:
                res = get_actual_signal(hist, t)
                if res:
                    signal_results.append(res)
        except: continue

    if signal_results:
        # เรียงลำดับจากเวลาล่าสุดลงมา (Newest to Oldest)
        df = pd.DataFrame(signal_results).sort_values(by="raw_time", ascending=False)
        
        def style_row(row):
            color = '#10b981' if "ซื้อ" in row['Signal'] else '#ef4444'
            return [f'color: {color};'] * len(row)

        st.dataframe(
            df.drop(columns=['raw_time']).style.apply(style_row, axis=1),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=70),
                "ราคา": st.column_config.TextColumn("ราคา", width=60),
                "Signal": st.column_config.TextColumn("Signal", width=70),
                "เวลา": st.column_config.TextColumn("เวลา", width=75),
                "วันที่": st.column_config.TextColumn("วันที่", width=65),
            },
            use_container_width=True, height=800, hide_index=True
        )
    else:
        st.warning("⚠️ ไม่พบสัญญาณการสลับสีในฐานข้อมูลปัจจุบัน")

# 6. รัน Dashboard
st.subheader("🛰️ SET100 Hull Suite: Active Signals Only")
live_signal_dashboard()

if st.button("🔄 Force Scan Now", use_container_width=True):
    st.rerun()
