import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP ---
st.set_page_config(page_title="Guardian Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }
    .stDataFrame [data-testid="stTable"] td, .stDataFrame [data-testid="stTable"] th {
        color: #000000 !important; background-color: #ffffff !important;
        font-weight: 500 !important; border: 1px solid #e2e8f0 !important;
    }
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 10px; border-radius: 8px;
        text-align: center; font-size: 13px; margin-bottom: 20px; border: 1px solid #334155; font-weight: bold;
    }
    .header-box { display: flex; justify-content: center; align-items: center; gap: 12px; padding: 15px 0; }
    .header-text { color: white; font-size: 28px; font-weight: bold; margin: 0; }
    .flag-img { width: 42px; height: auto; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. UNIVERSAL NAVIGATION ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Thai Scan'

nav_col = st.columns([1,1,1,1,1])
pages = [("🏠 Home", "Home"), ("📈 Thai Scan", "Thai Scan"), ("📊 Thai Charts", "Thai Charts"), ("🇺🇸 US Scan", "US Scan"), ("📉 US Charts", "US Charts")]

for i, (label, page_id) in enumerate(pages):
    with nav_col[i]:
        if st.button(label, use_container_width=True, type="primary" if st.session_state.current_page == page_id else "secondary"):
            st.session_state.current_page = page_id

# --- 3. SCAN ENGINE ---
@st.cache_data(ttl=300)
def fetch_data(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 30: return None
        df = df.dropna()
        df['hma'] = ta.hma(df['Close'], 24)
        df['ema8'] = ta.ema(df['Close'], 8)
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa, d = ta.ema(ap, 10), ta.ema(abs(ap - ta.ema(ap, 10)), 10)
        ci = (ap - esa) / (0.015 * d)
        df['wt1'], df['wt2'] = ta.ema(ci, 21), ta.sma(ta.ema(ci, 21), 4)
        buy_c = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2']) & (df['wt1'] < -50) & (df['Close'] > df['ema8'])
        sell_c = (df['wt1'].shift(1) > df['wt2'].shift(1)) & (df['wt1'] < df['wt2']) & (df['wt1'] > 48)
        sigs = df[buy_c | sell_c].copy()
        if not sigs.empty:
            last = sigs.iloc[-1]
            tz = pytz.timezone('Asia/Bangkok')
            curr = float(df['Close'].iloc[-1])
            prev = float(df['Close'].iloc[df.index.get_loc(last.name)-1]) if df.index.get_loc(last.name) > 0 else curr
            return {"Ticker": ticker.replace('.BK', ''), "Prev": prev, "Price": curr, "%Chg": ((curr - prev) / prev) * 100, "Signal": "▲ Deep Buy" if last.name in df[buy_c].index else "⚠️ P-Sell", "Time/Date": last.name.astimezone(tz).strftime("%H:%M %d/%m"), "raw_time": last.name.astimezone(tz)}
    except: pass
    return None

# --- 4. PAGE CONTENT ---
curr_p = st.session_state.current_page

if curr_p == "Thai Scan":
    st.markdown("""<div class="header-box"><img src="https://flagcdn.com/w80/th.png" class="flag-img"><p class="header-text">Thai Scan</p></div>""", unsafe_allow_html=True)
    st.markdown(f'<div class="time-status">🕒 {datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S")} | Guardian V6.2</div>', unsafe_allow_html=True)
    set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
    res = [fetch_data(t) for t in set100]
    res = [r for r in res if r]
    if res:
        df_m = pd.DataFrame(res).sort_values("raw_time", ascending=False).head(40)
        st.dataframe(df_m.drop(columns=['raw_time']), use_container_width=True, height=750, hide_index=True)

elif curr_p == "Home":
    st.markdown("<h2 style='text-align:center; color:white; margin-top:50px;'>🏡 Guardian Central Home</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div style='background-color:#1e293b; padding:20px; border-radius:15px; color:white;'><h3>⭐ Watchlist</h3>", unsafe_allow_html=True)
        for t in ['IONQ', 'IREN', 'PTT.BK', 'DELTA.BK']: st.write(f"🔍 {t}")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='background-color:#1e293b; padding:20px; border-radius:15px; color:white;'><h3>🏢 Company</h3><p>Por Piang Electric Plus Co., Ltd.</p></div>", unsafe_allow_html=True)

elif curr_p == "Thai Charts":
    st.markdown("<h2 style='text-align:center; color:white;'>📊 Thai Charts Analysis</h2>", unsafe_allow_html=True)
    t_input = st.text_input("ระบุชื่อหุ้นไทย (เช่น PTT.BK):", "PTT.BK")
    st.line_chart(yf.download(t_input, period="1mo")['Close'])

elif curr_p == "US Scan":
    st.markdown("""<div class="header-box"><img src="https://flagcdn.com/w80/us.png" class="flag-img"><p class="header-text">US Market Scan</p></div>""", unsafe_allow_html=True)
    us_list = ['IONQ', 'IREN', 'SMX', 'ONDS', 'NVDA', 'TSLA', 'MARA', 'MSTR']
    res_us = [fetch_data(t) for t in us_list]
    res_us = [r for r in res_us if r]
    if res_us: st.dataframe(pd.DataFrame(res_us).drop(columns=['raw_time']), use_container_width=True, hide_index=True)

elif curr_p == "US Charts":
    st.markdown("<h2 style='text-align:center; color:white;'>📉 US Charts Analysis</h2>", unsafe_allow_html=True)
    u_input = st.selectbox("เลือกหุ้น US:", ['IONQ', 'IREN', 'SMX', 'ONDS', 'NVDA'])
    st.line_chart(yf.download(u_input, period="1mo")['Close'])

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | V6.2 Full Content")
