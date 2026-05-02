import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz

# 1. Setup & Styling
st.set_page_config(page_title="Guardian Mobile Stable", layout="wide")
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    .main { background-color: #0f172a; }
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 12px; border-radius: 8px;
        text-align: center; font-size: 13px; margin-bottom: 15px; border: 1px solid #334155; font-weight: bold;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 12px !important; }
    [data-testid="stDataFrame"] td { font-size: 12px !important; text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Tickers (SET100 + Extra)
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

# 3. Stable Scanner Function
def analyze_stable_v33(ticker):
    try:
        # ใช้ข้อมูลรายวันเพื่อให้ข้อมูลสมบูรณ์ที่สุด
        df = yf.download(ticker, period="120d", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 40: return None
        df = df.dropna()

        # Indicators
        df['hma'] = ta.hma(df['Close'], length=24)
        df['ema21'] = ta.ema(df['Close'], length=21)
        wt = ta.wavetrend(df['High'], df['Low'], df['Close'])
        df['wt1'], df['wt2'] = wt.iloc[:, 0], wt.iloc[:, 1]
        
        # Conditions
        df['hull_up'] = df['hma'] > df['hma'].shift(1)
        df['wt_cross'] = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2'])
        df['above_ema'] = df['Close'] > df['ema21']
        
        # สัญญาณพิจารณาซื้อ: WT ตัดขึ้นใน 10 วันล่าสุด และทรงปัจจุบันยังเป็น Bullish
        df['valid_signal'] = df['wt_cross'].rolling(window=10).max().astype(bool) & \
                             df['hull_up'] & df['above_ema']
        
        signals = df[df['valid_signal']].copy()
        if not signals.empty:
            last_sig = signals.iloc[-1]
            tz = pytz.timezone('Asia/Bangkok')
            sig_time = last_sig.name.astimezone(tz)
            
            curr_price = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            pct_chg = ((curr_price - prev_close) / prev_close) * 100
            
            return {
                "Ticker": ticker.replace('.BK', ''),
                "Prev": prev_close,
                "Price": curr_price,
                "%Chg": pct_chg,
                "Signal": "🚀 BUY",
                "Time/Date": sig_time.strftime("%d/%m"),
                "raw_time": sig_time
            }
    except: pass
    return None

# 4. Display Logic
st.subheader("🛡️ Guardian Swing (Mobile Stable)")

if st.button("🔄 Full Market Scan", use_container_width=True):
    st.rerun()

@st.fragment(run_every="15m")
def dashboard_runtime():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Sync: {datetime.now(tz).strftime("%H:%M:%S")} | Looking back 10 Days Signal</div>', unsafe_allow_html=True)
    
    results = []
    bar = st.progress(0, text="สแกนข้อมูลรายวัน...")
    for i, t in enumerate(full_scan_list):
        res = analyze_stable_v33(t)
        if res: results.append(res)
        bar.progress((i + 1) / len(full_scan_list))
    bar.empty()

    if results:
        df = pd.DataFrame(results).sort_values("raw_time", ascending=False).head(40)
        styled = df.drop(columns=['raw_time']).style.format({
            "Prev": "{:,.2f}", "Price": "{:,.2f}", "%Chg": "{:+.2f}%"
        }).map(lambda x: 'color: #10b981; font-weight: bold;', subset=['Signal']) \
          .map(lambda x: 'color: #10b981;' if x > 0 else 'color: #ef4444;', subset=['%Chg'])
        
        st.dataframe(styled, column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width=80),
            "Prev": st.column_config.NumberColumn("Prev", width=65),
            "Price": st.column_config.NumberColumn("Price", width=65),
            "%Chg": st.column_config.TextColumn("%Chg", width=70),
            "Signal": st.column_config.TextColumn("Signal", width=80),
            "Time/Date": st.column_config.TextColumn("Date", width=70),
        }, use_container_width=True, height=700, hide_index=True)
    else:
        st.info("ไม่พบสัญญาณในเงื่อนไขปัจจุบัน")

dashboard_runtime()
