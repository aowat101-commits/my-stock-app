import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP & CSS ---
st.set_page_config(page_title="Guardian Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    /* Home Styling */
    .welcome-title { color: white; font-size: 38px; font-weight: 800; text-align: center; letter-spacing: 8px; margin-top: 15px; }
    .trading-home { color: #ffcc00; font-size: 32px; font-weight: 800; text-align: center; letter-spacing: 3px; margin-bottom: 25px; }
    .status-bar { color: #ffffff; font-size: 15px; text-align: center; margin-top: 15px; font-weight: 500; }

    /* Table Styling (Black text on White background) */
    .stDataFrame [data-testid="stTable"] td, .stDataFrame [data-testid="stTable"] th {
        color: #000000 !important; background-color: #ffffff !important; font-size: 14px !important; font-weight: 500 !important;
    }

    /* Navigation Buttons (V6.4 Base Style) */
    .stButton > button { height: 42px !important; font-size: 13px !important; border-radius: 8px !important; margin-bottom: -5px !important; }
    .block-container { padding-top: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE FUNCTIONS ---
def get_thai_datetime():
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
    months = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    return f"📅 วัน{days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year + 543}", f"🕒 {now.strftime('%H:%M:%S')}"

@st.cache_data(ttl=60)
def fetch_data(ticker, scan_mode=False):
    try:
        df = yf.download(ticker, period="40d", interval="1h", progress=False)
        if df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        curr = float(df['Close'].iloc[-1])
        prev = float(df['Open'].iloc[-1])
        chg = ((curr - prev) / prev) * 100
        
        if not scan_mode:
            return {"Ticker": ticker.replace('.BK', ''), "Price": f"{curr:.2f}", "%Chg": f"{chg:.2f}%"}
        
        # Scan Logic (V6.9 Formula)
        df['ema8'] = ta.ema(df['Close'], 8)
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa, d = ta.ema(ap, 10), ta.ema(abs(ap - ta.ema(ap, 10)), 10)
        ci = (ap - esa) / (0.015 * d)
        df['wt1'], df['wt2'] = ta.ema(ci, 21), ta.sma(ta.ema(ci, 21), 4)
        
        buy = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2']) & (df['wt1'] < -50) & (df['Close'] > df['ema8'])
        sell = (df['wt1'].shift(1) > df['wt2'].shift(1)) & (df['wt1'] < df['wt2']) & (df['wt1'] > 48)
        
        signal = "—"
        if any(buy.tail(3)): signal = "▲ Deep Buy"
        elif any(sell.tail(3)): signal = "⚠️ P-Sell"
        
        return {"Ticker": ticker.replace('.BK', ''), "Price": f"{curr:.2f}", "Signal": signal, "Update": df.index[-1].strftime("%H:%M")}
    except: return None

# --- 3. SESSION STATE (Watchlist Management) ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 't_watch' not in st.session_state: st.session_state.t_watch = ['PTT.BK', 'DELTA.BK']
if 'u_watch' not in st.session_state: st.session_state.u_watch = ['IONQ', 'NVDA']

# --- 4. NAVIGATION MENU ---
if st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.page == 'Home' else "secondary"):
    st.session_state.page = 'Home'

c1, c2 = st.columns(2)
with c1:
    if st.button("🇹🇭 Thai Watchlist", use_container_width=True, type="primary" if st.session_state.page == 'Thai Watchlist' else "secondary"):
        st.session_state.page = 'Thai Watchlist'
    if st.button("🇹🇭 Thai Market Scan", use_container_width=True, type="primary" if st.session_state.page == 'Thai Scan' else "secondary"):
        st.session_state.page = 'Thai Scan'
with c2:
    if st.button("🇺🇸 US Watchlist", use_container_width=True, type="primary" if st.session_state.page == 'US Watchlist' else "secondary"):
        st.session_state.page = 'US Watchlist'
    if st.button("🇺🇸 US Market Scan", use_container_width=True, type="primary" if st.session_state.page == 'US Scan' else "secondary"):
        st.session_state.page = 'US Scan'

# --- 5. PAGE ROUTING ---
t_date, t_time = get_thai_datetime()
p = st.session_state.page

if p == 'Home':
    st.markdown('<p class="welcome-title">WELCOME</p>', unsafe_allow_html=True)
    st.markdown('<p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.markdown(f'<p class="status-bar">{t_date}  |  {t_time}</p>', unsafe_allow_html=True)

elif p == 'Thai Watchlist':
    st.subheader("🇹🇭 Thai Watchlist (จัดการหุ้นไทย)")
    # ระบบ Pick-list (SET100 Sample)
    options = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'GULF.BK', 'KBANK.BK', 'PTT.BK', 'PTTEP.BK', 'SCB.BK', 'TRUE.BK', 'JMT.BK', 'IVL.BK']
    st.session_state.t_watch = st.multiselect("➕ เพิ่ม/ลด หุ้นไทยที่ต้องการเฝ้าดู:", options, default=st.session_state.t_watch)
    
    res = [fetch_data(t) for t in st.session_state.t_watch]
    df = pd.DataFrame([r for r in res if r])
    st.write("### 📋 ตารางราคาปัจจุบัน")
    st.dataframe(df, use_container_width=True, hide_index=True)

elif p == 'Thai Scan':
    st.subheader(f"🇹🇭 Thai Market Scan (เฉพาะลิสต์ที่เลือก) | {t_time}")
    if st.session_state.t_watch:
        res = [fetch_data(t, scan_mode=True) for t in st.session_state.t_watch]
        df = pd.DataFrame([r for r in res if r])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("กรุณาเพิ่มหุ้นในหน้า Thai Watchlist ก่อนครับ")

elif p == 'US Watchlist':
    st.subheader("🇺🇸 US Watchlist (Manage US Stocks)")
    us_options = ['IONQ', 'NVDA', 'TSLA', 'IREN', 'SMX', 'ONDS', 'MARA', 'MSTR', 'AAPL', 'MSFT']
    st.session_state.u_watch = st.multiselect("➕ Select US Stocks:", us_options, default=st.session_state.u_watch)
    
    res = [fetch_data(t) for t in st.session_state.u_watch]
    df = pd.DataFrame([r for r in res if r])
    st.write("### 📋 Real-time Price Table")
    st.dataframe(df, use_container_width=True, hide_index=True)

elif p == 'US Scan':
    st.subheader(f"🇺🇸 US Market Scan | {t_time}")
    if st.session_state.u_watch:
        res = [fetch_data(t, scan_mode=True) for t in st.session_state.u_watch]
        df = pd.DataFrame([r for r in res if r])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error("Please add stocks in US Watchlist first.")

st.write("---")
st.caption(f"PPE Guardian V8.0 | {t_date}")
