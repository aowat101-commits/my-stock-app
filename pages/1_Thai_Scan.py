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

    /* บังคับหัวข้อให้อยู่ตรงกลางจอแน่นอน */
    .stMarkdown h3 { text-align: center !important; width: 100% !important; margin-bottom: 5px !important; color: inherit !important; }
    .stMarkdown p { text-align: center !important; width: 100% !important; color: inherit !important; }

    .welcome-title { color: white !important; font-size: 38px; font-weight: 800; text-align: center; letter-spacing: 8px; margin-top: 15px; }
    .trading-home { color: #ffcc00 !important; font-size: 32px; font-weight: 800; text-align: center; letter-spacing: 3px; margin-bottom: 25px; }

    /* ปรับแต่งปุ่มเมนูให้สวยงามและเป็นระเบียบ */
    .stButton > button { height: 42px !important; font-size: 13px !important; border-radius: 8px !important; margin-bottom: 2px !important; width: 100%; }
    
    /* ตาราง: ตัวอักษรปกติ และสีที่เปลี่ยนตาม Theme เครื่อง */
    .stDataFrame [data-testid="stTable"] td, .stDataFrame [data-testid="stTable"] th {
        font-size: 14px !important; font-weight: 400 !important;
        color: inherit !important;
    }
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
def fetch_wallet_v8(ticker):
    try:
        df = yf.download(ticker, period="30d", interval="1h", progress=False)
        if df.empty or len(df) < 15: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        curr = float(df['Close'].iloc[-1])
        prev = float(df['Close'].iloc[-2])
        p_prev = float(df['Close'].iloc[-3])
        chg_v = curr - prev
        chg_p = (chg_v / prev) * 100
        
        rsi = ta.rsi(df['Close'], length=14)
        c_rsi = float(rsi.iloc[-1]) if not rsi.empty else 0
        
        # สีตามกฎคุณมิลค์: เขียว/แดง ตามทิศทางราคา
        # ช่อง 1, 3, 4, 5
        mc = "#00c805" if chg_v > 0 else "#ff1100"
        if chg_v == 0: mc = "inherit"

        # ช่อง 2 (Prev)
        pc = "#00c805" if prev > p_prev else "#ff1100"
        if prev == p_prev: pc = "inherit"

        return {
            "Ticker": ticker.replace('.BK', ''),
            "Prev": f"{prev:.2f}",
            "Price": f"{curr:.2f}",
            "Chg": f"{chg_v:+.2f}",
            "%Chg": f"{chg_p:.2f}%",
            "RSI(14)": f"{c_rsi:.2f}",
            "_mc": mc, "_pc": pc
        }
    except: return None

def apply_v8_style(row):
    m = f'color: {row["_mc"]}'
    p = f'color: {row["_pc"]}'
    return [m, p, m, m, m, 'color: inherit', '', '']

# --- 3. NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 't_watch' not in st.session_state: st.session_state.t_watch = ['DELTA.BK']
if 'u_watch' not in st.session_state: st.session_state.u_watch = ['IONQ']

# ปุ่มเมนู Home
st.button("🏠 Home", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home"}), 
          type="primary" if st.session_state.page == 'Home' else "secondary")

c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 Thai Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Thai Watchlist"}),
              type="primary" if st.session_state.page == 'Thai Watchlist' else "secondary")
    st.button("🇹🇭 Thai Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Thai Scan"}),
              type="primary" if st.session_state.page == 'Thai Scan' else "secondary")
with c2:
    st.button("🇺🇸 US Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US Watchlist"}),
              type="primary" if st.session_state.page == 'US Watchlist' else "secondary")
    st.button("🇺🇸 US Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US Scan"}),
              type="primary" if st.session_state.page == 'US Scan' else "secondary")

# --- 4. PAGE LOGIC ---
t_d, t_t = get_thai_datetime()
curr_p = st.session_state.page

if curr_p == 'Home':
    st.markdown('<p class="welcome-title">WELCOME</p>', unsafe_allow_html=True)
    st.markdown('<p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.markdown(f'<p>{t_d}  |  {t_t}</p>', unsafe_allow_html=True)

elif "Watchlist" in curr_p:
    st.markdown(f"### {'🇹🇭 Thai Watchlist' if 'Thai' in curr_p else '🇺🇸 US Watchlist'}")
    st.markdown(f"<p>{t_t}</p>", unsafe_allow_html=True)
    
    with st.expander("➕ จัดการลิสต์หุ้น"):
        th_o = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK', 'JMART.BK', 'JMT.BK', 'HANA.BK', 'KCE.BK']
        us_o = ['IONQ', 'NVDA', 'IREN', 'TSLA', 'SMX', 'ONDS', 'MARA', 'MSTR']
        if "Thai" in curr_p:
            st.session_state.t_watch = st.multiselect("เลือกหุ้นไทย:", th_o, default=st.session_state.t_watch)
        else:
            st.session_state.u_watch = st.multiselect("Select US Stocks:", us_o, default=st.session_state.u_watch)

    clist = st.session_state.t_watch if "Thai" in curr_p else st.session_state.u_watch
    if clist:
        data = [fetch_wallet_v8(t) for t in clist if fetch_wallet_v8(t)]
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df.style.apply(apply_v8_style, axis=1), use_container_width=True, hide_index=True, 
                         column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))

elif "Scan" in curr_p:
    st.markdown(f"### {'🇹🇭 Thai Market Scan' if 'Thai' in curr_p else '🇺🇸 US Market Scan'}")
    st.markdown(f"<p>{t_t}</p>", unsafe_allow_html=True)
    st.info("กำลังโหลดข้อมูลสแกน...")

st.markdown("---")
st.markdown(f'<p style="font-size:12px; opacity:0.7;">PPE Guardian V8.7 | {t_d}</p>', unsafe_allow_html=True)
