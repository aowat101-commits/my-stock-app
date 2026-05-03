import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP (Ultra Compact Focus) ---
st.set_page_config(page_title="Guardian Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    /* บังคับแบ่งครึ่งและลดช่องว่างระหว่างปุ่มให้เหลือน้อยที่สุด */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
    }
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }

    /* ตารางตัวหนังสือดำพื้นขาว */
    .stDataFrame [data-testid="stTable"] td, 
    .stDataFrame [data-testid="stTable"] th {
        color: #000000 !important;
        background-color: #ffffff !important;
        font-weight: 500 !important;
        font-size: 12px !important;
        padding: 4px !important;
    }

    /* บีบขนาดปุ่มให้เล็กที่สุดเพื่อไม่ให้ล้นจอ */
    .stButton > button {
        height: 32px !important;
        font-size: 10px !important;
        padding: 0px 2px !important;
        border-radius: 4px !important;
        margin-bottom: -18px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
    }

    .time-status {
        background-color: #1e293b; color: #10b981; padding: 2px; border-radius: 4px;
        text-align: center; font-size: 10px; margin: 2px 0; border: 1px solid #334155;
    }
    
    .header-box { display: flex; justify-content: center; align-items: center; gap: 4px; padding: 0px; }
    .header-text { color: white; font-size: 14px; font-weight: bold; margin: 0; }
    
    /* ลด Padding ของหน้าจอหลัก */
    .block-container { padding-top: 0.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. NAVIGATION (Ultra Compact) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Thai Scan'

# Home
if st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.current_page == 'Home' else "secondary"):
    st.session_state.current_page = 'Home'

# Thai Scan | Thai Charts
c1, c2 = st.columns(2)
with c1:
    if st.button("📈 ThaiScan", use_container_width=True, type="primary" if st.session_state.current_page == 'Thai Scan' else "secondary"):
        st.session_state.current_page = 'Thai Scan'
with c2:
    if st.button("📊 ThaiChart", use_container_width=True, type="primary" if st.session_state.current_page == 'Thai Charts' else "secondary"):
        st.session_state.current_page = 'Thai Charts'

# US Scan | US Charts
c3, c4 = st.columns(2)
with c3:
    if st.button("🇺🇸 US Scan", use_container_width=True, type="primary" if st.session_state.current_page == 'US Scan' else "secondary"):
        st.session_state.current_page = 'US Scan'
with c4:
    if st.button("📉 US Chart", use_container_width=True, type="primary" if st.session_state.current_page == 'US Charts' else "secondary"):
        st.session_state.current_page = 'US Charts'

# --- 3. ENGINE ---
@st.cache_data(ttl=300)
def fetch_stock(ticker):
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

# --- 4. CONTENT ---
cp = st.session_state.current_page

if cp == "Thai Scan":
    st.markdown("""<div class="header-box"><p class="header-text">🇹🇭 Thai Market</p></div>""", unsafe_allow_html=True)
    st.markdown(f'<div class="time-status">🕒 {datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S")} | V6.7</div>', unsafe_allow_html=True)
    set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
    res = [fetch_stock(t) for t in set100]
    res = [r for r in res if r]
    if res:
        df_m = pd.DataFrame(res).sort_values("raw_time", ascending=False).head(40)
        st.dataframe(df_m.drop(columns=['raw_time']), use_container_width=True, height=750, hide_index=True)

elif cp == "Home":
    st.info("Aowat Lukthong | PPE Co., Ltd.\nปรับขนาดปุ่มให้เล็กที่สุดเพื่อไม่ให้ล้นหน้าจอมือถือแล้วครับ")

elif cp == "Thai Charts":
    t_in = st.text_input("หุ้นไทย:", "PTT.BK")
    st.line_chart(yf.download(t_in, period="1mo")['Close'])

elif cp == "US Scan":
    us_res = [fetch_stock(t) for t in ['IONQ', 'IREN', 'NVDA', 'TSLA']]
    st.dataframe(pd.DataFrame([r for r in us_res if r]).drop(columns=['raw_time']), use_container_width=True)

elif cp == "US Charts":
    u_in = st.selectbox("หุ้น US:", ['IONQ', 'IREN', 'NVDA'])
    st.line_chart(yf.download(u_in, period="1mo")['Close'])

st.write("---")
st.caption("PPE | Ultra Compact v6.7")
