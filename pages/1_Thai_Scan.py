import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP: แยกสไตล์ตามขนาดหน้าจอ ---
st.set_page_config(page_title="Guardian V8.5 Hybrid", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"], header, footer {display: none !important;}
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    /* --- สไตล์สำหรับ PC & Tablet (ขนาดหน้าจอปกติ) --- */
    .stMarkdown h3, .stMarkdown p, .stMarkdown span, label { color: inherit; }
    .stDataFrame [data-testid="stTable"] td, .stDataFrame [data-testid="stTable"] th {
        font-size: 14px !important; font-weight: 400 !important;
        background-color: #ffffff !important;
    }

    /* --- สไตล์สำหรับมือถือ (Mobile Only: หน้าจอ < 768px) --- */
    @media only screen and (max-width: 767px) {
        /* บังคับสีเหลืองเข้มเฉพาะในมือถือ */
        .stMarkdown h3, .stMarkdown p, .stMarkdown span, label { color: #FFD700 !important; }
        .stExpander details summary p { color: #FFD700 !important; }
        
        /* บังคับสีหัวตารางและตัวหนังสือทั่วไปในตารางเป็นสีเหลือง (กรณีค่าเป็น 0) */
        .stDataFrame th { color: #FFD700 !important; }
        .stDataFrame [data-testid="stTable"] td { color: #000000; } /* ตัวเลขในตารางยังคงเห็นชัดบนพื้นขาว */
    }

    .welcome-title { color: #FFFFFF !important; font-size: 38px; font-weight: 800; text-align: center; letter-spacing: 8px; margin-top: 15px; }
    .trading-home { color: #FFD700 !important; font-size: 32px; font-weight: 800; text-align: center; letter-spacing: 3px; margin-bottom: 25px; }
    .stButton > button { height: 45px !important; border-radius: 10px !important; width: 100%; }
    .block-container { padding-top: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE FUNCTIONS ---
def get_thai_dt():
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
    months = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    return f"📅 วัน{days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year + 543}", f"🕒 {now.strftime('%H:%M:%S')}"

@st.cache_data(ttl=60)
def fetch_hybrid_v85(ticker):
    try:
        df = yf.download(ticker, period="35d", interval="1h", progress=False)
        if df.empty or len(df) < 5: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        curr, prev, p_prev = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2]), float(df['Close'].iloc[-3])
        cv, cp = curr - prev, ((curr - prev) / prev) * 100
        rsi = ta.rsi(df['Close'], length=14)
        cr = float(rsi.iloc[-1]) if not rsi.empty else 0
        
        # สีตามเกณฑ์ V8.5 เดิม (เขียว/แดง)
        g, r = "#008000", "#cc0000"
        m_c = g if cv > 0 else (r if cv < 0 else "inherit")
        p_c = g if prev > p_prev else (r if prev < p_prev else "inherit")

        return {
            "Ticker": ticker.replace('.BK', ''),
            "Prev": f"{prev:.2f}", "Price": f"{curr:.2f}",
            "Chg": f"{cv:+.2f}", "%Chg": f"{cp:.2f}%", "RSI(14)": f"{cr:.2f}",
            "_mc": m_c, "_pc": p_c
        }
    except: return None

def apply_hybrid_style(row):
    mc, pc = f'color: {row["_mc"]}', f'color: {row["_pc"]}'
    # RSI ในมือถือจะเป็นสีเหลืองเข้มอัตโนมัติผ่าน CSS แต่ในนี้เรากำหนดให้เป็นสีพื้นฐาน
    return [mc, pc, mc, mc, mc, '', '', '']

# --- 3. SESSION & NAVIGATION ---
if 'pg' not in st.session_state: st.session_state.pg = 'Home'
if 'tw' not in st.session_state: st.session_state.tw = ['DELTA.BK', 'ADVANC.BK']
if 'uw' not in st.session_state: st.session_state.uw = ['IONQ', 'NVDA']

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
    st.markdown('<p class="welcome-title">WELCOME</p><p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1611974714658-d78e19277f21?q=80&w=1200", use_container_width=True)
    st.markdown(f'<p style="text-align:center;">{d_s}  |  {t_s}</p>', unsafe_allow_html=True)

elif curr in ['TW', 'UW']:
    st.markdown(f"<h3 style='text-align:center;'>{'🇹🇭 Thai Watchlist' if curr == 'TW' else '🇺🇸 US Watchlist'}</h3>", unsafe_allow_html=True)
    with st.expander("➕ เพิ่ม/ลด หุ้นในลิสต์"):
        th_o = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK', 'HANA.BK', 'KCE.BK', 'JMART.BK', 'JMT.BK']
        us_o = ['IONQ', 'NVDA', 'IREN', 'TSLA', 'SMX', 'ONDS']
        if curr == 'TW': st.session_state.tw = st.multiselect("เลือกหุ้น:", th_o, default=st.session_state.tw)
        else: st.session_state.uw = st.multiselect("Select Stocks:", us_o, default=st.session_state.uw)
    
    lst = st.session_state.tw if curr == 'TW' else st.session_state.uw
    if lst:
        data = [fetch_hybrid_v85(t) for t in lst if fetch_hybrid_v85(t)]
        if data:
            st.dataframe(pd.DataFrame(data).style.apply(apply_hybrid_style, axis=1), use_container_width=True, hide_index=True, column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))

st.markdown(f'<p style="text-align:center; font-size:12px; margin-top:50px; opacity:0.6;">PPE Guardian V8.5 Hybrid | {d_s}</p>', unsafe_allow_html=True)
