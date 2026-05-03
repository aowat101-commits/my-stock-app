import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP & CSS (บังคับ Dark Mode และปุ่ม Active สีแดง) ---
st.set_page_config(page_title="Guardian Dashboard V8.5", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    /* หัวข้อหน้า: กึ่งกลางและสีเหลืองเข้ม */
    .centered-yellow-title {
        text-align: center !important;
        color: #FFD700 !important;
        font-size: 28px;
        font-weight: 700;
        margin-top: 10px;
        width: 100%;
    }
    .centered-time { text-align: center !important; color: #FFD700 !important; width: 100%; margin-bottom: 20px; }

    /* หน้า Home: Welcome และ Trading Home เป็นสีเหลืองทั้งหมด */
    .welcome-title { color: #FFD700 !important; font-size: 38px; font-weight: 800; text-align: center; letter-spacing: 8px; margin-top: 15px; }
    .trading-home { color: #FFD700 !important; font-size: 32px; font-weight: 800; text-align: center; letter-spacing: 3px; margin-bottom: 25px; }
    
    /* ตาราง: บังคับพื้นหลังดำสนิท (Dark Mode) สำหรับ PC/Tablet/Mobile */
    .stDataFrame [data-testid="stTable"] { 
        background-color: #000000 !important; 
    }
    .stDataFrame th { 
        color: #FFD700 !important; 
        background-color: #000000 !important; 
        border: 0.1px solid #334155 !important;
    }
    .stDataFrame [data-testid="stTable"] td {
        font-size: 14px !important; 
        font-weight: 400 !important;
        background-color: #000000 !important; /* บังคับพื้นหลังดำเด็ดขาด */
        color: #FFD700 !important; /* แถวว่างเป็นสีเหลืองเข้ม */
        border: 0.1px solid #334155 !important;
    }

    /* ส่วนจัดการหุ้น: ตัวหนังสือเหลือง และเครื่องหมาย + สีน้ำเงินฟ้า */
    .stExpander details summary p { color: #FFD700 !important; font-weight: 500; }
    .stExpander details summary span svg { fill: #00BFFF !important; }
    
    /* ปุ่มเมนู: ปรับขนาดและระยะห่าง */
    .stButton > button { height: 45px !important; border-radius: 10px !important; width: 100%; transition: 0.3s; }
    
    /* บังคับสีแดงสำหรับปุ่มที่กำลัง Active (ถูกเลือก) */
    div.stButton > button[kind="primary"] {
        background-color: #FF0000 !important;
        color: white !important;
        border: none !important;
    }
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
def fetch_wallet_v85_dark_fix(ticker):
    try:
        df = yf.download(ticker, period="35d", interval="1h", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        curr, prev, p_prev = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2]), float(df['Close'].iloc[-3])
        cv, cp = curr - prev, ((curr - prev) / prev) * 100
        rsi = ta.rsi(df['Close'], length=14)
        cr = float(rsi.iloc[-1]) if not rsi.empty else 0
        
        # สีหุ้นสว่างชัดบนพื้นดำ
        g, r = "#00FF00", "#FF1100" 
        m_c = g if cv > 0 else (r if cv < 0 else "#FFD700")
        p_c = g if prev > p_prev else (r if prev < p_prev else "#FFD700")
        
        return {"Ticker": ticker.replace('.BK', ''), "Prev": f"{prev:.2f}", "Price": f"{curr:.2f}", 
                "Chg": f"{cv:+.2f}", "%Chg": f"{cp:.2f}%", "RSI(14)": f"{cr:.2f}", 
                "_mc": m_c, "_pc": p_c}
    except: return None

def apply_style_v85_dark(row):
    mc, pc = f'color: {row["_mc"]}', f'color: {row["_pc"]}'
    return [mc, pc, mc, mc, mc, 'color: #FFD700', '', '']

# --- 3. SESSION & NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 't_watch' not in st.session_state: st.session_state.t_watch = ['PTT.BK', 'DELTA.BK']
if 'u_watch' not in st.session_state: st.session_state.u_watch = ['IONQ', 'NVDA']

# ปุ่ม Home
st.button("🏠 Home", use_container_width=True, 
          on_click=lambda: st.session_state.update({"page": "Home"}), 
          type="primary" if st.session_state.page == 'Home' else "secondary")

c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 Thai Watchlist", use_container_width=True, 
              on_click=lambda: st.session_state.update({"page": "TW"}),
              type="primary" if st.session_state.page == 'TW' else "secondary")
    st.button("🇹🇭 Thai Market Scan", use_container_width=True, 
              on_click=lambda: st.session_state.update({"page": "TS"}),
              type="primary" if st.session_state.page == 'TS' else "secondary")
with c2:
    st.button("🇺🇸 US Watchlist", use_container_width=True, 
              on_click=lambda: st.session_state.update({"page": "UW"}),
              type="primary" if st.session_state.page == 'UW' else "secondary")
    st.button("🇺🇸 US Market Scan", use_container_width=True, 
              on_click=lambda: st.session_state.update({"page": "US"}),
              type="primary" if st.session_state.page == 'US' else "secondary")

d_s, t_s = get_thai_datetime()
p_curr = st.session_state.page

# --- 4. CONTENT ---
if p_curr == 'Home':
    st.markdown('<p class="welcome-title">WELCOME</p><p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.markdown(f'<p style="text-align:center; color:#FFD700;">{d_s}  |  {t_s}</p>', unsafe_allow_html=True)

elif p_curr in ['TW', 'UW']:
    title_label = "🇹🇭 Thai Watchlist" if p_curr == 'TW' else "🇺🇸 US Watchlist"
    st.markdown(f'<p class="centered-yellow-title">{title_label}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="centered-time">{t_s}</p>', unsafe_allow_html=True)
    
    with st.expander("➕ จัดการลิสต์หุ้น"):
        th_o = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK', 'HANA.BK', 'KCE.BK']
        if p_curr == 'TW': st.session_state.t_watch = st.multiselect("เลือกหุ้นไทย:", th_o, default=st.session_state.t_watch)
        else: st.session_state.u_watch = st.multiselect("Select US Stocks:", ['IONQ', 'NVDA', 'IREN', 'TSLA'], default=st.session_state.u_watch)
    
    lst = st.session_state.t_watch if p_curr == 'TW' else st.session_state.u_watch
    if lst:
        data = [fetch_wallet_v85_dark_fix(t) for t in lst if fetch_wallet_v85_dark_fix(t)]
        if data:
            st.dataframe(pd.DataFrame(data).style.apply(apply_style_v85_dark, axis=1), 
                         use_container_width=True, hide_index=True, 
                         column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))

elif p_curr in ['TS', 'US']:
    st.markdown(f'<p class="centered-yellow-title">{"🇹🇭 Thai" if p_curr == "TS" else "🇺🇸 US"} Market Scan</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="centered-time">{t_s}</p>', unsafe_allow_html=True)
    st.info("Scanner is monitoring signals...")

st.markdown(f'<p style="text-align:center; color:#FFD700; margin-top:50px; opacity:0.6;">PPE Guardian V8.5 | {d_s}</p>', unsafe_allow_html=True)
