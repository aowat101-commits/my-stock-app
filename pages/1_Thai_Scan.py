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
    /* ซ่อนส่วนประกอบมาตรฐานที่ไม่ได้ใช้ */
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebarCollapsedControl"] { display: none !important; } /* ซ่อนลูกศรเจ้าปัญหา */
    
    .stApp { background-color: #0f172a; }

    /* สร้างแถบนำทางลอยตัว (Floating Nav Bar) */
    .floating-nav {
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 9999;
        display: flex;
        gap: 10px;
    }

    /* สไตล์ปุ่มลอย */
    .nav-btn {
        background-color: #1e293b;
        color: #10b981;
        border: 1px solid #334155;
        padding: 8px 15px;
        border-radius: 8px;
        font-weight: bold;
        text-decoration: none;
        font-size: 14px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }

    /* บังคับสีตัวหนังสือในตารางให้อ่านออก 100% */
    .stDataFrame div {
        color: #1e293b !important; /* บังคับเข้ม */
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
    </style>
    """, unsafe_allow_html=True)

# --- 2. CUSTOM NAVIGATION (ปุ่มลอยแทน Sidebar) ---
# ใช้ Session State เก็บค่าหน้าปัจจุบัน
if 'page' not in st.session_state:
    st.session_state.page = 'Thai Scan'

# สร้างปุ่มกดเปลี่ยนหน้าจริงๆ ด้วย Streamlit Columns ที่มุมบน
col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 8])
with col_nav1:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = 'Home'
with col_nav2:
    if st.button("📊 Charts", use_container_width=True):
        st.session_state.page = 'Thai Charts'

# --- 3. SCAN ENGINE ---
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

@st.cache_data(ttl=300)
def scan_stock(ticker):
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

# --- 4. DISPLAY ---
if st.session_state.page == "Thai Scan":
    st.markdown("""
        <div class="header-box">
            <img src="https://flagcdn.com/w80/th.png" class="flag-img">
            <p class="header-text">Thai scan</p>
        </div>
        """, unsafe_allow_html=True)
    
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 {datetime.now(tz).strftime("%H:%M:%S")} | Guardian V5.5</div>', unsafe_allow_html=True)
    
    results = [scan_stock(t) for t in full_scan_list]
    results = [r for r in results if r]

    if results:
        df_m = pd.DataFrame(results).sort_values("raw_time", ascending=False).head(40)
        df_final = df_m.drop(columns=['raw_time']).reset_index(drop=True)

        def style_rows(row):
            m = df_m[df_m['Ticker'] == row['Ticker']].iloc[0]
            sig_c = '#0d9488' if "▲" in m['Signal'] else '#dc2626'
            val_c = '#059669' if m['%Chg'] > 0 else ('#dc2626' if m['%Chg'] < 0 else '#1f2937')
            return [f'color: {sig_c}; font-weight:bold;', 'color: #1f2937;', f'color: {val_c};', f'color: {val_c};', f'color: {sig_c}; font-weight:bold;', 'color: #1f2937;']

        st.dataframe(df_final.style.format({"Prev":"{:.2f}","Price":"{:.2f}","%Chg":"{:.2f}%"}).apply(style_rows, axis=1), 
                     use_container_width=True, height=750, hide_index=True)
else:
    st.markdown(f"<h2 style='text-align:center; color:white; margin-top:100px;'>หน้านี้กำลังนำทางไปที่: {st.session_state.page}</h2>", unsafe_allow_html=True)
    if st.button("⬅️ กลับไปหน้าสแกน"):
        st.session_state.page = "Thai Scan"

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Floating Nav v5.5")
