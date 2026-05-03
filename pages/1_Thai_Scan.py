import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP (Dark Theme Focus) ---
st.set_page_config(page_title="Guardian Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* บังคับโทนสีพื้นหลังและสีตัวอักษรให้เป็น Dark Mode เสมอ */
    .stApp {
        background-color: #0f172a !important;
        color: #f8fafc !important;
    }
    
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    
    /* ปุ่มลูกศรควบคุม (>>) ให้มีสีเขียวชัดเจนและมีพื้นหลังตัดกับหน้าจอ */
    section[data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        left: 10px !important;
        top: 10px !important;
        z-index: 999999;
        background-color: #1e293b !important;
        border-radius: 0 10px 10px 0 !important;
        padding: 5px !important;
        border: 1px solid #334155 !important;
    }
    
    /* สีของไอคอนลูกศร */
    section[data-testid="stSidebarCollapsedControl"] svg {
        fill: #10b981 !important;
        width: 30px !important;
        height: 30px !important;
    }

    /* ปรับแต่ง Sidebar ให้เหมือนรูปตัวอย่าง */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155 !important;
    }
    
    /* จัดการความสวยงามของตัวเลือกเมนู (Radio) */
    div[data-testid="stSidebarNav"] {padding-top: 2rem;}
    .stRadio > div { gap: 8px; }
    
    /* แถบสถานะด้านบน */
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 12px; border-radius: 8px;
        text-align: center; font-size: 13px; margin-bottom: 20px; border: 1px solid #475569;
        font-weight: bold; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Header รูปธงและชื่อ Thai scan */
    .header-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 10px 0 20px 0;
        gap: 15px;
    }
    .header-text {
        color: #ffffff !important;
        font-size: 30px !important;
        font-weight: 800 !important;
        margin: 0 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .flag-img {
        width: 42px;
        height: auto;
        border-radius: 4px;
        border: 1px solid #475569;
    }
    
    /* ตารางข้อมูลให้มีสีที่อ่านง่ายบนพื้นหลังเข้ม */
    .stDataFrame {
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='color:#f8fafc; font-size:24px; margin-bottom:10px;'>📌 Menu</h2>", unsafe_allow_html=True)
    # ปรับหน้าตาปุ่มเลือกเมนูให้สะอาดตา
    app_page = st.radio(" ", ["Home", "Thai Scan", "Thai Charts", "US Scan"], index=1)
    
    st.markdown("<br><hr style='border-color:#334155;'><br>", unsafe_allow_html=True)
    
    # ส่วน Settings ตามรูปตัวอย่าง
    st.markdown("<p style='color:#94a3b8; font-size:16px; font-weight:bold;'>⚙️ Settings</p>", unsafe_allow_html=True)
    if st.button("🔄 Force Refresh", use_container_width=True):
        st.rerun()
    
    st.write("---")
    st.caption("Por Piang Electric Plus Co., Ltd.")

# --- 3. CORE ENGINE ---
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

def analyze_logic(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 30: return None
        df = df.dropna()
        df['hma'] = ta.hma(df['Close'], 24)
        df['ema8'] = ta.ema(df['Close'], 8)
        df['vma5'] = ta.sma(df['Volume'], 5)
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa, d = ta.ema(ap, 10), ta.ema(abs(ap - ta.ema(ap, 10)), 10)
        ci = (ap - esa) / (0.015 * d)
        df['wt1'], df['wt2'] = ta.ema(ci, 21), ta.sma(ta.ema(ci, 21), 4)
        df['buy_deep'] = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2']) & (df['wt1'] < -50) & (df['Close'] > df['ema8'])
        df['buy_std'] = (df['hma'] > df['hma'].shift(1)) & (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2']) & (df['wt1'] < -45) & (df['Volume'] >= df['vma5']*1.2)
        df['sell_p'] = (df['wt1'].shift(1) > df['wt2'].shift(1)) & (df['wt1'] < df['wt2']) & (df['wt1'] > 48)

        all_sig = df[df['buy_deep'] | df['buy_std'] | df['sell_p']].copy()
        if not all_sig.empty:
            last = all_sig.iloc[-1]
            tz = pytz.timezone('Asia/Bangkok')
            curr, idx = float(df['Close'].iloc[-1]), df.index.get_loc(last.name)
            prev = float(df['Close'].iloc[idx-1]) if idx > 0 else curr
            p_prev = float(df['Close'].iloc[idx-2]) if idx > 1 else prev
            return {
                "Ticker": ticker.replace('.BK', ''), "Prev": prev, "Price": curr, 
                "%Chg": ((curr - prev) / prev) * 100,
                "Signal": "▲ Deep Buy" if last['buy_deep'] else ("🚀 Buy" if last['buy_std'] else "⚠️ P-Sell"),
                "Time/Date": last.name.astimezone(tz).strftime("%H:%M %d/%m"),
                "raw_time": last.name.astimezone(tz), "p_diff": prev - p_prev
            }
    except: pass
    return None

# --- 4. DISPLAY ---
if app_page == "Thai Scan":
    # Header สไตล์ใหม่กึ่งกลางหน้าจอ
    st.markdown("""
        <div class="header-container">
            <img src="https://flagcdn.com/w80/th.png" class="flag-img">
            <p class="header-text">Thai scan</p>
        </div>
        """, unsafe_allow_html=True)
    
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 {datetime.now(tz).strftime("%H:%M:%S")} | Guardian V5.1</div>', unsafe_allow_html=True)
    
    results = [analyze_logic(t) for t in full_scan_list]
    results = [r for r in results if r]

    if results:
        df_m = pd.DataFrame(results).sort_values("raw_time", ascending=False).head(40)
        df_d = df_m.drop(columns=['raw_time', 'p_diff']).reset_index(drop=True)

        def apply_styles(row):
            m = df_m[df_m['Ticker'] == row['Ticker']].iloc[0]
            sig_c = '#4fd1c5' if "▲" in m['Signal'] or "🚀" in m['Signal'] else '#ef4444'
            prev_s = f'color: {"#10b981" if m["p_diff"] > 0 else ("#ef4444" if m["p_diff"] < 0 else "")};'
            price_s = f'color: {"#10b981" if m["%Chg"] > 0 else ("#ef4444" if m["%Chg"] < 0 else "")};'
            return [f'color: {sig_c};', prev_s, price_s, price_s, f'color: {sig_c};', f'color: {sig_c};']

        st.dataframe(df_d.style.format({"Prev":"{:.2f}","Price":"{:.2f}","%Chg":"{:.2f}%"}).apply(apply_styles, axis=1), use_container_width=True, height=750, hide_index=True)
    else:
        st.warning("🔎 ไม่พบข้อมูลสัญญาณ")

else:
    st.markdown(f"<h2 style='text-align:center; color:#ffffff; padding-top:50px;'>📂 หน้าจอ {app_page}</h2>", unsafe_allow_html=True)

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Stable Navigation v5.1")
