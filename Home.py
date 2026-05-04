import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
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

# --- 2. UI SETUP ---
st.set_page_config(page_title="PPE Guardian V15.6", layout="wide", initial_sidebar_state="collapsed")

# ป้องกันหน้าเด้งโดยการเช็ค session_state ให้เข้มข้นขึ้น
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 'market' not in st.session_state: st.session_state.market = None

st.markdown("""
    <style>
    [data-testid="stSidebar"], .st-emotion-cache-10o48ve, header, .stAppHeader { display: none !important; }
    .stApp { background-color: #0f172a; }
    .stApp .main .block-container {
        display: flex !important; flex-direction: column !important;
        align-items: center !important; justify-content: flex-start !important;
        text-align: center !important; width: 100% !important; margin: 0 auto !important;
    }
    div[data-testid="stVerticalBlock"] { align-items: center !important; width: 100% !important; }
    .stButton > button { 
        height: 50px !important; border-radius: 12px !important; font-size: 17px !important; 
        font-weight: bold !important; color: #FFD700 !important; background-color: #1e293b !important; 
        border: 2px solid #FFD700 !important; width: 300px !important; margin: 8px auto !important;
    }
    .scan-btn button { background-color: #0ea5e9 !important; color: white !important; border: none !important; }
    .del-btn button { color: #FF4B4B !important; border-color: #FF4B4B !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INDICATOR ENGINE ---
@st.cache_data(ttl=60)
def fetch_verified_data(ticker, market_mode):
    try:
        symbol = f"{ticker.upper()}.BK" if market_mode == "th" and ".BK" not in ticker.upper() else ticker.upper()
        df = yf.download(symbol, period="1mo", interval="1h", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        ema8 = ta.ema(df['Close'], 8); ema20 = ta.ema(df['Close'], 20)
        hull = ta.hma(df['Close'], 30); vma5 = ta.sma(df['Volume'], 5)
        esa = ta.ema(df['Close'], 9); d = ta.ema(abs(df['Close'] - esa), 9)
        ci = (df['Close'] - esa) / (0.015 * d); wt1 = ta.ema(ci, 12); wt2 = ta.sma(wt1, 4)
        
        cp = float(df['Close'].iloc[-1]); h_curr = hull.iloc[-1]; h_prev = hull.iloc[-2]
        w1 = wt1.iloc[-1]; w2 = wt2.iloc[-2]; vol = df['Volume'].iloc[-1]; v5 = vma5.iloc[-1]
        e8 = ema8.iloc[-1]; e20 = ema20.iloc[-1]
        
        s_label = "-"
        if cp > e8 and h_curr > h_prev and vol > (v5 * 1.2): s_label = "BUY"
        elif w1 > w2 and w1 < -47 and cp > e8: s_label = "DEEP BUY"
        elif cp < e20 or h_curr < h_prev: s_label = "SELL"
        elif cp < e8 and h_curr < h_prev: s_label = "P-SELL"
        
        c_pp = float(df['Close'].iloc[-2])
        p_p_close = float(df['Close'].iloc[-3])
        return {
            "Ticker": ticker.upper(), "Prev": c_pp, "Price": cp, "Chg": cp - c_pp,
            "%Chg": ((cp - c_pp) / c_pp) * 100, "Value (M)": (cp * vol) / 1_000_000,
            "TimeUpdate": df.index[-1].astimezone(pytz.timezone('Asia/Bangkok')).strftime("%H:%M %d/%m"),
            "Signal": s_label, "prev_signal": c_pp - p_p_close, "main_chg": cp - c_pp
        }
    except: return None

def apply_v15_6_styling(data):
    styles = pd.DataFrame('', index=data.index, columns=data.columns)
    for i in range(len(data)):
        row = data.iloc[i]
        sig_c = 'color: #00FF00' if row['Signal'] in ["BUY", "DEEP BUY"] else 'color: #FF0000'
        for col in ["Ticker", "Signal", "TimeUpdate"]:
            if col in data.columns: styles.at[data.index[i], col] = sig_c
        p_c = 'color: #00FF00' if row['prev_signal'] > 0 else ('color: #FF0000' if row['prev_signal'] < 0 else 'color: #FFD700')
        if "Prev" in data.columns: styles.at[data.index[i], "Prev"] = p_c
        m_c = 'color: #00FF00' if row['main_chg'] > 0 else ('color: #FF0000' if row['main_chg'] < 0 else 'color: #FFD700')
        for col in ["Price", "Chg", "%Chg", "Value (M)"]:
            if col in data.columns: styles.at[data.index[i], col] = m_c
    return styles

# --- 4. NAVIGATION ---
now = datetime.now(pytz.timezone("Asia/Bangkok"))
time_str = now.strftime("%H:%M:%S"); date_str = now.strftime("%d/%m/%Y")

def centered_header(title, subtitle):
    st.markdown(f"""<div style="text-align: center; width: 100%;"><h1 style="color: #FFD700; font-size: 32px; font-weight: 900; margin-bottom: 0px;">{title}</h1><p style="color: #1E90FF; font-size: 13px; margin-top: 0px; margin-bottom: 10px;">{subtitle}</p></div>""", unsafe_allow_html=True)

# --- 5. PAGE LOGIC ---
if st.session_state.page == 'Home':
    centered_header("TRADING HOME", f"{time_str} 📅 {date_str} | V15.6")
    if st.button("🇹🇭 ตลาดหุ้นไทย"): st.session_state.market = 'th'; st.session_state.page = 'SubMenu'; st.rerun()
    if st.button("🇺🇸 ตลาดหุ้นอเมริกา"): st.session_state.market = 'us'; st.session_state.page = 'SubMenu'; st.rerun()
    st.write('---')
    st.markdown(f'<div style="display: flex; justify-content: center; width: 100%; margin: 10px 0;"><img src="https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000" width="380" style="border-radius: 12px;"></div>', unsafe_allow_html=True)

elif st.session_state.page == 'SubMenu':
    flag = "🇹🇭" if st.session_state.market == 'th' else "🇺🇸"
    centered_header(f"{flag} MENU", f"{time_str} 📅 {date_str}")
    if st.button("📋 WATCHLIST"): st.session_state.page = 'Watch'; st.rerun()
    if st.button("🔍 MARKET SCAN"): st.session_state.page = 'Scan'; st.rerun()
    if st.button("🏠 กลับหน้าหลัก"): st.session_state.page = 'Home'; st.session_state.market = None; st.rerun()

elif st.session_state.page in ['Watch', 'Scan']:
    flag = "🇹🇭" if st.session_state.market == 'th' else "🇺🇸"
    title_label = "WATCHLIST" if st.session_state.page == 'Watch' else "SCAN"
    centered_header(f"{flag} {title_label}", f"{time_str} 📅 {date_str}")
    
    if st.button("⬅ กลับเมนูตลาด"): st.session_state.page = 'SubMenu'; st.rerun()
    
    # หน้า WATCH ให้มี Manage List สำหรับจัดการหุ้น
    if st.session_state.page == 'Watch':
        with st.expander("⚙️ Manage List", expanded=False):
            new_t = st.text_input("Ticker:", placeholder="e.g. PTT", key="add_input").upper()
            if st.button("➕ Add"): manage_storage(st.session_state.market, new_t, "add"); st.cache_data.clear(); st.rerun()
            st.markdown('<div class="del-btn">', unsafe_allow_html=True)
            if st.button("🗑️ Delete"): manage_storage(st.session_state.market, new_t, "delete"); st.cache_data.clear(); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # หน้า SCAN ตัด Manage List ออก และมีแค่ปุ่ม Manual Scan
    elif st.session_state.page == 'Scan':
        st.markdown('<div class="scan-btn">', unsafe_allow_html=True)
        if st.button("🔍 กดเพื่อสแกนใหม่ (Manual Scan)"): st.cache_data.clear(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    cl = manage_storage(st.session_state.market)
    results = [fetch_verified_data(t, st.session_state.market) for t in cl]
    results = [r for r in results if r]
    
    if st.session_state.page == 'Watch':
        watch_disp = ["Ticker", "Prev", "Price", "Chg", "%Chg", "Value (M)", "TimeUpdate"]
        if results:
            df = pd.DataFrame(results)
            styled = df.style.apply(apply_v15_6_styling, axis=None).format({"Prev": "{:.2f}", "Price": "{:.2f}", "Chg": "{:+.2f}", "%Chg": "{:+.2f}%", "Value (M)": "{:.2f}M"})
            st.dataframe(styled, use_container_width=True, hide_index=True, column_order=watch_disp)
    
    elif st.session_state.page == 'Scan':
        scan_cols = ["Ticker", "Prev", "Price", "Chg", "%Chg", "Signal", "TimeUpdate"]
        if results:
            df_scan = pd.DataFrame([r for r in results if r['Signal'] != "-"] )
            if not df_scan.empty:
                styled_s = df_scan.style.apply(apply_v15_6_styling, axis=None).format({"Prev": "{:.2f}", "Price": "{:.2f}", "Chg": "{:+.2f}", "%Chg": "{:+.2f}%"})
                st.dataframe(styled_s, use_container_width=True, hide_index=True, column_order=scan_cols)
            else: st.info("No active signals in your list.")

# Auto rerun
time.sleep(600); st.rerun()
