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
if 'keys_seen' not in st.session_state: st.session_state.keys_seen = set()

# --- 2. UI SETUP & ABSOLUTE CENTERING (V13.8) ---
st.set_page_config(page_title="PPE Guardian V13.8", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stSidebar"], .st-emotion-cache-10o48ve, header, .stAppHeader { display: none !important; }
    .stApp { background-color: #0f172a; }
    
    /* ล็อกกึ่งกลางระดับ Container ใหญ่ที่สุด */
    .main .block-container {
        padding-top: 1rem !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        text-align: center !important;
        width: 100% !important;
    }

    /* บังคับทุกบรรทัดย่อยให้กึ่งกลาง (ป้องกันดีดซ้าย) */
    div[data-testid="stVerticalBlock"] > div {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        margin: 0 auto !important;
    }

    /* สไตล์ปุ่มกด */
    .stButton > button { 
        height: 48px !important; 
        border-radius: 10px !important; 
        font-size: 16px !important; 
        font-weight: bold !important; 
        color: #FFD700 !important; 
        background-color: #1e293b !important; 
        border: 2px solid #FFD700 !important;
        width: 280px !important;
        margin: 6px auto !important;
    }

    .del-btn button { color: #FF4B4B !important; border-color: #FF4B4B !important; }
    
    /* ประหยัดพื้นที่ Expander */
    .stExpander { width: 100% !important; margin-top: -10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INDICATOR ENGINE ---
@st.cache_data(ttl=60)
def fetch_verified_data(ticker, market_mode, is_scan=False):
    try:
        symbol = f"{ticker.upper()}.BK" if market_mode == "th" and ".BK" not in ticker.upper() else ticker.upper()
        df = yf.download(symbol, period="7d", interval="1h", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        ema8 = ta.ema(df['Close'], 8); ema20 = ta.ema(df['Close'], 20)
        hull = ta.hma(df['Close'], 30); vma5 = ta.sma(df['Volume'], 5)
        esa = ta.ema(df['Close'], 9); d = ta.ema(abs(df['Close'] - esa), 9)
        ci = (df['Close'] - esa) / (0.015 * d); wt1 = ta.ema(ci, 12); wt2 = ta.sma(wt1, 4)
        cp = float(df['Close'].iloc[-1]); h_curr = hull.iloc[-1]; h_prev = hull.iloc[-2]
        w1 = wt1.iloc[-1]; w2 = wt2.iloc[-2]; vol = df['Volume'].iloc[-1]; v5 = vma5.iloc[-1]; e8 = ema8.iloc[-1]
        last_time = df.index[-1].astimezone(pytz.timezone('Asia/Bangkok'))
        is_closed = (datetime.now(pytz.timezone('Asia/Bangkok')) - last_time) > timedelta(minutes=55)
        s_label, s_col = "-", "#FFD700"
        if cp > e8 and h_curr > h_prev and vol > (v5 * 1.2): s_label, s_col = "BUY", "#00FF00"
        elif w1 > w2 and w1 < -47 and cp > e8: s_label, s_col = "DEEP BUY", "#00FF00"
        elif w1 < w2 and w1 > 53: s_label, s_col = "P-SELL", "#FFA500"
        elif cp < ema20.iloc[-1] or h_curr < h_prev: s_label, s_col = "SELL", "#FF1100"
        if s_label == "-": return None
        display_label = "DEEP BUY" if not is_closed and s_label == "BUY" else s_label
        c_pp = float(df['Close'].iloc[-2]); chg = cp - c_pp
        val_raw = (cp * float(df['Volume'].iloc[-1])) / 1_000_000
        return {"Ticker": ticker.upper(), "Prev": f"{c_pp:.2f}", "Price": f"{cp:.2f}", "Chg": f"{chg:+.2f}", "%Chg": f"{(chg/c_pp)*100:.2f}%", "Signal": display_label, "Value (M)": f"{val_raw:.2f}M", "TimeUpdate": last_time.strftime("%H:%M %d/%m")}
    except: return None

# --- 4. NAVIGATION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 'market' not in st.session_state: st.session_state.market = None
now = datetime.now(pytz.timezone("Asia/Bangkok"))
time_str = now.strftime("%H:%M:%S"); date_str = now.strftime("%d/%m/%Y")

# --- 5. PAGE LOGIC ---
# 🔥 ฟังก์ชันสร้างหัวกระดาษกึ่งกลาง (ป้องกันดีดซ้ายถาวร)
def centered_header(title, subtitle):
    st.markdown(f"""
        <div style="text-align: center; width: 100%;">
            <h1 style="color: #FFD700; font-size: 32px; font-weight: 900; margin-bottom: 0px;">{title}</h1>
            <p style="color: #1E90FF; font-size: 13px; margin-top: 0px; margin-bottom: 10px;">{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)

if st.session_state.page == 'Home':
    centered_header("TRADING HOME", f"{time_str} 📅 {date_str} | V13.8")
    if st.button("🇹🇭 ตลาดหุ้นไทย"): st.session_state.market = 'th'; st.session_state.page = 'SubMenu'; st.rerun()
    if st.button("🇺🇸 ตลาดหุ้นอเมริกา"): st.session_state.market = 'us'; st.session_state.page = 'SubMenu'; st.rerun()
    st.write('---')
    st.markdown(f'<div style="display: flex; justify-content: center; width: 100%; margin: 10px 0;"><img src="https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000" width="380" style="border-radius: 12px;"></div>', unsafe_allow_html=True)

elif st.session_state.page == 'SubMenu':
    m_label = "🇹🇭 THAI MENU" if st.session_state.market == 'th' else "🇺🇸 US MENU"
    centered_header(m_label, f"{time_str} 📅 {date_str} | V13.8")
    if st.button("📋 WATCHLIST"): st.session_state.page = 'Watch'; st.rerun()
    if st.button("🔍 MARKET SCAN"): st.session_state.page = 'Scan'; st.rerun()
    if st.button("🏠 กลับหน้าหลัก"): st.session_state.page = 'Home'; st.session_state.market = None; st.rerun()

elif st.session_state.page == 'Watch':
    m_code = "TH" if st.session_state.market == 'th' else "US"
    centered_header(f"📋 WATCHLIST ({m_code})", f"{time_str} 📅 {date_str} | V13.8")
    
    # ปรับสมดุลปุ่มย้อนกลับให้ไม่ชิดหัวข้อเกินไป
    back_lbl = "⬅ กลับเมนูไทย" if st.session_state.market == 'th' else "⬅ กลับเมนู US"
    st.markdown('<div style="margin: 10px 0;">', unsafe_allow_html=True)
    if st.button(back_lbl): st.session_state.page = 'SubMenu'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.expander("⚙️ Manage List", expanded=True):
        new_t = st.text_input("Ticker:", label_visibility="collapsed", placeholder="e.g. PTT").upper()
        if st.button("➕ Add"): 
            manage_storage(st.session_state.market, new_t, "add"); st.cache_data.clear(); st.rerun()
        st.markdown('<div class="del-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Delete"): 
            manage_storage(st.session_state.market, new_t, "delete"); st.cache_data.clear(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    cl = manage_storage(st.session_state.market); results = [fetch_verified_data(t, st.session_state.market) for t in cl]; results = [r for r in results if r]
    if results: st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

elif st.session_state.page == 'Scan':
    centered_header(f"🔍 SIGNAL SCAN", f"{time_str} 📅 {date_str} | V13.8")
    if st.button("🏠 Home"): st.session_state.page = 'Home'; st.session_state.market = None; st.rerun()
    if st.button("⬅ กลับเมนูตลาด"): st.session_state.page = 'SubMenu'; st.rerun()
    m = st.session_state.market
    if st.button("🔄 รีเฟรชสัญญาณ"): st.cache_data.clear(); st.rerun()
    for t in manage_storage(m): fetch_verified_data(t, m, is_scan=True)
    hist_df = st.session_state.th_logs if m == 'th' else st.session_state.us_logs
    if not hist_df.empty: st.dataframe(hist_df, use_container_width=True, hide_index=True)

time.sleep(600); st.rerun()
