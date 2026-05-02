import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์
st.set_page_config(page_title="Guardian Swing: Broad Scan v3", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    .main { background-color: #0f172a; }
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 12px; border-radius: 8px;
        text-align: center; font-size: 14px; margin-bottom: 15px; border: 1px solid #334155;
        font-weight: bold;
    }
    .debug-log {
        background-color: #1e293b; color: #94a3b8; padding: 10px; 
        border-radius: 5px; font-family: monospace; font-size: 11px;
        height: 120px; overflow-y: auto; border: 1px solid #334155; margin-bottom: 20px;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 12px !important; }
    [data-testid="stDataFrame"] td { font-size: 13px !important; text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น (SET100 + Extra Growth)
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

# 3. ฟังก์ชันสแกนหลัก
def analyze_broad_v3(ticker):
    try:
        # ดึงข้อมูลย้อนหลัง 15 วัน (รายชั่วโมง)
        df = yf.download(ticker, period="15d", interval="1h", progress=False)
        
        # แก้ปัญหา Multi-index (จุดสำคัญที่คุณมิลค์เจอ)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty or len(df) < 25: return None
        
        df = df.dropna()

        # คำนวณ Indicators โดยใช้ pandas_ta
        df['hma'] = ta.hma(df['Close'], length=24)
        df['ema21'] = ta.ema(df['Close'], length=21)
        
        # WaveTrend Calculation
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa = ta.ema(ap, length=10)
        d = ta.ema(abs(ap - esa), length=10)
        ci = (ap - esa) / (0.015 * d)
        df['wt1'] = ta.ema(ci, length=21)
        df['wt2'] = ta.sma(df['wt1'], length=4)
        
        df = df.dropna()

        # เงื่อนไขเช็คทรงขาขึ้นแบบ Broad Scan
        is_bullish = (df['Close'].iloc[-1] > df['ema21'].iloc[-1]) & \
                     (df['hma'].iloc[-1] > df['hma'].iloc[-2]) & \
                     (df['wt1'].iloc[-1] > df['wt2'].iloc[-1])
        
        if is_bullish:
            tz = pytz.timezone('Asia/Bangkok')
            last_time = df.index[-1].astimezone(tz)
            return {
                "Ticker": ticker.replace('.BK', ''),
                "Price": float(df['Close'].iloc[-1]),
                "Status": "📈 Up Trend",
                "WT": round(float(df['wt1'].iloc[-1]), 2),
                "Last_Update": last_time.strftime("%H:%M")
            }
    except: pass
    return None

# 4. ส่วนแสดงผล Dashboard
st.subheader("🛡️ Guardian Swing: Broad Scan (Multi-index Fix)")

if st.button("🚀 Run Scan Now", use_container_width=True):
    results = []
    log_area = st.empty()
    progress_bar = st.progress(0)
    
    total = len(full_scan_list)
    for i, t in enumerate(full_scan_list):
        res = analyze_broad_v3(t)
        if res: results.append(res)
        
        # แสดง Log การทำงาน
        log_area.markdown(f'<div class="debug-log">Scanning: {t} | Found: {len(results)}</div>', unsafe_allow_html=True)
        progress_bar.progress((i + 1) / total)
    
    progress_bar.empty()
    
    if results:
        st.success(f"พบหุ้นที่มีทรงเป็นขาขึ้นทั้งหมด {len(results)} ตัว")
        df_display = pd.DataFrame(results).sort_values("Ticker")
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.warning("ไม่พบหุ้นที่เข้าเงื่อนไขในขณะนี้ ลองตรวจสอบการเชื่อมต่ออินเทอร์เน็ตครับ")

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Trading Systems")
