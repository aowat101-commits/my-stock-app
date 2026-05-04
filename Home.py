import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz
import time
import os

# --- 1. CORE STORAGE SYSTEM ---
def manage_storage(mode, ticker=None, action="load"):
    file_path = f"{mode}_list.txt"
    defaults = ['PTT', 'DELTA'] if mode == "th" else ['IONQ', 'NVDA']
    if not os.path.exists(file_path):
        with open(file_path, "w") as f: f.write(",".join(defaults))
    with open(file_path, "r") as f:
        data = f.read().strip()
        current_data = [x.strip().upper() for x in data.split(",") if x.strip()] if data else defaults
    if action == "add" and ticker:
        ticker = ticker.strip().upper()
        if ticker and ticker not in current_data:
            current_data.append(ticker)
            with open(file_path, "w") as f: f.write(",".join(current_data)); f.flush()
    elif action == "delete" and ticker:
        if ticker in current_data:
            current_data.remove(ticker)
            with open(file_path, "w") as f: f.write(",".join(current_data)); f.flush()
    return current_data

if 'th_logs' not in st.session_state: st.session_state.th_logs = pd.DataFrame()
if 'us_logs' not in st.session_state: st.session_state.us_logs = pd.DataFrame()

# --- 2. UI SETUP & ABSOLUTE CENTERING ---
st.set_page_config(page_title="PPE Guardian V14.1", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stSidebar"], .st-emotion-cache-10o48ve, header, .stAppHeader { display: none !important; }
    .stApp { background-color: #0f172a; }
    
    .stApp .main .block-container {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-align: center !important;
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 auto !important;
    }

    div[data-testid="stVerticalBlock"] {
        align-items: center !important;
        width: 100% !important;
    }

    .stButton {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }
    .stButton > button { 
        height: 50px !important; 
        border-radius: 12px !important; 
        font-size: 17px !important; 
        font-weight: bold !important; 
        color: #FFD700 !important; 
        background-color: #1e293b !important; 
        border: 2px solid #FFD700 !important;
        width: 300px !important;
        margin: 8px auto !important;
    }

    .del-btn button { color: #FF4B4B !important; border-color: #FF4B4B !important; }
    .stExpander { width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INDICATOR ENGINE (With RSI) ---
@st.cache_data(ttl=60)
def fetch_verified_data(ticker, market_mode):
    try:
        symbol = f"{ticker.upper()}.BK" if market_mode == "th" and ".BK" not in ticker.upper() else ticker.upper()
        # ดึงข้อมูลย้อนหลังมากขึ้นเพื่อคำนวณ RSI 14 วัน
        df = yf.download(symbol, period="1mo", interval="1h", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # คำนวณ RSI
        rsi_series = ta.rsi(df['Close'], length=14)
        current_rsi = rsi_series.iloc[-1] if not rsi_series.empty else 0
        
        cp = float(df['Close'].iloc[-1])
        c_pp = float(df['Close'].iloc[-2])
        chg = cp - c_pp
        vol = df['Volume'].iloc[-1]
        val_raw = (cp * vol) / 1_000_000
        last_time = df.index[-1].astimezone(pytz.timezone('Asia/Bangkok'))
        
        # คืนค่าตามลำดับคอลัมน์ที่คุณมิลค์ต้องการ
        return {
            "Ticker": ticker.upper(),
            "Prev": f"{c_pp:.2f}",
            "Price": f"{cp:.2f}",
            "Chg": f"{chg:+.2f}",
            "%Chg": f"{(chg/c_pp)*100:.2f}%",
            "Value (M)": f"{val_raw:.2f}M",
            "TimeUpdate": last_time.strftime("%H:%M %d/%m"),
            "RSI": f"{current_rsi:.2f}"
        }
    except: return None

# --- 4. NAVIGATION & TIME ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 'market' not in st.session_state: st.session_state.market = None
now = datetime.now(pytz.timezone("Asia/Bangkok"))
time_str = now.strftime("%H:%M:%S"); date_str = now.strftime("%d/%m/%Y")

def centered_header(title, subtitle):
    st.markdown(f"""<div style="text-align: center; width: 100%;"><h1 style="color: #FFD700; font-size: 32px; font-weight: 900; margin-bottom: 0px;">{title}</h1><p style="color: #1E90FF; font-size: 13px; margin-top: 0px; margin-bottom: 10px;">{subtitle}</p></div>""", unsafe_allow_html=True)

# --- 5. PAGE LOGIC ---
if st.session_state.page == 'Home':
    centered_header("TRADING HOME", f"{time_str} 📅 {date_str} | V14.1")
    if st.button("🇹🇭 ตลาดหุ้นไทย"): st.session_state.market = 'th'; st.session_state.page = 'SubMenu'; st.rerun()
    if st.button("🇺🇸 ตลาดหุ้นอเมริกา"): st.session_state.market = 'us'; st.session_state.page = 'SubMenu'; st.rerun()
    st.write('---')
    st.markdown(f'<div style="display: flex; justify-content: center; width: 100%; margin: 10px 0;"><img src="https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000" width="380" style="border-radius: 12px;"></div>', unsafe_allow_html=True)

elif st.session_state.page == 'SubMenu':
    m_label = "🇹🇭 THAI MENU" if st.session_state.market == 'th' else "🇺🇸 US MENU"
    centered_header(m_label, f"{time_str} 📅 {date_str} | V14.1")
    if st.button("📋 WATCHLIST"): st.session_state.page = 'Watch'; st.rerun()
    if st.button("🔍 MARKET SCAN"): st.session_state.page = 'Scan'; st.rerun()
    if st.button("🏠 กลับหน้าหลัก"): st.session_state.page = 'Home'; st.session_state.market = None; st.rerun()

elif st.session_state.page == 'Watch':
    m_code = "TH" if st.session_state.market == 'th' else "US"
    centered_header(f"📋 WATCHLIST ({m_code})", f"{time_str} 📅 {date_str} | V14.1")
    if st.button("⬅ กลับเมนูตลาด"): st.session_state.page = 'SubMenu'; st.rerun()
    
    with st.expander("⚙️ Manage List", expanded=True):
        new_t = st.text_input("Ticker:", label_visibility="collapsed", placeholder="e.g. PTT").upper()
        if st.button("➕ Add"): 
            manage_storage(st.session_state.market, new_t, "add"); st.cache_data.clear(); st.rerun()
        st.markdown('<div class="del-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Delete"): 
            manage_storage(st.session_state.market, new_t, "delete"); st.cache_data.clear(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    cl = manage_storage(st.session_state.market)
    results = [fetch_verified_data(t, st.session_state.market) for t in cl]
    results = [r for r in results if r]
    
    # แสดงหัวตารางรอไว้แม้ไม่มีข้อมูล (เรียงคอลัมน์ตามสั่ง: ตัด Signal, ขยับ Value, จบด้วย RSI)
    cols = ["Ticker", "Prev", "Price", "Chg", "%Chg", "Value (M)", "TimeUpdate", "RSI"]
    df_display = pd.DataFrame(results) if results else pd.DataFrame(columns=cols)
    st.dataframe(df_display, use_container_width=True, hide_index=True)

elif st.session_state.page == 'Scan':
    centered_header(f"🔍 SIGNAL SCAN", f"{time_str} 📅 {date_str} | V14.1")
    if st.button("🏠 Home"): st.session_state.page = 'Home'; st.session_state.market = None; st.rerun()
    if st.button("⬅ กลับเมนูตลาด"): st.session_state.page = 'SubMenu'; st.rerun()
    m = st.session_state.market
    if st.button("🔄 รีเฟรชสัญญาณ"): st.cache_data.clear(); st.rerun()
    hist_df = st.session_state.th_logs if m == 'th' else st.session_state.us_logs
    st.dataframe(hist_df, use_container_width=True, hide_index=True)

time.sleep(600); st.rerun()
