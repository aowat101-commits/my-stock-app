import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP & CSS (เน้นแก้สีเฉพาะจุดที่คุณมิลค์สั่ง) ---
st.set_page_config(page_title="Guardian Dashboard V8.5", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    /* หน้า Home: ตัวหนังสือ Welcome และ Trading Home เป็นสีเหลือง/ส้มแบบเดิม */
    .welcome-title { color: #FFD700 !important; font-size: 38px; font-weight: 800; text-align: center; letter-spacing: 8px; margin-top: 15px; }
    .trading-home { color: #FFA500 !important; font-size: 32px; font-weight: 800; text-align: center; letter-spacing: 3px; margin-bottom: 25px; }
    
    /* ในตาราง: หัวตารางและแถวที่ว่างเป็นสีเหลืองเข้ม */
    .stDataFrame th { color: #FFD700 !important; background-color: #1e293b !important; }
    .stDataFrame [data-testid="stTable"] td {
        font-size: 14px !important; font-weight: 400 !important;
        background-color: #ffffff !important;
        color: #FFD700 !important; /* บังคับแถวว่างหรือค่าพื้นฐานเป็นสีเหลืองเข้ม */
    }

    /* ส่วนจัดการหุ้น: ตัวหนังสือเหลืองเข้ม และเครื่องหมาย + เป็นสีน้ำเงินฟ้า */
    .stExpander details summary p { color: #FFD700 !important; font-weight: 500; }
    .stExpander details summary span svg { fill: #00BFFF !important; } /* ปรับสีไอคอน + */
    
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
def fetch_wallet_v85(ticker):
    try:
        df = yf.download(ticker, period="35d", interval="1h", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        curr, prev, p_prev = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2]), float(df['Close'].iloc[-3])
        cv, cp = curr - prev, ((curr - prev) / prev) * 100
        rsi = ta.rsi(df['Close'], length=14)
        cr = float(rsi.iloc[-1]) if not rsi.empty else 0
        
        # สีตามเกณฑ์ V8.5: เขียว/แดง
        g, r = "#008000", "#cc0000"
        m_c = g if cv > 0 else (r if cv < 0 else "#FFD700")
        p_c = g if prev > p_prev else (r if prev < p_prev else "#FFD700")

        return {
            "Ticker": ticker.replace('.BK', ''), "Prev": f"{prev:.2f}", "Price": f"{curr:.2f}",
            "Chg": f"{cv:+.2f}", "%Chg": f"{cp:.2f}%", "RSI(14)": f"{cr:.2f}",
            "_mc": m_c, "_pc": p_c
        }
    except: return None

def apply_style_v85(row):
    mc, pc = f'color: {row["_mc"]}', f'color: {row["_pc"]}'
    # ช่อง 1,3,4,5 สีเขียว/แดง | ช่อง 2 สีแยก | ช่อง 6 (RSI) เป็นสีเหลืองเข้มตามสั่ง
    return [mc, pc, mc, mc, mc, 'color: #FFD700', '', '']

# --- 3. SESSION & NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 't_watch' not in st.session_state: st.session_state.t_watch = ['PTT.BK', 'DELTA.BK']
if 'u_watch' not in st.session_state: st.session_state.u_watch = ['IONQ', 'NVDA']

st.button("🏠 Home", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home"}), type="primary" if st.session_state.page == 'Home' else "secondary")

c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 Thai Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Thai Watchlist"}))
    st.button("🇹🇭 Thai Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Thai Scan"}))
with c2:
    st.button("🇺🇸 US Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US Watchlist"}))
    st.button("🇺🇸 US Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US Scan"}))

d_s, t_s = get_thai_datetime()
p = st.session_state.page

# --- 4. CONTENT ---
if p == 'Home':
    st.markdown('<p class="welcome-title">WELCOME</p>', unsafe_allow_html=True)
    st.markdown('<p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.markdown(f'<p style="text-align:center; color:#FFD700;">{d_s}  |  {t_s}</p>', unsafe_allow_html=True)

elif "Watchlist" in p:
    st.markdown(f"### {'🇹🇭 Thai' if 'Thai' in p else '🇺🇸 US'} Watchlist")
    with st.expander("➕ จัดการลิสต์หุ้น"):
        opts = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK', 'HANA.BK', 'KCE.BK', 'JMART.BK', 'JMT.BK']
        if "Thai" in p: st.session_state.t_watch = st.multiselect("เลือกหุ้นไทย:", opts, default=st.session_state.t_watch)
        else: st.session_state.u_watch = st.multiselect("Select US Stocks:", ['IONQ', 'NVDA', 'IREN', 'TSLA'], default=st.session_state.u_watch)
    
    lst = st.session_state.t_watch if "Thai" in p else st.session_state.u_watch
    if lst:
        data = [fetch_wallet_v85(t) for t in lst if fetch_wallet_v85(t)]
        if data:
            st.dataframe(pd.DataFrame(data).style.apply(apply_style_v85, axis=1), use_container_width=True, hide_index=True, column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))

st.markdown(f'<p style="text-align:center; color:#FFD700; margin-top:50px; opacity:0.6;">PPE Guardian V8.5 | {d_s}</p>', unsafe_allow_html=True)
