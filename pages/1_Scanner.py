import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="Market Intelligence Dashboard", layout="wide")

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

# 2. รายชื่อหุ้นแบบจัดเต็ม (SET100 + sSET/MAI ตัวเด่น)
set100 = [
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

extra_growth = [
    'TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 
    'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'MASTER.BK', 'KLINIQ.BK', 'WARRIX.BK', 
    'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK'
]

full_scan_list = list(set(set100 + extra_growth))

# 3. ฟังก์ชันคำนวณ HMA 30
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 4. ฟังก์ชันค้นหาจุดเปลี่ยนสีล่าสุด
def get_last_signal(df, ticker):
    if len(df) < 35: return None
    tz = pytz.timezone('Asia/Bangkok')
    df['hma'] = get_hma(df['Close'], 30)
    df['trend'] = np.where(df['hma'] > df['hma'].shift(1), "UP", "DOWN")
    df['is_switch'] = df['trend'] != df['trend'].shift(1)
    
    switches = df[df['is_switch'] == True].copy()
    if not switches.empty:
        last_sig = switches.iloc[-1]
        actual_time = last_sig.name.astimezone(tz)
        return {
            "Ticker": ticker.replace('.BK', ''),
            "ราคาที่ตัด": last_sig['Close'], # ส่งเป็นตัวเลขเพื่อนำไป Format ในตาราง
            "Signal": "🚀 ซื้อ" if last_sig['trend'] == "UP" else "🔻 ขาย",
            "เวลา": actual_time.strftime("%H:%M:%S"),
            "วันที่": actual_time.strftime("%d/%m/%y"),
            "raw_time": actual_time
        }
    return None

# 5. ส่วนหัวและปุ่มรีเฟรช
st.subheader("🛰️ Market Intelligence: Top 30 Active Signals")

if st.button("🔄 Force Refresh Scan", use_container_width=True):
    st.rerun()

# 6. Dashboard อัปเดตออโต้ทุก 10 นาที
@st.fragment(run_every="10m")
def dashboard_runtime():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Last Update: {datetime.now(tz).strftime("%H:%M:%S")} | สแกนหุ้น SET100 + sSET + MAI</div>', unsafe_allow_html=True)
    
    results = []
    bar = st.progress(0, text="กำลังสแกนหาจังหวะเปลี่ยนสีล่าสุด...")
    
    total = len(full_scan_list)
    for i, t in enumerate(full_scan_list):
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="10d", interval="1h")
            if not hist.empty:
                res = get_last_signal(hist, t)
                if res: results.append(res)
        except: continue
        bar.progress((i + 1) / total)
    
    bar.empty()

    if results:
        # เรียงตามความสดใหม่และคัดเฉพาะ 30 ตัวล่าสุด
        df = pd.DataFrame(results).sort_values(by="raw_time", ascending=False).head(30)
        
        def style_row(row):
            color = '#10b981' if "ซื้อ" in row['Signal'] else '#ef4444'
            return [f'color: {color};'] * len(row)

        st.dataframe(
            df.drop(columns=['raw_time']).style.apply(style_row, axis=1)
            .format({"ราคาที่ตัด": "{:,.2f}"}), # กำหนดทศนิยม 2 ตำแหน่ง (0.00) ตรงนี้
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=70),
                "ราคาที่ตัด": st.column_config.NumberColumn("ราคา", width=65, format="%.2f"), # บังคับ Format ใน Column Config ด้วย
                "Signal": st.column_config.TextColumn("Signal", width=70),
                "เวลา": st.column_config.TextColumn("เวลาจริง", width=75),
                "วันที่": st.column_config.TextColumn("วันที่", width=65),
            },
            use_container_width=True, height=650, hide_index=True
        )

dashboard_runtime()
