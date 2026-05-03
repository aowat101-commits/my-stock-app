import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP (ปรับแต่งเพื่อมือถือ) ---
st.set_page_config(page_title="Guardian Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    
    .stApp { background-color: #0f172a; }

    /* บังคับสีตาราง: ดำเข้มบนขาว */
    .stDataFrame [data-testid="stTable"] td, 
    .stDataFrame [data-testid="stTable"] th {
        color: #000000 !important;
        background-color: #ffffff !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }

    /* สไตล์เมนูปัดข้าง (Horizontal Scroll) */
    .scroll-nav {
        display: flex;
        overflow-x: auto;
        white-space: nowrap;
        gap: 8px;
        padding: 10px 0;
        scrollbar-width: none; /* ซ่อน scrollbar สำหรับ Firefox */
        -ms-overflow-style: none;  /* ซ่อน scrollbar สำหรับ IE */
    }
    .scroll-nav::-webkit-scrollbar { display: none; } /* ซ่อน scrollbar สำหรับ Chrome/Safari */

    .time-status {
        background-color: #1e293b; color: #10b981; padding: 6px; border-radius: 6px;
        text-align: center; font-size: 12px; margin-bottom: 10px; border: 1px solid #334155;
    }
    
    .header-box { display: flex; justify-content: center; align-items: center; gap: 8px; padding: 10px 0; }
    .header-text { color: white; font-size: 20px; font-weight: bold; margin: 0; }
    .flag-img { width: 30px; height: auto; border-radius: 2px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOBILE SCROLLING NAVIGATION ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Thai Scan'

# ใช้ Container สร้างแถบเลื่อนซ้ายขวา
st.markdown('<div class="scroll-nav">', unsafe_allow_html=True)
cols = st.columns([1,1,1,1,1]) # สร้างคอลัมน์ขนาดเท่ากัน

pages = [
    ("🏠 Home", "Home"),
    ("📈 Thai Scan", "Thai Scan"),
    ("📊 Thai Charts", "Thai Charts"),
    ("🇺🇸 US Scan", "US Scan"),
    ("📉 US Charts", "US Charts")
]

for i, (label, p_id) in enumerate(pages):
    with cols[i]:
        if st.button(label, use_container_width=True, type="primary" if st.session_state.current_page == p_id else "secondary"):
            st.session_state.current_page = p_id
st.markdown('</div>', unsafe_allow_html=True)

# --- 3. UNIVERSAL ENGINE ---
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
            return {
                "Ticker": ticker.replace('.BK', ''), "Prev": prev, "Price": curr, 
                "%Chg": ((curr - prev) / prev) * 100,
                "Signal": "▲ Deep Buy" if last.name in df[buy_c].index else "⚠️ P-Sell",
                "Time/Date": last.name.astimezone(tz).strftime("%H:%M %d/%m"),
                "raw_time": last.name.astimezone(tz)
            }
    except: pass
    return None

# --- 4. PAGE CONTENT ---
cp = st.session_state.current_page

if cp == "Thai Scan":
    st.markdown("""<div class="header-box"><img src="https://flagcdn.com/w80/th.png" class="flag-img"><p class="header-text">Thai Scan</p></div>""", unsafe_allow_html=True)
    st.markdown(f'<div class="time-status">🕒 {datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S")} | V6.3 Mobile</div>', unsafe_allow_html=True)
    
    set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
    res = [fetch_stock(t) for t in set100]
    res = [r for r in res if r]
    if res:
        df_m = pd.DataFrame(res).sort_values("raw_time", ascending=False).head(35)
        st.dataframe(df_m.drop(columns=['raw_time']), use_container_width=True, height=600, hide_index=True)

elif cp == "Home":
    st.markdown("<h4 style='text-align:center; color:white; padding:20px;'>🏡 Guardian Mobile Home</h4>", unsafe_allow_html=True)
    st.info(f"สวัสดีคุณมิลค์ | PPE Co., Ltd.\nระบบปุ่มนำทางแบบปัดข้างเปิดใช้งานแล้วครับ")

elif cp == "Thai Charts":
    st.markdown("<h4 style='text-align:center; color:white;'>📊 Mobile Charts</h4>", unsafe_allow_html=True)
    st.line_chart(yf.download("PTT.BK", period="1mo")['Close'])

elif cp == "US Scan":
    st.markdown("<h4 style='text-align:center; color:white;'>🇺🇸 US Scan</h4>", unsafe_allow_html=True)
    us_res = [fetch_stock(t) for t in ['IONQ', 'IREN', 'NVDA', 'TSLA']]
    st.dataframe(pd.DataFrame([r for r in us_res if r]).drop(columns=['raw_time']), use_container_width=True)

elif cp == "US Charts":
    st.markdown("<h4 style='text-align:center; color:white;'>📉 US Charts</h4>", unsafe_allow_html=True)
    st.line_chart(yf.download("IONQ", period="1mo")['Close'])

st.write("---")
st.caption("PPE | Mobile Optimized V6.3")
