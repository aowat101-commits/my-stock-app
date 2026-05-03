import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP: ล็import streamlit as st
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

    /* ปรับตัวหนังสือบนตารางและ Expander ให้เป็นสีขาวชัดเจน */
    .stMarkdown h3, .stMarkdown p, .stMarkdown span, label { color: #ffffff !important; }
    .stExpander details summary p { color: #ffffff !important; font-weight: 500; }
    
    .welcome-title { color: white !important; font-size: 38px; font-weight: 800; text-align: center; letter-spacing: 8px; margin-top: 15px; }
    .trading-home { color: #ffcc00 !important; font-size: 32px; font-weight: 800; text-align: center; letter-spacing: 3px; margin-bottom: 25px; }

    /* ตาราง: ตัวอักษรปกติ พื้นขาว */
    .stDataFrame [data-testid="stTable"] td, .stDataFrame [data-testid="stTable"] th {
        font-size: 14px !important; font-weight: 400 !important;
        background-color: #ffffff !important;
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
        
        rsi = ta.rsi(df['Close'], length=14)
        current_rsi = float(rsi.iloc[-1]) if not rsi.empty else 0
        
        # กฎสีช่อง 1, 3, 4, 5 (Ticker, Price, Chg, %Chg)
        main_color = "#008000" if chg_val > 0 else "#cc0000"
        if chg_val == 0: main_color = "#000000" # เป็น 0 ให้เป็นสีดำ

        # กฎสีช่อง 2 (Prev)
        prev_color = "#008000" if prev > prev_prev else "#cc0000"
        if prev == prev_prev: prev_color = "#000000" # เป็น 0 ให้เป็นสีดำ

        return {
            "Ticker": ticker.replace('.BK', ''),
            "Prev": f"{prev:.2f}",
            "Price": f"{curr:.2f}",
            "Chg": f"{chg_val:+.2f}",
            "%Chg": f"{chg_pct:.2f}%",
            "RSI(14)": f"{current_rsi:.2f}",
            "_main_color": main_color,
            "_prev_color": prev_color
        }
    except: return None

def apply_wallet_style(row):
    mc = f'color: {row["_main_color"]}'
    pc = f'color: {row["_prev_color"]}'
    return [mc, pc, mc, mc, mc, 'color: #000000', '', ''] # ช่อง 1,3,4,5 สีเดียวกัน / ช่อง 2 สีแยก / RSI สีดำ

# --- 3. SESSION STATE & NAVIGATION ---
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

# --- 4. PAGE CONTENT ---
t_date, t_time = get_thai_datetime()
p = st.session_state.page

if p == 'Home':
    st.markdown('<p class="welcome-title">WELCOME</p>', unsafe_allow_html=True)
    st.markdown('<p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.markdown(f'<p class="status-bar">{t_date}  |  {t_time}</p>', unsafe_allow_html=True)

elif "Watchlist" in p:
    st.markdown(f"### {'🇹🇭 Thai' if 'Thai' in p else '🇺🇸 US'} Watchlist")
    
    with st.expander("➕ เพิ่ม/ลด หุ้นในลิสต์ (ตัวหนังสือสีขาวมองเห็นชัดเจน)"):
        opts = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK', 'HANA.BK', 'KCE.BK', 'JMART.BK', 'JMT.BK'] if "Thai" in p else ['IONQ', 'NVDA', 'IREN', 'TSLA', 'SMX', 'ONDS']
        if "Thai" in p:
            st.session_state.t_watch = st.multiselect("เลือกหุ้นไทย:", opts, default=st.session_state.t_watch)
        else:
            st.session_state.u_watch = st.multiselect("Select US Stocks:", opts, default=st.session_state.u_watch)

    clist = st.session_state.t_watch if "Thai" in p else st.session_state.u_watch
    if clist:
        results = [fetch_wallet_data(t) for t in clist]
        df = pd.DataFrame([r for r in results if r])
        if not df.empty:
            st.dataframe(df.style.apply(apply_wallet_style, axis=1), use_container_width=True, hide_index=True, 
                         column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))
    else: st.warning("กรุณาเพิ่มหุ้นในลิสต์")

elif "Scan" in p:
    st.markdown(f"### {'🇹🇭 Thai' if 'Thai' in p else '🇺🇸 US'} Market Scan")
    st.info("กำลังโหลดผลการสแกน...")

st.markdown(f'<p style="text-align:center; color:#e2e8f0; margin-top:30px;">PPE Guardian V8.5 | {t_date}</p>', unsafe_allow_html=True)ขาด ---
st.set_page_config(page_title="Guardian V9.3", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"], header, footer {display: none !important;}
    section[data-testid="stSidebar"] { display: none !important; }

    /* บังคับสีเหลืองเข้มให้ตัวหนังสือพื้นฐานทั้งหมด */
    html, body, [data-testid="stWidgetLabel"], .stMarkdown p, .stMarkdown h3 {
        color: #FFD700 !important;
    }

    .home-box {
        background-color: #050a18 !important;
        padding: 40px 15px;
        border-radius: 20px;
        text-align: center;
        border: 2px solid #FFD700;
    }
    
    /* หัวข้อหน้า Home */
    .w-yellow { color: #FFD700 !important; font-size: 42px; font-weight: 800; letter-spacing: 10px; margin: 0; }
    .t-yellow { color: #FFD700 !important; font-size: 32px; font-weight: 800; margin-top: 10px; }

    /* ปุ่มเมนู */
    .stButton > button { 
        width: 100% !important; 
        border-radius: 10px !important; 
        height: 50px !important; 
        border: 1px solid #FFD700 !important;
        color: #FFD700 !important;
    }

    /* ตาราง Watchlist: บังคับหัวตารางสีเหลือง */
    .stDataFrame th { color: #FFD700 !important; }
    .stDataFrame [data-testid="stTable"] td { 
        font-size: 14px !important; 
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCTIONS ---
def get_dt_now():
    tz = pytz.timezone('Asia/Bangkok')
    n = datetime.now(tz)
    d = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"][n.weekday()]
    m = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"][n.month-1]
    return f"📅 วัน{d}, {n.day} {m} {n.year + 543}", f"🕒 {n.strftime('%H:%M:%S')}"

@st.cache_data(ttl=60)
def fetch_stock_v93(ticker):
    try:
        df = yf.download(ticker, period="35d", interval="1h", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        c, p, pp = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2]), float(df['Close'].iloc[-3])
        cv, cp = c - p, ((c - p) / p) * 100
        rsi = ta.rsi(df['Close'], length=14)
        cr = float(rsi.iloc[-1]) if not rsi.empty else 0
        
        # สีเขียว/แดงสว่าง
        g, r = "#00FF00", "#FF3D00"
        mc = g if cv > 0 else (r if cv < 0 else "#FFD700")
        pc = g if p > pp else (r if p < pp else "#FFD700")
        
        return {"Ticker": ticker.replace('.BK', ''), "Prev": f"{p:.2f}", "Price": f"{c:.2f}", 
                "Chg": f"{cv:+.2f}", "%Chg": f"{cp:.2f}%", "RSI(14)": f"{cr:.2f}", 
                "_mc": mc, "_pc": pc}
    except: return None

def apply_color_v93(row):
    m, p = f'color: {row["_mc"]}', f'color: {row["_pc"]}'
    return [m, p, m, m, m, "color: #FFD700", "", ""]

# --- 3. APP ---
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

d_s, t_s = get_dt_now()
curr = st.session_state.pg

if curr == 'Home':
    st.markdown(f"""
    <div class="home-box">
        <p class="w-yellow">WELCOME</p>
        <p class="t-yellow">TRADING HOME</p>
        <div style="padding: 20px 0;">
            <img src="https://images.unsplash.com/photo-1611974714658-d78e19277f21?q=80&w=1000" 
                 style="width: 90%; border-radius: 12px; border: 1px solid #FFD700;"
                 onerror="this.style.display='none'">
        </div>
        <p style="color: #FFD700; margin-top: 20px;">{d_s} | {t_s}</p>
    </div>
    """, unsafe_allow_html=True)

elif curr in ['TW', 'UW']:
    st.markdown(f"<h3 style='text-align:center;'>{'🇹🇭 Thai Watchlist' if curr == 'TW' else '🇺🇸 US Watchlist'}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;'>{t_s}</p>", unsafe_allow_html=True)
    with st.expander("➕ จัดการลิสต์หุ้น"):
        opts = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK', 'HANA.BK', 'KCE.BK'] if curr == 'TW' else ['IONQ', 'NVDA', 'IREN', 'TSLA', 'SMX', 'ONDS']
        if curr == 'TW': st.session_state.tw = st.multiselect("เลือกหุ้นไทย:", opts, default=st.session_state.tw)
        else: st.session_state.uw = st.multiselect("Select US Stocks:", opts, default=st.session_state.uw)
    
    lst = st.session_state.tw if curr == 'TW' else st.session_state.uw
    if lst:
        data = [fetch_stock_v93(t) for t in lst if fetch_stock_v93(t)]
        if data:
            st.dataframe(pd.DataFrame(data).style.apply(apply_color_v93, axis=1), use_container_width=True, hide_index=True, column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))

st.markdown(f'<p style="text-align:center; font-size:12px; margin-top:50px; color: #FFD700; opacity: 0.6;">PPE Guardian V9.3 | {d_s}</p>', unsafe_allow_html=True)
