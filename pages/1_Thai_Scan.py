import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz
import requests

# --- 1. LINE NOTIFY CONFIG ---
# ใส่ Token ของคุณมิลค์ที่นี่
LINE_TOKEN = "YOUR_LINE_NOTIFY_TOKEN"

def send_line_notify(message):
    if LINE_TOKEN == "YOUR_LINE_NOTIFY_TOKEN":
        return
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {LINE_TOKEN}'}
    data = {'message': message}
    try:
        requests.post(url, headers=headers, data=data)
    except:
        pass

# --- 2. UI SETUP (Loft Style) ---
st.set_page_config(page_title="Guardian Balanced Notify", layout="wide")
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

# --- 3. TICKERS ---
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

# --- 4. ENGINE LOGIC (Balanced & Stable) ---
def analyze_guardian_balanced(ticker):
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

        # Logic Flags
        df['hull_up'] = df['hma'] > df['hma'].shift(1)
        df['wt_cross_up'] = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2'])
        df['wt_cross_down'] = (df['wt1'].shift(1) > df['wt2'].shift(1)) & (df['wt1'] < df['wt2'])
        
        # 🟢 1. Deep Buy (WT < -50 + EMA 8)
        df['deep_buy'] = df['wt_cross_up'] & (df['wt1'] < -50) & (df['Close'] > df['ema8'])
        
        # 🟢 2. Standard Buy (WT < -45 + EMA 21 + Hull + Vol)
        df['std_buy'] = df['hull_up'] & df['wt_cross_up'] & (df['wt1'] < -45) & \
                        (df['Volume'] >= df['vma5'] * 1.2) & (df['Close'] > df['ema21'])
        
        # 🔴 3. Take Profit Sell (WT Red Cross > +48)
        df['tp_sell'] = df['wt_cross_down'] & (df['wt1'] > 48)

        # ค้นหาสัญญาณล่าสุด (Window Period)
        all_signals = df[df['deep_buy'] | df['std_buy'] | df['tp_sell']].copy()
        if not all_signals.empty:
            last_sig = all_signals.iloc[-1]
            
            # กำหนดประเภทสัญญาณ
            if last_sig['deep_buy']: sig_type = "🚀 DEEP BUY"
            elif last_sig['std_buy']: sig_type = "🚀 STD BUY"
            else: sig_type = "⚠️ SELL (TP)"
            
            tz = pytz.timezone('Asia/Bangkok')
            sig_time = last_sig.name.astimezone(tz)
            
            # ดึงข้อมูลราคา
            curr_price = float(df['Close'].iloc[-1])
            idx = df.index.get_loc(last_sig.name)
            prev_close = float(df['Close'].iloc[idx-1]) if idx > 0 else curr_price
            pct_chg = ((curr_price - prev_close) / prev_close) * 100
            
            if sig_time > datetime.now(tz) - timedelta(days=60):
                return {
                    "Ticker": ticker.replace('.BK', ''),
                    "Prev": prev_close,
                    "Price": curr_price,
                    "%Chg": pct_chg,
                    "Signal": sig_type,
                    "Time/Date": sig_time.strftime("%H:%M %d/%m"),
                    "raw_time": sig_time,
                    "WT_Lvl": float(last_sig['wt1'])
                }
    except: pass
    return None

# --- 5. RUNTIME & DASHBOARD ---
st.subheader("🛡️ Guardian Swing Balanced (3-Signal Edition)")

if 'alert_cache' not in st.session_state:
    st.session_state.alert_cache = {}

if st.button("🔄 Manual Refresh", use_container_width=True):
    st.session_state.alert_cache.clear()
    st.rerun()

@st.fragment(run_every="10m")
def dashboard():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Sync: {datetime.now(tz).strftime("%H:%M:%S")} | Mode: 3-Signal Balanced</div>', unsafe_allow_html=True)
    
    results = []
    bar = st.progress(0, text="Scanning Market...")
    total = len(full_scan_list)
    
    for i, t in enumerate(full_scan_list):
        res = analyze_guardian_balanced(t)
        if res:
            results.append(res)
            # Notification Logic
            alert_key = f"{res['Ticker']}_{res['Signal']}_{res['Time/Date']}"
            if alert_key not in st.session_state.alert_cache:
                msg = f"\n🛡️ Guardian {res['Signal']}\nStock: {res['Ticker']}\nPrice: {res['Price']:.2f}\nWT: {res['WT_Lvl']:.1f}\nTime: {res['Time/Date']}"
                send_line_notify(msg)
                st.session_state.alert_cache[alert_key] = True
        bar.progress((i + 1) / total)
    bar.empty()

    if results:
        df = pd.DataFrame(results).sort_values("raw_time", ascending=False).head(40)
        styled = df.drop(columns=['raw_time', 'WT_Lvl']).style.format({
            "Prev": "{:,.2f}", "Price": "{:,.2f}", "%Chg": "{:+.2f}%"
        }).map(lambda x: 'color: #10b981; font-weight: bold;' if "BUY" in str(x) else 'color: #ef4444; font-weight: bold;', subset=['Signal']
        ).map(lambda x: 'color: #10b981;' if x > 0 else 'color: #ef4444;', subset=['%Chg'])
        
        st.dataframe(styled, column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width=75),
            "Prev": st.column_config.NumberColumn("Prev", width=60),
            "Price": st.column_config.NumberColumn("Price", width=60),
            "%Chg": st.column_config.TextColumn("%Chg", width=65),
            "Signal": st.column_config.TextColumn("Signal", width=95),
            "Time/Date": st.column_config.TextColumn("Time/Date", width=100),
        }, use_container_width=True, height=700, hide_index=True)
    else:
        st.info("🔎 No Balanced Signals Found")

dashboard()
st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Stable Release v3.5 (Balanced)")
