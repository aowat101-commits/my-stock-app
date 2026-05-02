import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="Guardian Swing: 2-Month Deep Scan", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    .main { background-color: #0f172a; }
    .time-status {
        background-color: #1e293b; color: #fbbf24; padding: 12px; border-radius: 8px;
        text-align: center; font-size: 14px; margin-bottom: 15px; border: 1px solid #334155;
        font-weight: bold;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 12px !important; }
    [data-testid="stDataFrame"] td { font-size: 13px !important; text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น (SET100 + Extra Growth/MAI)
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

# 3. ฟังก์ชันคำนวณ HMA และ WaveTrend
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

def get_wavetrend(df, n1=10, n2=21):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ta.ema(ap, length=n1)
    d = ta.ema(abs(ap - esa), length=n1)
    ci = (ap - esa) / (0.015 * d)
    tci = ta.ema(ci, length=n2)
    wt1 = tci
    wt2 = ta.sma(wt1, length=4)
    return wt1, wt2

# 4. ฟังก์ชันวิเคราะห์ย้อนหลัง 60 วัน
def analyze_guardian_60d(ticker):
    try:
        # ดึงข้อมูลรายชั่วโมงย้อนหลัง 90 วัน เพื่อให้ครอบคลุม 60 วันทำการ
        df = yf.download(ticker, period="90d", interval="1h", progress=False)
        if len(df) < 50: return None

        tz = pytz.timezone('Asia/Bangkok')
        df['ema8'] = ta.ema(df['Close'], length=8)
        df['ema20'] = ta.ema(df['Close'], length=20)
        df['hma30'] = get_hma(df['Close'], 30)
        df['vma5'] = ta.sma(df['Volume'], length=5)
        wt1, wt2 = get_wavetrend(df)
        df['wt1'], df['wt2'] = wt1, wt2

        # เงื่อนไข Logic
        df['trend_up'] = df['hma30'] > df['hma30'].shift(1)
        df['above_ema'] = (df['Close'] > df['ema8']) & (df['Close'] > df['ema20'])
        df['wt_cross_up'] = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2'])
        df['vol_ok'] = df['Volume'] > (df['vma5'] * 1.5)
        
        # ค้นหา BUY Signal
        df['buy_signal'] = (df['above_ema']) & (df['trend_up']) & (df['wt_cross_up']) & (df['wt1'] < -53) & (df['vol_ok'])
        
        cutoff = datetime.now(tz) - timedelta(days=60)
        signals = df[df['buy_signal']].copy()
        
        if not signals.empty:
            last_sig = signals.iloc[-1]
            sig_time = last_sig.name.astimezone(tz)
            
            if sig_time > cutoff:
                return {
                    "Ticker": ticker.replace('.BK', ''),
                    "Price": last_sig['Close'],
                    "Signal": "🚀 BUY",
                    "Date": sig_time.strftime("%d/%m/%y %H:%M"),
                    "WT": round(last_sig['wt1'], 2),
                    "Vol_Force": f"{round(last_sig['Volume'] / last_sig['vma5'], 2)}x",
                    "raw_time": sig_time
                }
    except: return None
    return None

# 5. UI ส่วนควบคุม
st.subheader("🛰️ Guardian Swing: 2-Month Deep History Scan")

if st.button("🔄 Start Deep Scan (60 Days)", use_container_width=True):
    st.rerun()

# 6. Dashboard Runtime
@st.fragment(run_every="10m")
def deep_runtime():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Deep Scanning: {datetime.now(tz).strftime("%H:%M:%S")} | Looking back 60 Days</div>', unsafe_allow_html=True)
    
    results = []
    bar = st.progress(0, text="กำลังขุดประวัติสัญญาณย้อนหลัง 2 เดือน...")
    
    total = len(full_scan_list)
    for i, t in enumerate(full_scan_list):
        res = analyze_guardian_60d(t)
        if res: results.append(res)
        bar.progress((i + 1) / total)
    bar.empty()

    if results:
        df = pd.DataFrame(results).sort_values(by="raw_time", ascending=False).head(30)
        st.dataframe(
            df.drop(columns=['raw_time']).style.format({"Price": "{:,.2f}"})
            .applymap(lambda x: 'color: #10b981; font-weight: bold;', subset=['Signal']),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=80),
                "Price": st.column_config.NumberColumn("Entry Price", width=90),
                "Signal": st.column_config.TextColumn("Signal", width=80),
                "Date": st.column_config.TextColumn("Signal Date", width=120),
                "WT": st.column_config.NumberColumn("WT Level", width=70),
                "Vol_Force": st.column_config.TextColumn("Vol Force", width=80),
            },
            use_container_width=True, height=650, hide_index=True
        )
    else:
        st.info("🔎 ไม่พบหุ้นที่เกิดสัญญาณสมบูรณ์แบบในช่วง 2 เดือนที่ผ่านมา")

deep_runtime()
st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Portfolio Strategy Analysis")
