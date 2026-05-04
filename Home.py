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

# --- 2. UI SETUP & GLOBAL CENTERING (V12.0) ---
st.set_page_config(page_title="PPE Guardian V12.0", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* ปิดส่วนหัวและเมนูของ Streamlit */
    [data-testid="stSidebar"], .st-emotion-cache-10o48ve, header, .stAppHeader { display: none !important; }
    
    /* บังคับทุกอย่างในหน้าจอให้จัดกึ่งกลาง (The Fix) */
    .stApp { background-color: #0f172a; }
    .main .block-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        padding-top: 2rem;
    }
    
    /* บังคับปุ่มและข้อความให้เด้งมากึ่งกลาง */
    div[data-testid="stVerticalBlock"] {
        align-items: center !important;
        width: 100%;
    }

    h1, h2, h3, p, span, label { color: #FFD700 !important; text-align: center; }
    .classic-header { color: #1E90FF !important; font-size: 14px; font-weight: 600; text-align: center; margin-top: 15px; }

    /* สไตล์ปุ่มแนวตั้ง V12.0 */
    .stButton > button { 
        height: 55px !important; 
        border-radius: 12px !important; 
        font-size: 18px !important; 
        font-weight: bold !important; 
        color: #FFD700 !important; 
        background-color: #1e293b !important; 
        border: 2px solid #FFD700 !important;
        width: 260px !important; /* กว้างเท่ากันทั้งสองปุ่ม */
        margin: 10px auto !important; /* จัดกึ่งกลางเป๊ะ */
        display: block !important;
    }
    
    .stButton > button:hover {
        background-color: #334155 !important;
        border-color: #ffffff !important;
        transform: scale(1.05);
    }

    div.stButton > button[kind="primary"] { background-color: #FF0000 !important; color: white !important; border: none !important; width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INDICATOR ENGINE ---
@st.cache_data(ttl=60)
def fetch_verified_data(ticker, market_mode, is_scan=False):
    try:
        symbol = f"{ticker.upper()}.BK" if market_mode == "th" and ".BK" not in ticker.upper() else ticker.upper()
        df = yf.download(symbol, period="7d", interval="1h", progress=False)
        if df.empty or len(df) < 20: return None
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
        v_col = "#808080" if val_raw <= 10 else ("#00BFFF" if val_raw <= 100 else "#FF00FF")

        res = {
            "Ticker": ticker.upper(), "Prev": f"{c_pp:.2f}", "Price": f"{cp:.2f}", 
            "Chg": f"{chg:+.2f}", "%Chg": f"{(chg/c_pp)*100:.2f}%", 
            "Signal": display_label, "Value (M)": f"{val_raw:.2f}M",
            "TimeUpdate": last_time.strftime("%H:%M %d/%m"), 
            "PriceCol": "#00FF00" if chg > 0 else "#FF1100", "SigCol": s_col, "ValCol": v_col
        }

        if is_scan:
            key = f"{market_mode}_{ticker}_{display_label}_{last_time.strftime('%Y%m%d%H')}"
            if key not in st.session_state.keys_seen:
                st.session_state.keys_seen.add(key)
                new_row = pd.DataFrame([res])
                if market_mode == "th": st.session_state.th_logs = pd.concat([new_row, st.session_state.th_logs], ignore_index=True)
                else: st.session_state.us_logs = pd.concat([new_row, st.session_state.us_logs], ignore_index=True)
        return res
    except: return None

# --- 4. NAVIGATION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 'market' not in st.session_state: st.session_state.market = None

now = datetime.now(pytz.timezone("Asia/Bangkok"))
time_str = now.strftime("%H:%M:%S")
date_str = now.strftime("%d/%m/%Y")

# --- 5. PAGE LOGIC ---

if st.session_state.page == 'Home':
    st.write('<div style="margin-bottom:10px;"><span style="color:#FFD700; font-size:40px; font-weight:900;">TRADING HOME</span></div>', unsafe_allow_html=True)
    
    # ปุ่มแนวตั้ง จัดกึ่งกลางจออัตโนมัติด้วย CSS V12.0
    if st.button("🇹🇭 ตลาดหุ้นไทย"):
        st.session_state.market = 'th'; st.session_state.page = 'SubMenu'; st.rerun()
        
    if st.button("🇺🇸 ตลาดหุ้นอเมริกา"):
        st.session_state.market = 'us'; st.session_state.page = 'SubMenu'; st.rerun()
    
    # แถบข้อมูลกึ่งกลาง
    st.write(f'<div class="classic-header">{time_str} 📅 {date_str} | PPE Guardian V12.0</div>', unsafe_allow_html=True)
    st.write('---')
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", width=400)

elif st.session_state.page == 'SubMenu':
    st.write(f'<div class="classic-header">{time_str} 📅 {date_str} | PPE Guardian V12.0</div>', unsafe_allow_html=True)
    if st.button("🏠 กลับหน้าหลัก"):
        st.session_state.page = 'Home'; st.session_state.market = None; st.rerun()
            
    m = st.session_state.market
    st.write(f"### {'🇹🇭 THAI MENU' if m=='th' else '🇺🇸 US MENU'}")
    st.write('---')
    if st.button("📋 WATCHLIST"):
        st.session_state.page = 'Watch'; st.rerun()
    if st.button("🔍 MARKET SCAN"):
        st.session_state.page = 'Scan'; st.rerun()

elif st.session_state.page == 'Watch':
    st.write(f'<div class="classic-header">{time_str} 📅 {date_str} | PPE Guardian V12.0</div>', unsafe_allow_html=True)
    if st.button("🏠 Home"): st.session_state.page = 'Home'; st.session_state.market = None; st.rerun()
    if st.button("⬅ กลับเมนูตลาด"): st.session_state.page = 'SubMenu'; st.rerun()

    m = st.session_state.market
    st.write(f"### 📋 WATCHLIST ({'TH' if m=='th' else 'US'})")
    with st.expander("➕ เพิ่มหุ้น", expanded=True):
        new_t = st.text_input("ระบุชื่อหุ้น:").upper()
        if st.button("✅ ยืนยันเพิ่ม"):
            manage_storage(m, new_t, "add"); st.cache_data.clear(); st.rerun()
    
    cl = manage_storage(m)
    results = [fetch_verified_data(t, m) for t in cl]
    results = [r for r in results if r]
    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)

elif st.session_state.page == 'Scan':
    st.write(f'<div class="classic-header">{time_str} 📅 {date_str} | PPE Guardian V12.0</div>', unsafe_allow_html=True)
    if st.button("🏠 Home"): st.session_state.page = 'Home'; st.session_state.market = None; st.rerun()
    if st.button("⬅ กลับเมนูตลาด"): st.session_state.page = 'SubMenu'; st.rerun()

    m = st.session_state.market
    st.write(f"### 🔍 SIGNAL SCAN ({'TH' if m=='th' else 'US'})")
    if st.button("🔄 รีเฟรชสัญญาณ"): st.cache_data.clear(); st.rerun()
    for t in manage_storage(m): fetch_verified_data(t, m, is_scan=True)
    hist_df = st.session_state.th_logs if m == 'th' else st.session_state.us_logs
    if not hist_df.empty:
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

time.sleep(600); st.rerun()
