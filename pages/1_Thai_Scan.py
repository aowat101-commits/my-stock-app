import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz

# 1. Page Configuration
st.set_page_config(page_title="Guardian Mobile", layout="wide")
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
full_scan_list = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'KBANK.BK', 'PTT.BK', 'SCB.BK', 'GULF.BK', 'HANA.BK', 'KCE.BK', 'JTS.BK', 'DITTO.BK', 'COCOCO.BK', 'MASTER.BK', 'AMATA.BK', 'AP.BK', 'BEM.BK', 'GUNKUL.BK', 'ICHI.BK']

# 3. Core Function
def analyze_guardian_final(ticker):
    try:
        df = yf.download(ticker, period="90d", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 50: return None
        df = df.dropna()

        df['hma'] = ta.hma(df['Close'], length=24)
        df['ema21'] = ta.ema(df['Close'], length=21)
        df['vma5'] = ta.sma(df['Volume'], length=5)
        wt = ta.wavetrend(df['High'], df['Low'], df['Close'])
        df['wt1'], df['wt2'] = wt.iloc[:, 0], wt.iloc[:, 1]
        df = df.dropna()

        # Buy Signal Logic
        df['buy_sig'] = (df['hma'] > df['hma'].shift(1)) & \
                        (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2']) & \
                        (df['wt1'] < -45) & (df['Volume'] >= ta.sma(df['Volume'], 5)*1.2) & \
                        (df['Close'] > ta.ema(df['Close'], 21))
        
        signals = df[df['buy_sig']].copy()
        if not signals.empty:
            last_sig = signals.iloc[-1]
            tz = pytz.timezone('Asia/Bangkok')
            sig_time = last_sig.name.astimezone(tz)
            
            if sig_time > datetime.now(tz) - timedelta(days=60):
                curr_price = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                pct_chg = ((curr_price - prev_close) / prev_close) * 100
                
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

# 4. Display
st.subheader("🛡️ Guardian Swing (Mobile)")
if st.button("🔄 Refresh", use_container_width=True): st.rerun()

@st.fragment(run_every="10m")
def runtime():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Sync: {datetime.now(tz).strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
    results = [analyze_guardian_final(t) for t in full_scan_list if analyze_guardian_final(t)]
    
    if results:
        df = pd.DataFrame(results).sort_values("raw_time", ascending=False).head(30)
        styled = df.drop(columns=['raw_time']).style.format({"Prev": "{:,.2f}", "Price": "{:,.2f}", "%Chg": "{:+.2f}%"}).map(
            lambda x: 'color: #10b981; font-weight: bold;', subset=['Signal']
        ).map(lambda x: 'color: #10b981;' if x > 0 else 'color: #ef4444;', subset=['%Chg'])
        
        st.dataframe(styled, column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width=70),
            "Prev": st.column_config.NumberColumn("Prev", width=60),
            "Price": st.column_config.NumberColumn("Price", width=60),
            "%Chg": st.column_config.TextColumn("%Chg", width=65),
            "Signal": st.column_config.TextColumn("Signal", width=70),
            "Time/Date": st.column_config.TextColumn("Time/Date", width=90),
        }, use_container_width=True, hide_index=True)
    else:
        st.info("No signals found.")

runtime()
