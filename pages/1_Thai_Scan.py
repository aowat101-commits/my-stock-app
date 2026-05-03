import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP (Universal Concept) ---
st.set_page_config(page_title="Guardian Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* ล้างส่วนเกินระบบ */
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    
    .stApp { background-color: #0f172a; }

    /* บังคับสีตาราง: ตัวหนังสือดำเข้มบนพื้นขาว เพื่อความชัดเจนบนทุกหน้าจอ */
    .stDataFrame [data-testid="stTable"] td, 
    .stDataFrame [data-testid="stTable"] th {
        color: #000000 !important;
        background-color: #ffffff !important;
        font-weight: 500 !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    /* แถบสถานะ */
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 10px; border-radius: 8px;
        text-align: center; font-size: 13px; margin-bottom: 20px; border: 1px solid #334155;
        font-weight: bold;
    }
    
    /* กล่องหัวข้อ */
    .header-box {
        display: flex; justify-content: center; align-items: center;
        gap: 12px; padding: 15px 0;
    }
    .header-text { color: white; font-size: 28px; font-weight: bold; margin: 0; }
    .flag-img { width: 42px; height: auto; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. UNIVERSAL NAVIGATION (Concept ปุ่มลอยเชื่อมต่อทุกหน้า) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Thai Scan'

# ปุ่มนำทางลอยตัวด้านบน (แสดงผลเหมือนกันทุกหน้า)
nav_col = st.columns([1,1,1,1,1])
with nav_col[0]:
    if st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.current_page == 'Home' else "secondary"):
        st.session_state.current_page = 'Home'
with nav_col[1]:
    if st.button("📈 Thai Scan", use_container_width=True, type="primary" if st.session_state.current_page == 'Thai Scan' else "secondary"):
        st.session_state.current_page = 'Thai Scan'
with nav_col[2]:
    if st.button("📊 Thai Charts", use_container_width=True, type="primary" if st.session_state.current_page == 'Thai Charts' else "secondary"):
        st.session_state.current_page = 'Thai Charts'
with nav_col[3]:
    if st.button("🇺🇸 US Scan", use_container_width=True, type="primary" if st.session_state.current_page == 'US Scan' else "secondary"):
        st.session_state.current_page = 'US Scan'
with nav_col[4]:
    if st.button("📉 US Charts", use_container_width=True, type="primary" if st.session_state.current_page == 'US Charts' else "secondary"):
        st.session_state.current_page = 'US Charts'

# --- 3. UNIVERSAL ENGINE ---
@st.cache_data(ttl=300)
def universal_scan(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 30: return None
        df = df.dropna()
        # คำนวณตามสูตรคุณมิลค์
        df['hma'] = ta.hma(df['Close'], 24)
        df['ema8'] = ta.ema(df['Close'], 8)
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa, d = ta.ema(ap, 10), ta.ema(abs(ap - ta.ema(ap, 10)), 10)
        ci = (ap - esa) / (0.015 * d)
        df['wt1'], df['wt2'] = ta.ema(ci, 21), ta.sma(ta.ema(ci, 21), 4)
        
        buy_cond = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2']) & (df['wt1'] < -50) & (df['Close'] > df['ema8'])
        sell_cond = (df['wt1'].shift(1) > df['wt2'].shift(1)) & (df['wt1'] < df['wt2']) & (df['wt1'] > 48)

        sigs = df[buy_cond | sell_cond].copy()
        if not sigs.empty:
            last = sigs.iloc[-1]
            tz = pytz.timezone('Asia/Bangkok')
            curr = float(df['Close'].iloc[-1])
            prev = float(df['Close'].iloc[df.index.get_loc(last.name)-1]) if df.index.get_loc(last.name) > 0 else curr
            return {
                "Ticker": ticker.replace('.BK', ''), "Prev": prev, "Price": curr, 
                "%Chg": ((curr - prev) / prev) * 100,
                "Signal": "▲ Deep Buy" if last.name in df[buy_cond].index else "⚠️ P-Sell",
                "Time/Date": last.name.astimezone(tz).strftime("%H:%M %d/%m"),
                "raw_time": last.name.astimezone(tz)
            }
    except: pass
    return None

# --- 4. PAGE ROUTING ---

# หน้า THAI SCAN
if st.session_state.current_page == "Thai Scan":
    st.markdown("""<div class="header-box"><img src="https://flagcdn.com/w80/th.png" class="flag-img"><p class="header-text">Thai scan</p></div>""", unsafe_allow_html=True)
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 {datetime.now(tz).strftime("%H:%M:%S")} | Guardian V6.1</div>', unsafe_allow_html=True)
    
    # รายชื่อหุ้นไทย
    set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
    extra_list = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
    full_list = list(set(set100 + extra_list))

    res = [universal_scan(t) for t in full_list]
    res = [r for r in res if r]
    if res:
        df_m = pd.DataFrame(res).sort_values("raw_time", ascending=False).head(45)
        df_f = df_m.drop(columns=['raw_time']).reset_index(drop=True)

        def row_style(row):
            m = df_m[df_m['Ticker'] == row['Ticker']].iloc[0]
            sig_c = '#0d9488' if "▲" in m['Signal'] else '#dc2626'
            val_c = '#059669' if m['%Chg'] > 0 else ('#dc2626' if m['%Chg'] < 0 else '#000000')
            return [f'color: {sig_c}; font-weight:bold;', 'color: #000000;', f'color: {val_c}; font-weight:bold;', f'color: {val_c};', f'color: {sig_c}; font-weight:bold;', 'color: #000000;']

        st.dataframe(df_f.style.format({"Prev":"{:.2f}","Price":"{:.2f}","%Chg":"{:.2f}%"}).apply(row_style, axis=1), 
                     use_container_width=True, height=800, hide_index=True)

# หน้า US SCAN
elif st.session_state.current_page == "US Scan":
    st.markdown("""<div class="header-box"><img src="https://flagcdn.com/w80/us.png" class="flag-img"><p class="header-text">US Market Scan</p></div>""", unsafe_allow_html=True)
    us_stocks = ['IONQ', 'IREN', 'SMX', 'ONDS', 'MARA', 'RIOT', 'MSTR', 'NVDA', 'TSLA']
    res = [universal_scan(t) for t in us_stocks]
    res = [r for r in res if r]
    if res:
        df_us = pd.DataFrame(res).drop(columns=['raw_time']).reset_index(drop=True)
        st.dataframe(df_us, use_container_width=True, height=400, hide_index=True)

# หน้า US CHARTS (เชื่อมต่อข้อมูลหุ้นสหรัฐ)
elif st.session_state.current_page == "US Charts":
    st.markdown("""<div class="header-box"><img src="https://flagcdn.com/w80/us.png" class="flag-img"><p class="header-text">US Charts Analysis</p></div>""", unsafe_allow_html=True)
    sel_us = st.selectbox("เลือกหุ้น US เพื่อดูกราฟ:", ['IONQ', 'IREN', 'SMX', 'ONDS', 'MSTR', 'NVDA'])
    st.info(f"กำลังดึงข้อมูลกราฟเทคนิคสำหรับ {sel_us}...")
    # ส่วนแสดงผลกราฟเบื้องต้น
    st.line_chart(yf.download(sel_us, period="1mo")['Close'])

# หน้า HOME
elif st.session_state.current_page == "Home":
    st.markdown("<h2 style='text-align:center; color:white; margin-top:50px;'>🏡 Guardian Central Home</h2>", unsafe_allow_html=True)
    st.markdown("<div style='background-color:#1e293b; padding:30px; border-radius:15px; max-width:700px; margin:auto; color:white; text-align:center; border: 1px solid #334155;'>", unsafe_allow_html=True)
    st.write(f"**ยินดีต้อนรับคุณมิลค์ (Aowat Lukthong)**")
    st.write("บริษัท พอเพียง อิเล็คทริค พลัส จำกัด (PPE)")
    st.write("---")
    st.write("สถานะระบบ: เชื่อมต่อสมบูรณ์ทุกหน้าจอ (Concept V6.1)")
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Universal Concept v6.1")
