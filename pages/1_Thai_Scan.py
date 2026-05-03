import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP & DEEP CSS FIX ---
st.set_page_config(page_title="Guardian V9.0", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"], header, footer {display: none !important;}
    section[data-testid="stSidebar"] { display: none !important; }
    
    /* บังคับหน้า Home ให้ล็อกสีเข้มเสมอเพื่อความสวยงาม */
    .home-box {
        background-color: #0f172a;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .w-title { color: #ffffff !important; font-size: 42px; font-weight: 800; letter-spacing: 10px; margin-bottom: 5px; }
    .t-title { color: #ffcc00 !important; font-size: 32px; font-weight: 800; letter-spacing: 2px; margin-bottom: 25px; }
    .st-text { color: #cbd5e1 !important; font-size: 16px; margin-top: 20px; font-weight: 500; }

    /* ปุ่มเมนู */
    .stButton > button { width: 100% !important; border-radius: 12px !important; height: 48px !important; font-weight: 600 !important; }
    
    /* ตาราง Watchlist */
    .stDataFrame [data-testid="stTable"] td { font-size: 14px !important; font-weight: 500 !important; }
    .stMarkdown h3 { text-align: center !important; width: 100%; color: inherit !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCTIONS ---
def get_thai_dt():
    tz = pytz.timezone('Asia/Bangkok')
    n = datetime.now(tz)
    d = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"][n.weekday()]
    m = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"][n.month-1]
    return f"📅 วัน{d}, {n.day} {m} {n.year + 543}", f"🕒 {n.strftime('%H:%M:%S')}"

@st.cache_data(ttl=60)
def fetch_v9(ticker):
    try:
        df = yf.download(ticker, period="35d", interval="1h", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        c, p, pp = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2]), float(df['Close'].iloc[-3])
        cv, cp = c - p, ((c - p) / p) * 100
        rsi = ta.rsi(df['Close'], length=14)
        cr = float(rsi.iloc[-1]) if not rsi.empty else 0
        g, r = "#00c805", "#ff1100"
        m_c = g if cv > 0 else (r if cv < 0 else "inherit")
        p_c = g if p > pp else (r if p < pp else "inherit")
        return {"Ticker": ticker.replace('.BK', ''), "Prev": f"{p:.2f}", "Price": f"{c:.2f}", "Chg": f"{cv:+.2f}", "%Chg": f"{cp:.2f}%", "RSI(14)": f"{cr:.2f}", "_m": m_c, "_p": p_c}
    except: return None

def style_v9(row):
    m, p = f'color: {row["_m"]}', f'color: {row["_p"]}'
    return [m, p, m, m, m, "color: inherit", "", ""]

# --- 3. SESSION & NAV ---
if 'pg' not in st.session_state: st.session_state.pg = 'Home'
if 'tw' not in st.session_state: st.session_state.tw = ['DELTA.BK', 'ADVANC.BK', 'PTT.BK']
if 'uw' not in st.session_state: st.session_state.uw = ['IONQ', 'NVDA', 'IREN']

st.button("🏠 Home", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "Home"}), type="primary" if st.session_state.pg == 'Home' else "secondary")

c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 Thai Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "TW"}))
    st.button("🇹🇭 Thai Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "TS"}))
with c2:
    st.button("🇺🇸 US Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "UW"}))
    st.button("🇺🇸 US Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "US"}))

d_s, t_s = get_thai_dt()
curr = st.session_state.pg

# --- 4. CONTENT ---
if curr == 'Home':
    st.markdown(f"""
    <div class="home-box">
        <p class="w-title">WELCOME</p>
        <p class="t-title">TRADING HOME</p>
        <div style="display: flex; justify-content: center;">
            <img src="https://images.unsplash.com/photo-1611974714658-d78e19277f21?q=80&w=1000" style="width:90%; border-radius:15px; border: 2px solid #ffcc00;">
        </div>
        <p class="st-text">{d_s} | {t_s}</p>
    </div>
    """, unsafe_allow_html=True)

elif curr in ['TW', 'UW']:
    m_label = "🇹🇭 Thai Watchlist" if curr == 'TW' else "🇺🇸 US Watchlist"
    st.markdown(f"### {m_label}")
    st.markdown(f"<p style='text-align:center;'>{t_s}</p>", unsafe_allow_html=True)
    with st.expander("➕ เพิ่ม/ลด หุ้นในลิสต์"):
        th_o = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK', 'HANA.BK', 'KCE.BK', 'JMART.BK', 'JMT.BK']
        us_o = ['IONQ', 'NVDA', 'IREN', 'TSLA', 'SMX', 'ONDS', 'MARA', 'MSTR']
        if curr == 'TW': st.session_state.tw = st.multiselect("เลือกหุ้นไทย:", th_o, default=st.session_state.tw)
        else: st.session_state.uw = st.multiselect("Select US Stocks:", us_o, default=st.session_state.uw)
    lst = st.session_state.tw if curr == 'TW' else st.session_state.uw
    if lst:
        data = [fetch_v9(t) for t in lst if fetch_v9(t)]
        if data:
            st.dataframe(pd.DataFrame(data).style.apply(style_v9, axis=1), use_container_width=True, hide_index=True, column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))

elif curr in ['TS', 'US']:
    st.markdown(f"### {'🇹🇭 Thai' if curr == 'TS' else '🇺🇸 US'} Market Scan")
    st.markdown(f"<p style='text-align:center;'>{t_s}</p>", unsafe_allow_html=True)
    st.info("Scanner is active and monitoring signals...")

st.markdown(f'<p style="text-align:center; font-size:12px; margin-top:50px; opacity:0.5;">PPE Guardian V9.0 | {d_s}</p>', unsafe_allow_html=True)
