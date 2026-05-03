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
    /* ซ่อนส่วนประกอบมาตรฐาน */
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    
    .stApp { background-color: #0f172a; }

    /* บังคับสีตาราง (ตัวหนังสือเข้มบนพื้นขาว) */
    .stDataFrame [data-testid="stTable"] td, 
    .stDataFrame [data-testid="stTable"] th {
        color: #111827 !important;
        background-color: #ffffff !important;
        font-weight: 500;
    }
    
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 10px; border-radius: 8px;
        text-align: center; font-size: 13px; margin-bottom: 20px; border: 1px solid #334155;
        font-weight: bold;
    }
    
    .header-box {
        display: flex; justify-content: center; align-items: center;
        gap: 12px; padding: 10px 0;
    }
    .header-text { color: white; font-size: 28px; font-weight: bold; margin: 0; }
    .flag-img { width: 42px; height: auto; border-radius: 4px; }

    /* สไตล์ปุ่มนำทาง (Navigation Buttons) */
    .stButton > button {
        border-radius: 8px !important;
        height: 45px !important;
        font-weight: bold !important;
        border: 1px solid #334155 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FAST NAVIGATION LOGIC ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Thai Scan'

# สร้างปุ่มนำทางด้านบนพร้อมระบบแสดงสถานะ Active
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1,1,1,1])

with nav_col1:
    btn_home = st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.current_page == 'Home' else "secondary")
    if btn_home: st.session_state.current_page = 'Home'
with nav_col2:
    btn_thai = st.button("📈 Thai Scan", use_container_width=True, type="primary" if st.session_state.current_page == 'Thai Scan' else "secondary")
    if btn_thai: st.session_state.current_page = 'Thai Scan'
with nav_col3:
    btn_charts = st.button("📊 Charts", use_container_width=True, type="primary" if st.session_state.current_page == 'Charts' else "secondary")
    if btn_charts: st.session_state.current_page = 'Charts'
with nav_col4:
    btn_us = st.button("🇺🇸 US Scan", use_container_width=True, type="primary" if st.session_state.current_page == 'US Scan' else "secondary")
    if btn_us: st.session_state.current_page = 'US Scan'

# --- 3. SCAN ENGINE ---
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
        
        buy_d = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2']) & (df['wt1'] < -50) & (df['Close'] > df['ema8'])
        sell_p = (df['wt1'].shift(1) > df['wt2'].shift(1)) & (df['wt1'] < df['wt2']) & (df['wt1'] > 48)

        all_sig = df[buy_d | sell_p].copy()
        if not all_sig.empty:
            last = all_sig.iloc[-1]
            tz = pytz.timezone('Asia/Bangkok')
            curr = float(df['Close'].iloc[-1])
            prev = float(df['Close'].iloc[df.index.get_loc(last.name)-1]) if df.index.get_loc(last.name) > 0 else curr
            return {
                "Ticker": ticker.replace('.BK', ''), "Prev": prev, "Price": curr, 
                "%Chg": ((curr - prev) / prev) * 100,
                "Signal": "▲ Deep Buy" if last.name in df[buy_d].index else "⚠️ P-Sell",
                "Time/Date": last.name.astimezone(tz).strftime("%H:%M %d/%m"),
                "raw_time": last.name.astimezone(tz)
            }
    except: pass
    return None

# --- 4. DISPLAY CONTENT ---

if st.session_state.current_page == "Thai Scan":
    st.markdown("""
        <div class="header-box">
            <img src="https://flagcdn.com/w80/th.png" class="flag-img">
            <p class="header-text">Thai scan</p>
        </div>
        """, unsafe_allow_html=True)
    
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 {datetime.now(tz).strftime("%H:%M:%S")} | Guardian V5.9</div>', unsafe_allow_html=True)
    
    set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
    extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
    full_list = list(set(set100 + extra_growth))

    results = [fetch_stock(t) for t in full_list]
    results = [r for r in results if r]

    if results:
        df_m = pd.DataFrame(results).sort_values("raw_time", ascending=False).head(40)
        df_final = df_m.drop(columns=['raw_time']).reset_index(drop=True)

        def style_logic(row):
            m = df_m[df_m['Ticker'] == row['Ticker']].iloc[0]
            sig_c = '#0d9488' if "▲" in m['Signal'] else '#dc2626'
            val_c = '#059669' if m['%Chg'] > 0 else ('#dc2626' if m['%Chg'] < 0 else '#374151')
            return [f'color: {sig_c}; font-weight:bold;', 'color: #374151;', f'color: {val_c}; font-weight:bold;', f'color: {val_c};', f'color: {sig_c}; font-weight:bold;', 'color: #374151;']

        st.dataframe(df_final.style.format({"Prev":"{:.2f}","Price":"{:.2f}","%Chg":"{:.2f}%"}).apply(style_logic, axis=1), 
                     use_container_width=True, height=750, hide_index=True)

elif st.session_state.current_page == "Home":
    st.markdown("<h2 style='text-align:center; color:white; margin-top:50px;'>🏡 Home Dashboard</h2>", unsafe_allow_html=True)
    
    # เพิ่มตารางสรุปในหน้า Home
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div style='background-color:#1e293b; padding:20px; border-radius:15px;'>", unsafe_allow_html=True)
        st.subheader("⭐ My Watchlist")
        fav_stocks = ['PTT.BK', 'SCB.BK', 'DELTA.BK', 'ADVANC.BK']
        fav_results = [fetch_stock(t) for t in fav_stocks]
        fav_results = [r for r in fav_results if r]
        if fav_results:
            st.table(pd.DataFrame(fav_results).drop(columns=['raw_time']))
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<div style='background-color:#1e293b; padding:20px; border-radius:15px;'>", unsafe_allow_html=True)
        st.subheader("🏢 Corporate Info")
        st.write("**Company:** Por Piang Electric Plus Co., Ltd. (PPE)")
        st.write("**Focus:** Electrical Installation, PLC Systems, Maintenance")
        st.write("**Area:** Nakhon Pathom / Nonthaburi")
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.current_page == "Charts":
    st.markdown("<h2 style='text-align:center; color:white; margin-top:100px;'>📊 Charts Analytics</h2>", unsafe_allow_html=True)

elif st.session_state.current_page == "US Scan":
    st.markdown("<h2 style='text-align:center; color:white; margin-top:100px;'>🇺🇸 US Market Scan</h2>", unsafe_allow_html=True)

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Stable Dash v5.9")
