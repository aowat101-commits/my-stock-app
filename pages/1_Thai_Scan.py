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
    /* ปรับแต่ง Sidebar ให้เหมือนรูปตัวอย่าง */
    [data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid #334155; }
    .stButton>button { width: 100%; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR NAVIGATION (เลียนแบบรูป 1233.jpg) ---
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    # เมนูหลัก
    nav_choice = st.radio(
        "Navigation",
        ["Home", "Thai Scan", "Thai Charts", "US Scan", "US Charts"],
        index=1, # ให้เริ่มที่ Thai Scan เป็นค่าเริ่มต้น
        label_visibility="collapsed"
    )
    
    st.write("---")
    st.markdown("### ⚙️ Settings")
    if st.button("🔄 Force Refresh"):
        st.rerun()
    
    st.write("---")
    st.caption("Por Piang Electric Plus Co., Ltd.")

# --- 3. TICKERS & ENGINE (อ้างอิงจาก User Summary) ---
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

def analyze_engine(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 30: return None
        df = df.dropna()
        # คำนวณอินดิเคเตอร์ (HMA, WT)
        df['hma'] = ta.hma(df['Close'], length=24)
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa, d = ta.ema(ap, 10), ta.ema(abs(ap - ta.ema(ap, 10)), 10)
        ci = (ap - esa) / (0.015 * d)
        df['wt1'], df['wt2'] = ta.ema(ci, 21), ta.sma(ta.ema(ci, 21), 4)
        # หาจังหวะสัญญาณ
        all_sig = df[((df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2']) & (df['wt1'] < -50)) |
                     ((df['wt1'].shift(1) > df['wt2'].shift(1)) & (df['wt1'] < df['wt2']) & (df['wt1'] > 48))].copy()
        if not all_sig.empty:
            last = all_sig.iloc[-1]
            tz = pytz.timezone('Asia/Bangkok')
            curr, idx = float(df['Close'].iloc[-1]), df.index.get_loc(last.name)
            prev = float(df['Close'].iloc[idx-1]) if idx > 0 else curr
            p_prev = float(df['Close'].iloc[idx-2]) if idx > 1 else prev
            return {
                "Ticker": ticker.replace('.BK', ''), "Prev": prev, "Price": curr, 
                "%Chg": ((curr - prev) / prev) * 100,
                "Signal": "▲ Buy" if last['wt1'] < 0 else "⚠️ P-Sell",
                "Time/Date": last.name.astimezone(tz).strftime("%H:%M %d/%m"),
                "raw_time": last.name.astimezone(tz), "p_diff": prev - p_prev
            }
    except: pass
    return None

# --- 4. DISPLAY LOGIC ---
if nav_choice == "Thai Scan":
    st.subheader("🛡️ Thai Scan Dashboard")
    results = [analyze_engine(t) for t in full_scan_list]
    if results:
        df_m = pd.DataFrame(results).sort_values("raw_time", ascending=False).head(40)
        df_d = df_m.drop(columns=['raw_time', 'p_diff']).reset_index(drop=True)
        # ตรรกะสีแยกอิสระ (Locked)
        def apply_styles(row):
            ticker = row['Ticker']
            m = df_m[df_m['Ticker'] == ticker].iloc[0]
            sig_c = '#4fd1c5' if "Buy" in m['Signal'] else '#ef4444'
            prev_s = f'color: {"#10b981" if m["p_diff"] > 0 else ("#ef4444" if m["p_diff"] < 0 else "")};'
            price_s = f'color: {"#10b981" if m["%Chg"] > 0 else ("#ef4444" if m["%Chg"] < 0 else "")};'
            return [f'color: {sig_c};', prev_s, price_s, price_s, f'color: {sig_c};', f'color: {sig_c};']
        styled = df_d.style.format({"Prev": "{:,.2f}", "Price": "{:,.2f}", "%Chg": "{:+.2f}%"}).apply(apply_styles, axis=1)
        st.dataframe(styled, use_container_width=True, height=750, hide_index=True)
else:
    st.subheader(f"🗂️ {nav_choice}")
    st.info(f"หน้าจอ {nav_choice} พร้อมเชื่อมต่อข้อมูลครับ")
