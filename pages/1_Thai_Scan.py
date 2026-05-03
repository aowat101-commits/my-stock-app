import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP (Compact Base) ---
st.set_page_config(page_title="Guardian Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    
    .stApp { background-color: #0f172a; }

    /* ตารางตัวหนังสือดำพื้นขาว */
    .stDataFrame [data-testid="stTable"] td, 
    .stDataFrame [data-testid="stTable"] th {
        color: #000000 !important;
        background-color: #ffffff !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }

    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }

    /* ปุ่มกดสไตล์ V6.9 Compact */
    .stButton > button {
        height: 40px !important;
        font-size: 12px !important;
        border-radius: 6px !important;
        margin-bottom: -10px !important;
    }

    .time-status {
        background-color: #1e293b; color: #10b981; padding: 5px; border-radius: 5px;
        text-align: center; font-size: 11px; margin-top: 5px; margin-bottom: 5px; border: 1px solid #334155;
    }
    
    .welcome-text { color: #38bdf8; font-size: 24px; font-weight: bold; text-align: center; margin-top: 10px; }
    .sub-welcome { color: #94a3b8; font-size: 14px; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. COMPACT NAVIGATION ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Home'

# แถว 1: Home
if st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.current_page == 'Home' else "secondary"):
    st.session_state.current_page = 'Home'

# แถว 2: Thai Scan | Charts
c1, c2 = st.columns(2)
with c1:
    if st.button("📈 Thai Scan", use_container_width=True, type="primary" if st.session_state.current_page == 'Thai Scan' else "secondary"):
        st.session_state.current_page = 'Thai Scan'
with c2:
    if st.button("📊 Thai Charts", use_container_width=True, type="primary" if st.session_state.current_page == 'Thai Charts' else "secondary"):
        st.session_state.current_page = 'Thai Charts'

# แถว 3: US Scan | Charts
c3, c4 = st.columns(2)
with c3:
    if st.button("🇺🇸 US Scan", use_container_width=True, type="primary" if st.session_state.current_page == 'US Scan' else "secondary"):
        st.session_state.current_page = 'US Scan'
with c4:
    if st.button("📉 US Charts", use_container_width=True, type="primary" if st.session_state.current_page == 'US Charts' else "secondary"):
        st.session_state.current_page = 'US Charts'

# --- 3. CORE ENGINE ---
@st.cache_data(ttl=300)
def fetch_stock(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if df.empty: return None
        df = df.dropna()
        # Indicators...
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
            return {"Ticker": ticker.replace('.BK', ''), "Price": curr, "%Chg": ((curr - prev) / prev) * 100, "Signal": "▲ Deep Buy" if last.name in df[buy_c].index else "⚠️ P-Sell", "Time": last.name.astimezone(tz).strftime("%H:%M %d/%m"), "raw_time": last.name.astimezone(tz)}
    except: pass
    return None

# --- 4. PAGE ROUTING ---
cp = st.session_state.current_page

if cp == "Home":
    st.markdown('<p class="welcome-text">Welcome Trading for milk</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-welcome">Por Piang Electric Plus Co., Ltd. (PPE)</p>', unsafe_allow_html=True)
    
    # แสดงกราฟหน้า Home เหมือนตอนแรก (ตัวอย่างหุ้นหลัก)
    st.markdown('<div style="background-color:#1e293b; padding:10px; border-radius:10px; border:1px solid #334155;">', unsafe_allow_html=True)
    st.subheader("📊 Market Overview")
    index_data = yf.download("^SET.BK", period="1mo", interval="1d", progress=False)['Close']
    st.line_chart(index_data)
    st.markdown('</div>', unsafe_allow_html=True)

elif cp == "Thai Scan":
    st.markdown(f'<div class="time-status">🕒 {datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S")} | V7.0</div>', unsafe_allow_html=True)
    set100 = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK'] # ตัวอย่าง
    res = [fetch_stock(t) for t in set100]
    res = [r for r in res if r]
    if res:
        df_m = pd.DataFrame(res).sort_values("raw_time", ascending=False)
        st.dataframe(df_m.drop(columns=['raw_time']), use_container_width=True, hide_index=True)

elif cp == "Thai Charts":
    t_in = st.text_input("หุ้นไทย:", "PTT.BK")
    st.line_chart(yf.download(t_in, period="1mo")['Close'])

elif cp == "US Scan":
    us_res = [fetch_stock(t) for t in ['IONQ', 'IREN', 'NVDA', 'TSLA']]
    st.dataframe(pd.DataFrame([r for r in us_res if r]).drop(columns=['raw_time']), use_container_width=True)

elif cp == "US Charts":
    st.line_chart(yf.download("IONQ", period="1mo")['Close'])

st.write("---")
st.caption("PPE | Home Classic v7.0")
