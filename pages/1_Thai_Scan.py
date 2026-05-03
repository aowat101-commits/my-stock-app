import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP (Speed Focus) ---
st.set_page_config(page_title="Guardian Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    .welcome-title { color: white; font-size: 40px; font-weight: 800; text-align: center; letter-spacing: 8px; margin-top: 15px; }
    .trading-home { color: #ffcc00; font-size: 32px; font-weight: 800; text-align: center; letter-spacing: 3px; margin-bottom: 25px; }
    
    .status-bar { color: #ffffff; font-size: 14px; text-align: center; margin-top: 15px; }
    .stButton > button { height: 42px !important; font-size: 14px !important; border-radius: 8px !important; }
    .stDataFrame [data-testid="stTable"] td { color: black !important; background: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THAI DATETIME ---
def get_thai_datetime():
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
    months = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    return f"📅 วัน{days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year + 543}", f"🕒 {now.strftime('%H:%M:%S')}"

# --- 3. FAST SCAN ENGINE (เพิ่มความเร็ว Cache) ---
@st.cache_data(ttl=600) # เพิ่มเป็น 10 นาทีเพื่อความเร็ว
def fast_fetch(ticker):
    try:
        df = yf.download(ticker, period="30d", interval="1h", progress=False)
        if df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df['ema8'] = ta.ema(df['Close'], 8)
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa, d = ta.ema(ap, 10), ta.ema(abs(ap - ta.ema(ap, 10)), 10)
        ci = (ap - esa) / (0.015 * d)
        df['wt1'], df['wt2'] = ta.ema(ci, 21), ta.sma(ta.ema(ci, 21), 4)
        
        buy = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2']) & (df['wt1'] < -50)
        sell = (df['wt1'].shift(1) > df['wt2'].shift(1)) & (df['wt1'] < df['wt2']) & (df['wt1'] > 48)
        
        last_sig = df[buy | sell].tail(1)
        if not last_sig.empty:
            curr = float(df['Close'].iloc[-1])
            prev = float(df['Open'].iloc[-1])
            return {
                "Ticker": ticker.replace('.BK', ''), "Price": curr, 
                "%Chg": ((curr - prev) / prev) * 100,
                "Signal": "▲ Deep Buy" if last_sig.index[-1] in df[buy].index else "⚠️ P-Sell",
                "Time": last_sig.index[-1].strftime("%H:%M %d/%m")
            }
    except: pass
    return None

# --- 4. NAVIGATION ---
if 'current_page' not in st.session_state: st.session_state.current_page = 'Home'

nav_cols = st.columns([1.2, 1, 1])
with nav_cols[0]:
    if st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.current_page == 'Home' else "secondary"):
        st.session_state.current_page = 'Home'
with nav_cols[1]:
    if st.button("📈 Thai Scan", use_container_width=True, type="primary" if st.session_state.current_page == 'Thai Scan' else "secondary"):
        st.session_state.current_page = 'Thai Scan'
with nav_cols[2]:
    if st.button("🇺🇸 US Market", use_container_width=True, type="primary" if st.session_state.current_page == 'US Scan' else "secondary"):
        st.session_state.current_page = 'US Scan'

# --- 5. PAGE CONTENT ---
cp = st.session_state.current_page
t_date, t_time = get_thai_datetime()

if cp == "Home":
    st.markdown(f'<p class="welcome-title">WELCOME</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.markdown(f'<p class="status-bar">{t_date} | {t_time}</p>', unsafe_allow_html=True)

elif cp == "Thai Scan":
    st.subheader(f"🇹🇭 Thai Market Scan | {t_time}")
    quick_list = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK', 'KBANK.BK', 'PTTEP.BK', 'GULF.BK', 'TRUE.BK']
    res = [fast_fetch(t) for t in quick_list]
    df = pd.DataFrame([r for r in res if r])
    if not df.empty: st.dataframe(df, use_container_width=True, hide_index=True)

elif cp == "US Scan":
    st.subheader(f"🇺🇸 US Market | {t_time}")
    us_list = ['IONQ', 'IREN', 'NVDA', 'TSLA', 'SMX', 'ONDS']
    res_us = [fast_fetch(t) for t in us_list]
    df_us = pd.DataFrame([r for r in res_us if r])
    if not df_us.empty: st.dataframe(df_us, use_container_width=True, hide_index=True)
