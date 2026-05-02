import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="Guardian Swing Mobile", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    .main { background-color: #0f172a; }
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 12px; border-radius: 8px;
        text-align: center; font-size: 13px; margin-bottom: 15px; border: 1px solid #334155;
        font-weight: bold;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 12px !important; }
    [data-testid="stDataFrame"] td { font-size: 12px !important; text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น (SET100 + Extra Growth)
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

# 3. ฟังก์ชันวิเคราะห์ Logic หลัก
def analyze_guardian_mobile(ticker):
    try:
        df = yf.download(ticker, period="90d", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 50: return None
        df = df.dropna()

        # Indicators
        df['hma'] = ta.hma(df['Close'], length=24)
        df['ema21'] = ta.ema(df['Close'], length=21)
        df['vma5'] = ta.sma(df['Volume'], length=5)
        
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa = ta.ema(ap, length=10)
        d = ta.ema(abs(ap - esa), length=10)
        ci = (ap - esa) / (0.015 * d)
        df['wt1'] = ta.ema(ci, length=21)
        df['wt2'] = ta.sma(df['wt1'], length=4)
        df = df.dropna()

        # Logic Conditions
        df['hull_up'] = df['hma'] > df['hma'].shift(1)
        df['wt_cross'] = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2'])
        df['vol_ok'] = df['Volume'] >= (df['vma5'] * 1.2)
        
        # BUY Condition
        df['buy_signal'] = df['hull_up'] & df['wt_cross'] & (df['wt1'] < -45) & df['vol_ok'] & (df['Close'] > df['ema21'])
        
        signals = df[df['buy_signal']].copy()
        if not signals.empty:
            last_sig = signals.iloc[-1]
            tz = pytz.timezone('Asia/Bangkok')
            sig_time = last_sig.name.astimezone(tz)
            
            # ดึงราคาปิดแท่งก่อนหน้าสัญญาณ (เพื่อหา %Change)
            idx = df.index.get_loc(last_sig.name)
            prev_close = float(df['Close'].iloc[idx-1]) if idx > 0 else float(last_sig['Close'])
            curr_price = float(last_sig['Close'])
            pct_chg = ((curr_price - prev_close) / prev_close) * 100
            
            if sig_time > datetime.now(tz) - timedelta(days=60):
                return {
                    "Ticker": ticker.replace('.BK', ''),
                    "Prev": prev_close,
                    "Price": curr_price,
                    "%Chg": pct_chg,
                    "Signal": "🚀 BUY",
                    "Time/Date": sig_time.strftime("%H:%M %d/%m"),
                    "raw_time": sig_time
                }
    except: pass
    return None

# 4. ส่วน Dashboard UI
st.subheader("🛡️ Guardian Swing (Mobile Edition)")

if st.button("🔄 Refresh Scan", use_container_width=True):
    st.rerun()

@st.fragment(run_every="10m")
def dashboard_runtime():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 {datetime.now(tz).strftime("%H:%M:%S")} | Looking back 60 Days</div>', unsafe_allow_html=True)
    
    results = []
    bar = st.progress(0, text="Scanning...")
    
    total = len(full_scan_list)
    for i, t in enumerate(full_scan_list):
        res = analyze_guardian_mobile(t)
        if res: results.append(res)
        bar.progress((i + 1) / total)
    bar.empty()

    if results:
        df = pd.DataFrame(results).sort_values(by="raw_time", ascending=False).head(30)
        
        # จัดสไตล์ข้อมูลและใช้ .map แทน .applymap สำหรับ Pandas 2.x
        styled_df = df.drop(columns=['raw_time']).style.format({
            "Prev": "{:,.2f}", 
            "Price": "{:,.2f}", 
            "%Chg": "{:+.2f}%"
        }).map(
            lambda x: 'color: #10b981; font-weight: bold;', subset=['Signal']
        ).map(
            lambda x: 'color: #10b981;' if x > 0 else 'color: #ef4444;', subset=['%Chg']
        )
        
        st.dataframe(
            styled_df,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=75),
                "Prev": st.column_config.NumberColumn("Prev", width=60),
                "Price": st.column_config.NumberColumn("Price", width=60),
                "%Chg": st.column_config.TextColumn("%Chg", width=65),
                "Signal": st.column_config.TextColumn("Signal", width=70),
                "Time/Date": st.column_config.TextColumn("Time/Date", width=100),
            },
            use_container_width=True, height=650, hide_index=True
        )
    else:
        st.info("🔎 No Signal Found (60D)")

dashboard_runtime()
st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Stable Release")
