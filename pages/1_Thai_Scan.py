import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP ---
# ตั้งค่าเริ่มต้นให้ Sidebar ปิดไว้ (collapsed) เพื่อให้มีปุ่ม >> บน PC/Tablet ทันที
st.set_page_config(page_title="Guardian Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* ซ่อน Header มาตรฐานของ Streamlit */
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    
    /* บังคับแสดงปุ่มลูกศร Sidebar (Toggle) ให้เห็นชัดเจนบน PC/Tablet */
    section[data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        left: 15px !important;
        top: 15px !important;
        z-index: 999999;
    }
    
    /* ปรับแต่งปุ่มลูกศร (>>) */
    button[kind="headerNoSpacing"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #10b981 !important;
        border-radius: 8px !important;
        padding: 5px !important;
    }

    .main { background-color: #0f172a; }
    [data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid #334155; }
    
    /* แถบสถานะด้านบน */
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 12px; border-radius: 8px;
        text-align: center; font-size: 13px; margin-bottom: 20px; border: 1px solid #334155;
        font-weight: bold;
    }
    
    /* แก้ไขปัญหาชื่อหาย: ใช้ Flexbox จัดรูปธงและชื่อให้อยู่กึ่งกลาง */
    .custom-header {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-bottom: 10px;
    }
    .header-content {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .header-text {
        color: white;
        font-size: 32px;
        font-weight: bold;
        margin: 0;
    }
    .flag-img {
        width: 45px;
        height: auto;
        border-radius: 4px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='color:white; margin-bottom:20px;'>📌 Menu</h2>", unsafe_allow_html=True)
    app_page = st.radio("เลือกหน้าจอ:", ["Home", "Thai Scan", "Thai Charts", "US Scan"], index=1)
    st.write("---")
    # ส่วน Settings แบบในรูปตัวอย่าง
    st.markdown("<p style='color:#94a3b8; font-size:14px; font-weight:bold;'>⚙️ Settings</p>", unsafe_allow_html=True)
    if st.button("🔄 Force Refresh", use_container_width=True):
        st.rerun()
    st.write("---")
    st.caption("Por Piang Electric Plus Co., Ltd.")

# --- 3. ENGINE (คงตรรกะเสถียร V4.6) ---
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

def analyze_v5(ticker):
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

# --- 4. DISPLAY LOGIC ---
if app_page == "Thai Scan":
    # ส่วนหัวข้อที่แก้ไขใหม่: แสดงรูปธงและชื่อพร้อมกันกึ่งกลางหน้าจอ
    st.markdown("""
        <div class="custom-header">
            <div class="header-content">
                <img src="https://flagcdn.com/w80/th.png" class="flag-img">
                <p class="header-text">Thai scan</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 {datetime.now(tz).strftime("%H:%M:%S")} | Guardian V5.0</div>', unsafe_allow_html=True)
    
    results = [analyze_v5(t) for t in full_scan_list]
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
    st.markdown(f"<h2 style='text-align:center; color:white; padding-top:50px;'>📂 หน้าจอ {app_page}</h2>", unsafe_allow_html=True)
    st.info("ใช้ปุ่มลูกศร (>>) มุมซ้ายบนเพื่อเปลี่ยนหน้าจอ")

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Stable Navigation v5.0")
