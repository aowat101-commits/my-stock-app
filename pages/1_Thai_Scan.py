import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz

# --- 1. UI SETUP ---
st.set_page_config(page_title="Guardian Swing Dashboard", layout="wide")
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    /* ปรับแต่ง Sidebar ให้เห็นชัดเจน */
    [data-testid="stSidebarNav"] { background-color: #1e293b; }
    .main { background-color: #0f172a; }
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 12px; border-radius: 8px;
        text-align: center; font-size: 13px; margin-bottom: 15px; border: 1px solid #334155;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR NAVIGATION (บังคับลูกศรเมนู) ---
# การใช้ st.sidebar จะทำให้ปุ่มลูกศรโผล่ที่มุมซ้ายบนของโทรศัพท์ทันที
with st.sidebar:
    st.title("🛡️ Menu")
    app_page = st.radio("เลือกหน้าจอ:", ["หน้าหลัก (Dashboard)", "ประวัติย้อนหลัง", "ตั้งค่า"], index=0)
    st.write("---")
    if st.button("🔄 Refresh / Scan", use_container_width=True):
        st.rerun()
    st.caption("Por Piang Electric Plus Co., Ltd.")

# --- 3. TICKERS & ENGINE ---
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

def analyze_guardian_v4_2_sidebar(ticker):
    try:
        # ดึงประวัติ 60 วันเพื่อให้มีข้อมูลย้อนหลังมาโชว์ทันที
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 30: return None
        df = df.dropna()

        # Indicators (HMA, Volume, WaveTrend)
        df['hma'] = ta.hma(df['Close'], length=24)
        df['vma5'] = ta.sma(df['Volume'], length=5)
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa = ta.ema(ap, 10)
        d = ta.ema(abs(ap - esa), 10)
        ci = (ap - esa) / (0.015 * d)
        df['wt1'] = ta.ema(ci, 21)
        df['wt2'] = ta.sma(df['wt1'], 4)

        # ค้นหาสัญญาณล่าสุด
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

# --- 4. MAIN PAGE DISPLAY ---
if app_page == "หน้าหลัก (Dashboard)":
    st.subheader("🛡️ Guardian Dashboard (Sidebar Mode)")
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 {datetime.now(tz).strftime("%H:%M:%S")} | กดลูกศรมุมซ้ายบนเพื่อดูเมนู</div>', unsafe_allow_html=True)
    
    results = []
    # โชว์ความคืบหน้าการสแกน
    bar = st.progress(0, text="กำลังสแกนหุ้น...")
    for i, t in enumerate(full_scan_list):
        res = analyze_guardian_v4_2_sidebar(t)
        if res: results.append(res)
        bar.progress((i + 1) / len(full_scan_list))
    bar.empty()

    if results:
        df_m = pd.DataFrame(results).sort_values("raw_time", ascending=False).head(40)
        df_d = df_m.drop(columns=['raw_time', 'p_diff']).reset_index(drop=True)

        def apply_styles(row):
            ticker = row['Ticker']
            m = df_m[df_m['Ticker'] == ticker].iloc[0]
            sig_c = '#4fd1c5' if "Buy" in m['Signal'] else '#ef4444'
            p_diff, pct = m['p_diff'], m['%Chg']
            # ตรรกะสีที่คุณมิลค์สั่ง (แยกอิสระ)
            prev_s = f'color: {"#10b981" if p_diff > 0 else ("#ef4444" if p_diff < 0 else "")};'
            price_s = f'color: {"#10b981" if pct > 0 else ("#ef4444" if pct < 0 else "")};'
            return [f'color: {sig_c};', prev_s, price_s, price_s, f'color: {sig_c};', f'color: {sig_c};']

        styled = df_d.style.format({"Prev": "{:,.2f}", "Price": "{:,.2f}", "%Chg": "{:+.2f}%"}).apply(apply_styles, axis=1)
        st.dataframe(styled, use_container_width=True, height=750, hide_index=True)
    else:
        st.warning("🔎 กำลังดึงข้อมูลย้อนหลัง...")

else:
    st.subheader(f"📂 {app_page}")
    st.info("หน้านี้กำลังอยู่ระหว่างการพัฒนาตามคำแนะนำของคุณมิลค์ครับ")

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | Mobile Sidebar v4.2")
