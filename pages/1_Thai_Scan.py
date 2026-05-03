import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP ---
# ตั้งค่าให้ Sidebar ปิดไว้แต่แรกเพื่อให้มีปุ่ม >> แสดงผลเหมือนหน้าอื่นๆ
st.set_page_config(page_title="Guardian Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* ซ่อน Header มาตรฐานเพื่อให้หน้าจอคลีนเหมือนรูปตัวอย่าง */
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    
    /* พื้นหลังโทนเข้มสะอาดตา */
    .stApp { background-color: #0f172a; }

    /* ปรับแต่งปุ่มลูกศร (Toggle) ให้เด่นชัดและกดง่าย */
    button[kind="headerNoSpacing"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #10b981 !important;
        border-radius: 8px !important;
        margin-left: 10px !important;
        margin-top: 10px !important;
    }
    
    /* แถบสถานะ */
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 10px; border-radius: 8px;
        text-align: center; font-size: 13px; margin-bottom: 20px; border: 1px solid #334155;
        font-weight: bold;
    }
    
    /* จัดหัวข้อกึ่งกลางแบบเรียบง่ายไม่กวนระบบ */
    .center-title {
        display: flex; justify-content: center; align-items: center;
        gap: 15px; padding: 15px 0;
    }
    .title-text { color: white; font-size: 32px; font-weight: bold; margin: 0; }
    .flag-img { width: 45px; height: auto; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR (เมนูสไลด์เหมือนหน้าอื่นๆ) ---
with st.sidebar:
    st.markdown("<h2 style='color:white;'>📌 Menu</h2>", unsafe_allow_html=True)
    app_page = st.radio(" ", ["Home", "Thai Scan", "Thai Charts", "US Scan"], index=1)
    st.write("---")
    st.markdown("<p style='color:#94a3b8; font-weight:bold;'>⚙️ Settings</p>", unsafe_allow_html=True)
    if st.button("🔄 Force Refresh", use_container_width=True):
        st.rerun()
    st.caption("Por Piang Electric Plus Co., Ltd.")

# --- 3. ENGINE (Stable V4.2 Core) ---
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

@st.cache_data(ttl=300)
def fetch_scan(ticker):
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
if app_page == "Thai Scan":
    st.markdown("""
        <div class="center-title">
            <img src="https://flagcdn.com/w80/th.png" class="flag-img">
            <p class="title-text">Thai scan</p>
        </div>
        """, unsafe_allow_html=True)
    
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 {datetime.now(tz).strftime("%H:%M:%S")} | Guardian V5.3</div>', unsafe_allow_html=True)
    
    results = [fetch_scan(t) for t in full_scan_list]
    results = [r for r in results if r]

    if results:
        df_m = pd.DataFrame(results).sort_values("raw_time", ascending=False).head(40)
        df_show = df_m.drop(columns=['raw_time']).reset_index(drop=True)

        def row_style(row):
            m = df_m[df_m['Ticker'] == row['Ticker']].iloc[0]
            sig_c = '#4fd1c5' if "▲" in m['Signal'] else '#ef4444'
            val_c = '#10b981' if m['%Chg'] > 0 else ('#ef4444' if m['%Chg'] < 0 else '#ffffff')
            return [f'color: {sig_c};', '', f'color: {val_c};', f'color: {val_c};', f'color: {sig_c};', '']

        st.dataframe(df_show.style.format({"Prev":"{:.2f}","Price":"{:.2f}","%Chg":"{:.2f}%"}).apply(row_style, axis=1), 
                     use_container_width=True, height=750, hide_index=True)
    else:
        st.info("🔎 ไม่พบสัญญาณในขณะนี้")

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Stable Navigation v5.3")
