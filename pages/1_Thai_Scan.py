import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="Guardian Swing: Full Debug Edition", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    .main { background-color: #0f172a; }
    .time-status {
        background-color: #1e293b; color: #38bdf8; padding: 12px; border-radius: 8px;
        text-align: center; font-size: 14px; margin-bottom: 15px; border: 1px solid #334155;
        font-weight: bold;
    }
    .debug-log {
        background-color: #1e293b; color: #94a3b8; padding: 10px; 
        border-radius: 5px; font-family: monospace; font-size: 11px;
        height: 150px; overflow-y: auto; border: 1px solid #334155; margin-bottom: 20px;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 12px !important; }
    [data-testid="stDataFrame"] td { font-size: 13px !important; text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น (SET100 + Extra Growth)
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

# 3. ฟังก์ชันคำนวณ Indicators
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

def get_wavetrend(df):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ta.ema(ap, length=10)
    d = ta.ema(abs(ap - esa), length=10)
    ci = (ap - esa) / (0.015 * d)
    wt1 = ta.ema(ci, length=21)
    wt2 = ta.sma(wt1, length=4)
    return wt1, wt2

# 4. ฟังก์ชันวิเคราะห์ (พร้อม Data Cleaning)
def analyze_stock(ticker):
    try:
        # ดึงข้อมูล 60 วัน (รายชั่วโมง)
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        
        # ป้องกัน Error ในรูป: ตรวจสอบข้อมูลเบื้องต้น
        if df.empty or len(df) < 30: return "No Data"
        
        # กำจัดค่า NaN/None ที่ Yahoo Finance อาจส่งมาไม่ครบ
        df = df.dropna()

        # คำนวณ Indicators
        df['hma'] = get_hma(df['Close'], 24)
        df['ema21'] = ta.ema(df['Close'], length=21)
        df['vma5'] = ta.sma(df['Volume'], length=5)
        wt1, wt2 = get_wavetrend(df)
        df['wt1'], df['wt2'] = wt1, wt2
        
        # ล้างค่า NaN ที่เกิดจากการคำนวณย้อนหลัง (Shift/EMA)
        df = df.dropna()

        # สร้างเงื่อนไข Logic (แบบ Flexible)
        df['hull_up'] = df['hma'] > df['hma'].shift(1)
        df['above_ema'] = df['Close'] > df['ema21']
        df['wt_cross'] = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2'])
        df['vol_ok'] = df['Volume'] >= df['vma5'] # วอลุ่มเท่ากับหรือมากกว่าค่าเฉลี่ย
        
        # รวมสัญญาณ (เน้น Hull เขียว + WT ตัดขึ้น)
        df['buy_signal'] = df['hull_up'] & df['wt_cross'] & df['above_ema']
        
        signals = df[df['buy_signal']].copy()
        
        if not signals.empty:
            last_sig = signals.iloc[-1]
            tz = pytz.timezone('Asia/Bangkok')
            sig_time = last_sig.name.astimezone(tz)
            
            return {
                "Ticker": ticker.replace('.BK', ''),
                "Price": float(last_sig['Close']),
                "Signal": "✅ BUY",
                "Date": sig_time.strftime("%d/%m %H:%M"),
                "WT": round(float(last_sig['wt1']), 2),
                "Vol": f"{round(float(last_sig['Volume']/last_sig['vma5']), 2)}x",
                "raw_time": sig_time
            }
        return "No Signal"
    except Exception as e:
        return f"Error: {str(e)}"

# 5. UI Dashboard
st.subheader("🛡️ Guardian Swing: Full Debug & Flexible Scan")

# ส่วนควบคุมการสแกน
col1, col2 = st.columns([1, 4])
with col1:
    start_btn = st.button("🚀 Start Scan", use_container_width=True)
with col2:
    st.info("ระบบจะดึงข้อมูลย้อนหลัง 60 วัน และกรองเฉพาะหุ้นที่มีสัญญาณ 'Hull เขียว + WT ตัดขึ้น' 30 อันดับล่าสุด")

if start_btn:
    log_area = st.empty()
    results = []
    debug_text = "🔍 Initializing Scanner...\n"
    
    # บาร์แสดงความคืบหน้า
    progress_bar = st.progress(0)
    total_stocks = len(full_scan_list)
    
    for i, ticker in enumerate(full_scan_list):
        res = analyze_stock(ticker)
        
        if isinstance(res, dict):
            results.append(res)
            debug_text += f"✅ {ticker}: Signal Found!\n"
        else:
            # ถ้าต้องการดูรายละเอียด Error ให้เปิดบรรทัดล่างนี้
            # debug_text += f"❌ {ticker}: {res}\n"
            pass
            
        # อัปเดต Log และ Progress
        log_area.markdown(f'<div class="debug-log">{debug_text}</div>', unsafe_allow_html=True)
        progress_bar.progress((i + 1) / total_stocks)
    
    progress_bar.empty()
    
    if results:
        st.success(f"การสแกนเสร็จสิ้น: พบหุ้นเข้าเงื่อนไขทั้งหมด {len(results)} ตัว")
        # เรียงตามเวลาล่าสุดและเลือก 30 แถว
        final_df = pd.DataFrame(results).sort_values(by="raw_time", ascending=False).head(30)
        
        st.dataframe(
            final_df.drop(columns=['raw_time']).style.format({"Price": "{:,.2f}"})
            .applymap(lambda x: 'color: #38bdf8; font-weight: bold;', subset=['Signal']),
            use_container_width=True, height=600, hide_index=True
        )
    else:
        st.warning("⚠️ สแกนครบแล้ว แต่ไม่พบหุ้นที่เข้าเงื่อนไขในรอบ 60 วัน")

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Stable Release v2.1")
