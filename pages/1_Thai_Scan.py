import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz

# --- 1. UI SETUP ---
st.set_page_config(page_title="Guardian Dashboard", layout="wide")
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    .main { background-color: #0f172a; }
    /* ปุ่มเลื่อนหน้าด้านล่าง */
    .stButton>button { width: 100%; border-radius: 20px; height: 50px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. NAVIGATION LOGIC (ระบบเลื่อนหน้า) ---
pages = ["Home", "Thai Scan", "Thai Charts", "US Scan"]
if 'page_index' not in st.session_state:
    st.session_state.page_index = 1  # เริ่มที่ Thai Scan

def change_page(delta):
    st.session_state.page_index = (st.session_state.page_index + delta) % len(pages)

# --- 3. SIDEBAR (เมนูเดิมเพื่อความปลอดภัย) ---
with st.sidebar:
    st.title("📌 Menu")
    app_page = st.radio("เลือกหน้าจอ:", pages, index=st.session_state.page_index, key="sidebar_nav")
    st.write("---")
    if st.button("🔄 Force Refresh", key="refresh"): st.rerun()

# อัปเดต index ตามการเลือกใน Sidebar
st.session_state.page_index = pages.index(app_page)
current_page = pages[st.session_state.page_index]

# --- 4. TICKERS & ENGINE (คงเดิม v4.2) ---
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

def analyze_v4_2_core(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 30: return None
        df = df.dropna()
        df['hma'] = ta.hma(df['Close'], 24)
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa, d = ta.ema(ap, 10), ta.ema(abs(ap - ta.ema(ap, 10)), 10)
        ci = (ap - esa) / (0.015 * d)
        df['wt1'], df['wt2'] = ta.ema(ci, 21), ta.sma(ta.ema(ci, 21), 4)
        df['buy'] = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2']) & (df['wt1'] < -50)
        df['sell'] = (df['wt1'].shift(1) > df['wt2'].shift(1)) & (df['wt1'] < df['wt2']) & (df['wt1'] > 48)
        all_sig = df[df['buy'] | df['sell']].copy()
        if not all_sig.empty:
            last = all_sig.iloc[-1]
            curr, idx = float(df['Close'].iloc[-1]), df.index.get_loc(last.name)
            prev = float(df['Close'].iloc[idx-1]) if idx > 0 else curr
            p_prev = float(df['Close'].iloc[idx-2]) if idx > 1 else prev
            return {
                "Ticker": ticker.replace('.BK', ''), "Prev": prev, "Price": curr, 
                "%Chg": ((curr - prev) / prev) * 100,
                "Signal": "▲ Buy" if last['buy'] else "⚠️ P-Sell",
                "Time/Date": last.name.strftime("%H:%M %d/%m"),
                "raw_time": last.name, "p_diff": prev - p_prev
            }
    except: pass
    return None

# --- 5. DISPLAY LOGIC ---
if current_page == "Thai Scan":
    st.subheader("🛡️ Thai Scan Dashboard")
    
    # ส่วนแสดงข้อมูล
    results = [analyze_v4_2_core(t) for t in full_scan_list]
    if results:
        df_m = pd.DataFrame(results).sort_values("raw_time", ascending=False).head(40)
        def apply_styles(row):
            m = df_m[df_m['Ticker'] == row['Ticker']].iloc[0]
            sig_c = '#4fd1c5' if "Buy" in m['Signal'] else '#ef4444'
            prev_s = f'color: {"#10b981" if m["p_diff"] > 0 else ("#ef4444" if m["p_diff"] < 0 else "")};'
            price_s = f'color: {"#10b981" if m["%Chg"] > 0 else ("#ef4444" if m["%Chg"] < 0 else "")};'
            return [f'color: {sig_c};', prev_s, price_s, price_s, f'color: {sig_c};', f'color: {sig_c};']
        
        df_d = df_m.drop(columns=['raw_time', 'p_diff']).reset_index(drop=True)
        st.dataframe(df_d.style.format({"Prev":"{:.2f}","Price":"{:.2f}","%Chg":"{:.2f}%"}).apply(apply_styles, axis=1), use_container_width=True, height=650, hide_index=True)

# --- 6. FLOATING FOOTER NAVIGATION (ปุ่มเลื่อนหน้า) ---
st.write("---")
col_prev, col_center, col_next = st.columns([1, 2, 1])
with col_prev:
    if st.button("⬅️ ย้อนกลับ"):
        change_page(-1)
        st.rerun()
with col_next:
    if st.button("ถัดไป ➡️"):
        change_page(1)
        st.rerun()
with col_center:
    st.markdown(f"<center>หน้าปัจจุบัน: <b>{current_page}</b></center>", unsafe_allow_html=True)
