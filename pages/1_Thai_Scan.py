import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz

# --- 1. UI SETUP ---
st.set_page_config(page_title="Guardian Swing Dashboard", layout="wide")
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
    </style>
    """, unsafe_allow_html=True)

# --- 2. TICKERS ---
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

# --- 3. CORE ENGINE ---
def analyze_guardian_v3_7(ticker):
    try:
        df = yf.download(ticker, period="90d", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 50: return None
        df = df.dropna()

        # Indicators
        df['hma'] = ta.hma(df['Close'], length=24)
        df['ema8'] = ta.ema(df['Close'], length=8)
        df['ema21'] = ta.ema(df['Close'], length=21)
        df['vma5'] = ta.sma(df['Volume'], length=5)
        
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa = ta.ema(ap, length=10)
        d = ta.ema(abs(ap - esa), length=10)
        ci = (ap - esa) / (0.015 * d)
        df['wt1'] = ta.ema(ci, length=21)
        df['wt2'] = ta.sma(df['wt1'], length=4)
        df = df.dropna()

        # Signal Logic
        df['wt_cross_up'] = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2'])
        df['wt_cross_down'] = (df['wt1'].shift(1) > df['wt2'].shift(1)) & (df['wt1'] < df['wt2'])
        df['hull_up'] = df['hma'] > df['hma'].shift(1)
        
        df['buy_deep'] = df['wt_cross_up'] & (df['wt1'] < -50) & (df['Close'] > df['ema8'])
        df['buy_std'] = df['hull_up'] & df['wt_cross_up'] & (df['wt1'] < -45) & (df['Volume'] >= df['vma5']*1.2) & (df['Close'] > df['ema21'])
        df['sell_p'] = df['wt_cross_down'] & (df['wt1'] > 48)

        all_sig = df[df['buy_deep'] | df['buy_std'] | df['sell_p']].copy()
        if not all_sig.empty:
            last_sig = all_sig.iloc[-1]
            sig_label = "▲ Deep Buy" if last_sig['buy_deep'] else ("🚀 Buy" if last_sig['buy_std'] else "⚠️ P-Sell")
            
            tz = pytz.timezone('Asia/Bangkok')
            sig_time = last_sig.name.astimezone(tz)
            
            if sig_time > datetime.now(tz) - timedelta(days=60):
                curr_price = float(df['Close'].iloc[-1])
                idx = df.index.get_loc(last_sig.name)
                
                prev_close = float(df['Close'].iloc[idx-1]) if idx > 0 else curr_price
                prev_prev_close = float(df['Close'].iloc[idx-2]) if idx > 1 else prev_close
                
                return {
                    "Ticker": ticker.replace('.BK', ''),
                    "Prev": prev_close,
                    "Price": curr_price,
                    "%Chg": ((curr_price - prev_close) / prev_close) * 100,
                    "Signal": sig_label,
                    "Time/Date": sig_time.strftime("%H:%M %d/%m"),
                    "raw_time": sig_time,
                    "prev_diff": prev_close - prev_prev_close 
                }
    except: pass
    return None

# --- 4. DASHBOARD RUNTIME ---
st.subheader("🛡️ Guardian Balanced Dashboard (v3.7)")

if st.button("🔄 Refresh Market", use_container_width=True):
    st.rerun()

@st.fragment(run_every="10m")
def dashboard():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 {datetime.now(tz).strftime("%H:%M:%S")} | Strategy: Independent Color Verification</div>', unsafe_allow_html=True)
    
    results = []
    for t in full_scan_list:
        res = analyze_guardian_v3_7(t)
        if res: results.append(res)

    if results:
        df_master = pd.DataFrame(results).sort_values("raw_time", ascending=False).head(40)
        df_display = df_master.drop(columns=['raw_time', 'prev_diff']).reset_index(drop=True)

        def apply_independent_styles(row):
            ticker = row['Ticker']
            m_row = df_master[df_master['Ticker'] == ticker].iloc[0]
            
            # 1. สี SIGNAL (Ticker, Signal, Time)
            sig = m_row['Signal']
            sig_c = '#4fd1c5' if "▲" in sig else ('#10b981' if "🚀" in sig else '#ef4444')
            
            # 2. สี PREV (Prev) - แยกอิสระ
            p_diff = m_row['prev_diff']
            prev_c = 'color: #10b981;' if p_diff > 0 else ('color: #ef4444;' if p_diff < 0 else '')
            
            # 3. สี PRICE (Price, %Chg) - แยกอิสระ
            pct = m_row['%Chg']
            price_c = 'color: #10b981;' if pct > 0 else ('color: #ef4444;' if pct < 0 else '')
            
            return [
                f'color: {sig_c}', # Ticker
                prev_c,            # Prev
                price_c,           # Price
                price_c,           # %Chg
                f'color: {sig_c}', # Signal
                f'color: {sig_c}'  # Time/Date
            ]

        styled = df_display.style.format({
            "Prev": "{:,.2f}", "Price": "{:,.2f}", "%Chg": "{:+.2f}%"
        }).apply(apply_independent_styles, axis=1)

        st.dataframe(styled, column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width=75),
            "Prev": st.column_config.NumberColumn("Prev", width=60),
            "Price": st.column_config.NumberColumn("Price", width=60),
            "%Chg": st.column_config.TextColumn("%Chg", width=65),
            "Signal": st.column_config.TextColumn("Signal", width=105),
            "Time/Date": st.column_config.TextColumn("Time/Date", width=100),
        }, use_container_width=True, height=700, hide_index=True)
    else:
        st.info("🔎 ไม่พบสัญญาณใหม่")

dashboard()
st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Verified Independent Color Release")
