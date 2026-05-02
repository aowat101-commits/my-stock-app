import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# 1. UI Setup
st.set_page_config(page_title="Guardian Swing: Broad Scan", layout="wide")
st.markdown("""<style>.main { background-color: #0f172a; } .debug-log { background-color: #1e293b; color: #94a3b8; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 11px; height: 100px; overflow-y: auto; border: 1px solid #334155; }</style>""", unsafe_allow_html=True)

# 2. Ticker List
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

# 3. Helper Functions
def get_hma(series, length):
    wma = lambda d, p: d.rolling(p).apply(lambda x: np.dot(x, np.arange(1, p + 1)) / np.arange(1, p + 1).sum(), raw=True)
    return wma(2 * wma(series, int(length/2)) - wma(series, length), int(np.sqrt(length)))

def get_wavetrend(df):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ta.ema(ap, length=10)
    d = ta.ema(abs(ap - esa), length=10)
    ci = (ap - esa) / (0.015 * d)
    wt1 = ta.ema(ci, length=21)
    return wt1, ta.sma(wt1, length=4)

# 4. Scanner Function
def analyze_broad(ticker):
    try:
        df = yf.download(ticker, period="10d", interval="1h", progress=False).dropna()
        if len(df) < 25: return None
        
        df['hma'] = get_hma(df['Close'], 24)
        df['ema21'] = ta.ema(df['Close'], length=21)
        wt1, wt2 = get_wavetrend(df)
        df['wt1'], df['wt2'] = wt1, wt2
        df = df.dropna()

        # เงื่อนไข Broad Scan: ขอแค่ทรงเป็นขาขึ้น
        is_bullish = (df['Close'] > df['ema21']) & (df['hma'] > df['hma'].shift(1)) & (df['wt1'] > df['wt2'])
        
        if is_bullish.iloc[-1]: # เช็คว่าแท่งล่าสุดยัง Bullish อยู่ไหม
            return {
                "Ticker": ticker.replace('.BK', ''),
                "Price": float(df['Close'].iloc[-1]),
                "Status": "📈 Bullish Trend",
                "WT": round(float(df['wt1'].iloc[-1]), 2),
                "Time": df.index[-1].strftime("%H:%M")
            }
    except: pass
    return None

# 5. Execution
st.subheader("🛡️ Guardian Swing: Broad Bullish Scan")
if st.button("🚀 Run Broad Scan", use_container_width=True):
    results = []
    log = st.empty()
    progress = st.progress(0)
    
    for i, t in enumerate(full_scan_list):
        res = analyze_broad(t)
        if res: results.append(res)
        log.markdown(f'<div class="debug-log">Scanning: {t} ({len(results)} found)</div>', unsafe_allow_html=True)
        progress.progress((i + 1) / len(full_scan_list))
    
    if results:
        st.dataframe(pd.DataFrame(results).sort_values("Ticker"), use_container_width=True, hide_index=True)
    else:
        st.warning("ยังไม่พบหุ้นที่เป็นขาขึ้นชัดเจนในขณะนี้")
