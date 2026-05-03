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
    [data-testid="stHeaderimport streamlit as st
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

st.markdown(f'<p style="text-align:center; color:#e2e8f0; margin-top:30px;">PPE Guardian V8.5 | {t_date}</p>', unsafe_allow_html=True)Header { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    /* ปรับสีตัวหนังสือส่วนหัวและเวลา */
    .stMarkdown h3, .stMarkdown p, .stMarkdown span { color: #ffffff !important; }
    .welcome-title { color: white !important; font-size: 38px; font-weight: 800; text-align: center; letter-spacing: 8px; margin-top: 15px; }
    .trading-home { color: #ffcc00 !important; font-size: 32px; font-weight: 800; text-align: center; letter-spacing: 3px; margin-bottom: 25px; }
    
    /* ตาราง Watchlist: ตัวหนังสือปกติ พื้นขาว ตามแบบหน้า Charts เดิม */
    .stDataFrame [data-testid="stTable"] td, .stDataFrame [data-testid="stTable"] th {
        font-size: 14px !important; font-weight: 400 !important;
        color: #000000 !important; background-color: #ffffff !important;
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
def fetch_watchlist_full(ticker):
    try:
        df = yf.download(ticker, period="30d", interval="1h", progress=False)
        if df.empty or len(df) < 15: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        curr = float(df['Close'].iloc[-1])
        prev = float(df['Close'].iloc[-2])
        chg_val = curr - prev
        chg_pct = (chg_val / prev) * 100
        
        # คำนวณ RSI 14
        rsi = ta.rsi(df['Close'], length=14)
        current_rsi = float(rsi.iloc[-1]) if not rsi.empty else 0
        
        # สีตามทิศทางราคาปัจจุบัน
        color = "#008000" if curr >= prev else "#cc0000"

        return {
            "Ticker": ticker.replace('.BK', ''),
            "Prev": f"{prev:.2f}",
            "Price": f"{curr:.2f}",
            "Chg": f"{chg_val:+.2f}",
            "%Chg": f"{chg_pct:.2f}%",
            "RSI(14)": f"{current_rsi:.2f}",
            "_color": color
        }
    except: return None

def apply_watchlist_style(row):
    return [f'color: {row["_color"]}'] * 6 + ['']

# --- 3. SESSION STATE & LISTS ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 't_watch' not in st.session_state: st.session_state.t_watch = ['PTT.BK', 'DELTA.BK', 'ADVANC.BK']
if 'u_watch' not in st.session_state: st.session_state.u_watch = ['IONQ', 'NVDA', 'IREN']

# รายชื่อหุ้นไทยจำนวนมาก (SET100 + Growth)
TH_OPTIONS = ['ADVANC.BK', 'AOT.BK', 'AWC.BK', 'BANPU.BK', 'BBL.BK', 'BCP.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'EA.BK', 'EGCO.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'INTUCH.BK', 'IRPC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KEX.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'OSP.BK', 'PLANB.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'RATCH.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'STA.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'TIDLOR.BK', 'TISCO.BK', 'TOP.BK', 'TRUE.BK', 'TTB.BK', 'TU.BK', 'VGI.BK', 'WHA.BK']
US_OPTIONS = ['AAPL', 'AMZN', 'AMD', 'GOOGL', 'IONQ', 'IREN', 'MARA', 'MSFT', 'MSTR', 'NVDA', 'ONDS', 'PLTR', 'SMX', 'TSLA', 'U', 'COIN']

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

# --- 5. PAGE CONTENT ---
t_date, t_time = get_thai_datetime()
p = st.session_state.page

if p == 'Home':
    st.markdown('<p class="welcome-title">WELCOME</p>', unsafe_allow_html=True)
    st.markdown('<p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.markdown(f'<p class="status-bar">{t_date}  |  {t_time}</p>', unsafe_allow_html=True)

elif "Watchlist" in p:
    m_name = "🇹🇭 Thai" if "Thai" in p else "🇺🇸 US"
    st.markdown(f"### {m_name} Watchlist")
    
    # ระบบ Pop-up เลือกหุ้น (Expander เพื่อให้ยุบเก็บได้เมื่อเลือกเสร็จ)
    with st.expander("➕ เพิ่ม/ลด หุ้นในลิสต์ (เลือกเสร็จแล้วกดปิดหน้านี้)"):
        if "Thai" in p:
            st.session_state.t_watch = st.multiselect("เลือกหุ้นไทยที่คุณต้องการ:", TH_OPTIONS, default=st.session_state.t_watch)
        else:
            st.session_state.u_watch = st.multiselect("Select US Stocks:", US_OPTIONS, default=st.session_state.u_watch)

    clist = st.session_state.t_watch if "Thai" in p else st.session_state.u_watch
    if clist:
        results = [fetch_watchlist_full(t) for t in clist]
        df = pd.DataFrame([r for r in results if r])
        if not df.empty:
            st.dataframe(df.style.apply(apply_watchlist_style, axis=1), use_container_width=True, hide_index=True, 
                         column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))
    else: st.warning("กรุณากดปุ่มด้านบนเพื่อเพิ่มหุ้นเข้าลิสต์ครับ")

elif "Scan" in p:
    # หน้าเจ็ตสแกน (คงไว้ตามเดิม ไม่แก้ไขตามสั่ง)
    st.markdown(f"### {'🇹🇭 Thai' if 'Thai' in p else '🇺🇸 US'} Market Scan")
    st.markdown(f"**{t_time}**")
    st.info("ระบบสแกนกำลังทำงานตามปกติ...")

st.markdown(f'<p style="text-align:center; color:#e2e8f0; margin-top:30px;">PPE Guardian V8.4 | {t_date}</p>', unsafe_allow_html=True)
