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

    /* ปรับหัวข้อให้อยู่ตรงกลางจอ */
    .centered-title {
        text-align: center !important;
        width: 100%;
        margin-top: 10px;
    }

    /* ปรับแต่งตัวหนังสือให้เปลี่ยนสีตาม Theme อัตโนมัติ (Dynamic Color) */
    .stMarkdown h3, .stMarkdown p, .stMarkdown span, label {
        color: inherit !important;
    }
    
    .welcome-title { font-size: 38px; font-weight: 800; text-align: center; letter-spacing: 8px; margin-top: 15px; }
    .trading-home { color: #ffcc00 !important; font-size: 32px; font-weight: 800; text-align: center; letter-spacing: 3px; margin-bottom: 25px; }

    /* ตาราง: ให้สีพื้นหลังโปร่งแสงและตัวหนังสือเปลี่ยนตาม Theme */
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
def fetch_wallet_data(ticker):
    try:
        df = yf.download(ticker, period="30d", interval="1h", progress=False)
        if df.empty or len(df) < 5: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        curr = float(df['Close'].iloc[-1])
        prev = float(df['Close'].iloc[-2])
        prev_prev = float(df['Close'].iloc[-3])
        chg_val = curr - prev
        chg_pct = (chg_val / prev) * 100
        
        rsi_val = ta.rsi(df['Close'], length=14)
        curr_rsi = float(rsi_val.iloc[-1]) if not rsi_val.empty else 0
        
        # กฎสีช่อง 1, 3, 4, 5: เขียว/แดง ตามราคาปัจจุบัน
        main_c = "#00c805" if chg_val > 0 else "#ff1100"
        if chg_val == 0: main_c = "inherit" # เปลี่ยนตามพื้นหลัง

        # กฎสีช่อง 2 (Prev): เขียว/แดง ตามวันก่อนหน้า
        prev_c = "#00c805" if prev > prev_prev else "#ff1100"
        if prev == prev_prev: prev_c = "inherit" # เปลี่ยนตามพื้นหลัง

        return {
            "Ticker": ticker.replace('.BK', ''),
            "Prev": f"{prev:.2f}",
            "Price": f"{curr:.2f}",
            "Chg": f"{chg_val:+.2f}",
            "%Chg": f"{chg_pct:.2f}%",
            "RSI(14)": f"{curr_rsi:.2f}",
            "_mc": main_c, "_pc": prev_c
        }
    except: return None

def apply_style(row):
    # กำหนดสีตามเงื่อนไข (inherit จะปรับตาม PC/มือถือ อัตโนมัติ)
    mc = f'color: {row["_mc"]}'
    pc = f'color: {row["_pc"]}'
    return [mc, pc, mc, mc, mc, 'color: inherit', '', '']

# --- 3. SESSION & NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 't_watch' not in st.session_state: st.session_state.t_watch = ['PTT.BK', 'DELTA.BK']
if 'u_watch' not in st.session_state: st.session_state.u_watch = ['IONQ', 'NVDA']

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

# --- 4. PAGE ROUTING ---
t_date, t_time = get_thai_datetime()
p = st.session_state.page

if p == 'Home':
    st.markdown('<p class="welcome-title">WELCOME</p>', unsafe_allow_html=True)
    st.markdown('<p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.markdown(f'<p style="text-align:center;">{t_date}  |  {t_time}</p>', unsafe_allow_html=True)

elif "Watchlist" in p:
    m_label = "🇹🇭 Thai Watchlist" if "Thai" in p else "🇺🇸 US Watchlist"
    st.markdown(f'<h3 class="centered-title">{m_label}</h3>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;">{t_time}</p>', unsafe_allow_html=True)
    
    with st.expander("➕ จัดการลิสต์หุ้น"):
        opts = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK'] if "Thai" in p else ['IONQ', 'NVDA', 'IREN', 'TSLA']
        if "Thai" in p:
            st.session_state.t_watch = st.multiselect("เลือกหุ้นไทย:", opts, default=st.session_state.t_watch)
        else:
            st.session_state.u_watch = st.multiselect("Select US Stocks:", opts, default=st.session_state.u_watch)

    clist = st.session_state.t_watch if "Thai" in p else st.session_state.u_watch
    if clist:
        df = pd.DataFrame([fetch_wallet_data(t) for t in clist if fetch_wallet_data(t)])
        if not df.empty:
            st.dataframe(df.style.apply(apply_style, axis=1), use_container_width=True, hide_index=True, 
                         column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))

elif "Scan" in p:
    m_label = "🇹🇭 Thai Market Scan" if "Thai" in p else "🇺🇸 US Market Scan"
    st.markdown(f'<h3 class="centered-title">{m_label}</h3>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;">{t_time}</p>', unsafe_allow_html=True)
    st.info("ระบบกำลังแสดงข้อมูลสแกนตามโครงสร้างเดิม...")

st.markdown("---")
st.markdown(f'<p style="text-align:center; font-size:12px;">PPE Guardian V8.6 | {t_date}</p>', unsafe_allow_html=True)
