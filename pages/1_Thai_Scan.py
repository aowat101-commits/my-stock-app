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

    /* ปรับสีหัวข้อและข้อความทั่วไปให้เป็นสีขาวเพื่อให้มองเห็นชัด */
    h1, h2, h3, p, span, .stMarkdown { color: white !important; }
    
    .welcome-title { color: white !important; font-size: 38px; font-weight: 800; text-align: center; letter-spacing: 8px; margin-top: 15px; }
    .trading-home { color: #ffcc00 !important; font-size: 32px; font-weight: 800; text-align: center; letter-spacing: 3px; margin-bottom: 25px; }
    .status-bar { color: #ffffff !important; font-size: 15px; text-align: center; margin-top: 15px; font-weight: 500; }
    
    /* Caption ใต้ตาราง */
    .stCaption { color: #cbd5e1 !important; font-size: 12px !important; }

    /* Table Styling: ตัวอักษรปกติ (ไม่หนา) */
    .stDataFrame [data-testid="stTable"] td, .stDataFrame [data-testid="stTable"] th {
        font-size: 14px !important; font-weight: 400 !important;
    }

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
def fetch_styled_data(ticker, scan_mode=False):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False)
        if df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        curr = float(df['Close'].iloc[-1])
        prev_close = float(df['Close'].iloc[-2])
        prev_prev_close = float(df['Close'].iloc[-3])
        chg = ((curr - prev_close) / prev_close) * 100
        
        # Scan Logic (EMA8 + WaveTrend)
        df['ema8'] = ta.ema(df['Close'], 8)
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa, d = ta.ema(ap, 10), ta.ema(abs(ap - ta.ema(ap, 10)), 10)
        ci = (ap - esa) / (0.015 * d)
        df['wt1'], df['wt2'] = ta.ema(ci, 21), ta.sma(ta.ema(ci, 21), 4)
        
        buy = (df['wt1'].shift(1) < df['wt2'].shift(1)) & (df['wt1'] > df['wt2']) & (df['wt1'] < -50) & (df['Close'] > df['ema8'])
        sell = (df['wt1'].shift(1) > df['wt2'].shift(1)) & (df['wt1'] < df['wt2']) & (df['wt1'] > 48)
        
        sig_text, sig_color = "—", "#ffffff" # Default เป็นสีขาวถ้าไม่มีสัญญาณ
        if any(buy.tail(3)): sig_text, sig_color = "▲ Deep Buy", "#22c55e" # เขียว
        elif any(sell.tail(3)): sig_text, sig_color = "⚠️ P-Sell", "#ef4444" # แดง

        price_color = "#22c55e" if curr > prev_close else "#ef4444"
        prev_color = "#22c55e" if prev_close > prev_prev_close else "#ef4444"

        return {
            "Ticker": ticker.replace('.BK', ''),
            "Prev": f"{prev_close:.2f}",
            "Price": f"{curr:.2f}",
            "%Chg": f"{chg:.2f}%",
            "Signal": sig_text,
            "Time/Date": df.index[-1].strftime("%H:%M %d/%m"),
            "_sc": sig_color,
            "_pc": price_color,
            "_pv": prev_color
        }
    except: return None

def color_rows(row):
    return [f'color: {row["_sc"]}', f'color: {row["_pv"]}', f'color: {row["_pc"]}', 
            f'color: {row["_pc"]}', f'color: {row["_sc"]}', f'color: {row["_sc"]}', '', '', '']

# --- 3. SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 't_watch' not in st.session_state: st.session_state.t_watch = ['PTT.BK', 'DELTA.BK']
if 'u_watch' not in st.session_state: st.session_state.u_watch = ['IONQ', 'NVDA']

# --- 4. NAVIGATION ---
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

else:
    title = f"{'🇹🇭 Thai' if 'Thai' in p else '🇺🇸 US'} {'Market Scan' if 'Scan' in p else 'Watchlist'}"
    st.markdown(f"### {title}")
    st.markdown(f"**{t_time}**") # เวลาเหนือตารางปรับให้เป็นตัวหนาสีขาว
    
    clist = st.session_state.t_watch if "Thai" in p else st.session_state.u_watch
    is_scan = "Scan" in p

    if not is_scan:
        opts = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK'] if "Thai" in p else ['IONQ', 'IREN', 'NVDA', 'TSLA']
        if "Thai" in p: st.session_state.t_watch = st.multiselect("➕ จัดการหุ้น:", opts, default=st.session_state.t_watch)
        else: st.session_state.u_watch = st.multiselect("➕ Manage Stocks:", opts, default=st.session_state.u_watch)

    if clist:
        data = [fetch_styled_data(t, scan_mode=is_scan) for t in clist]
        df = pd.DataFrame([r for r in data if r])
        if not df.empty:
            st.dataframe(df.style.apply(color_rows, axis=1), use_container_width=True, hide_index=True, 
                         column_order=("Ticker", "Prev", "Price", "%Chg", "Signal", "Time/Date"))
    else: st.warning("กรุณาเพิ่มหุ้นในหน้า Watchlist")

st.markdown("---")
st.markdown(f"<p style='text-align:center; color:#94a3b8;'>PPE Guardian V8.2 | {t_date}</p>", unsafe_allow_html=True)
