import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz
import time
import os

# --- 1. CORE STORAGE ---
def manage_storage(mode, ticker=None, action="load"):
    file_path = f"{mode}_list.txt"
    if not os.path.exists(file_path):
        with open(file_path, "w") as f: f.write("PTT,DELTA" if mode == "th" else "IONQ,NVDA")
    with open(file_path, "r") as f:
        data = f.read().strip()
        current_data = [x.strip().upper() for x in data.split(",") if x.strip()]
    if action == "add" and ticker:
        ticker = ticker.strip().upper()
        if ticker not in current_data:
            current_data.append(ticker)
            with open(file_path, "w") as f: f.write(",".join(current_data))
    elif action == "delete" and ticker in current_data:
        current_data.remove(ticker)
        with open(file_path, "w") as f: f.write(",".join(current_data))
    return current_data

# --- 2. UI SETUP & CLEAN CSS ---
st.set_page_config(page_title="PPE Guardian V16.8", layout="wide", initial_sidebar_state="collapsed")

if 'signal_history' not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=["Ticker", "Prev", "Price", "Chg", "%Chg", "Signal", "TimeUpdate", "RawTime", "m_chg"])

if 'page' not in st.query_params: st.query_params['page'] = 'Home'
curr_p = st.query_params.get('page', 'Home')
curr_m = st.query_params.get('market', None)

st.markdown("""
    <style>
    [data-testid="stSidebar"], header, .stAppHeader { display: none !important; }
    .stApp { background-color: #0f172a; }
    .stApp .main .block-container {
        display: flex !important; flex-direction: column !important;
        align-items: center !important; justify-content: flex-start !important;
        width: 100% !important; margin: 0 auto !important;
    }
    div[data-testid="stVerticalBlock"] > div, div.stButton {
        display: flex !important; justify-content: center !important; width: 100% !important;
    }
    .stButton > button { 
        height: 52px !important; width: 320px !important;
        border-radius: 14px !important; font-size: 18px !important; 
        font-weight: bold !important; color: #FFD700 !important; 
        background-color: #1e293b !important; border: 2px solid #FFD700 !important; 
        margin: 10px auto !important; display: block !important;
    }
    .del-btn button { color: #FF4B4B !important; border-color: #FF4B4B !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE ENGINE ---
def fetch_data(ticker, mode):
    try:
        sym = f"{ticker.upper()}.BK" if mode == "th" else ticker.upper()
        t_obj = yf.Ticker(sym)
        hist = t_obj.history(period="5d", interval="1d")
        if hist.empty: return None
        
        prev_close = float(hist['Close'].iloc[-2])
        current_price = float(t_obj.fast_info['last_price'])
        current_vol = float(t_obj.fast_info['last_volume'])
        
        df = t_obj.history(period="1mo", interval="1h")
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        rsi = ta.rsi(df['Close'], length=14)
        e8 = ta.ema(df['Close'], 8); h = ta.hma(df['Close'], 30)
        
        chg = current_price - prev_close
        pct_chg = (chg / prev_close) * 100
        
        sig = "-"
        if current_price > e8.iloc[-1] and h.iloc[-1] > h.iloc[-2]: sig = "BUY"
        elif current_price < ta.ema(df['Close'], 20).iloc[-1]: sig = "SELL"
        
        now = datetime.now(pytz.timezone("Asia/Bangkok"))
        return {"Ticker": ticker.upper(), "Prev": prev_close, "Price": current_price, 
                "Chg": chg, "%Chg": pct_chg, "Value (M)": (current_price * current_vol) / 1_000_000, 
                "RSI": rsi.iloc[-1] if not rsi.empty else 0, "TimeUpdate": now.strftime("%H:%M:%S %d/%m"), 
                "RawTime": now, "Signal": sig, "m_chg": chg}
    except: return None

def apply_styles(data):
    styles = pd.DataFrame('', index=data.index, columns=data.columns)
    for i in range(len(data)):
        row = data.iloc[i]
        # สีอิงตามการเปลี่ยนแปลงราคา (เขียว/แดง/เหลือง)
        m_c = 'color: #00FF00' if row['m_chg'] > 0 else ('color: #FF0000' if row['m_chg'] < 0 else 'color: #FFD700')
        
        # ปรับ Ticker และ TimeUpdate ให้อิงตามราคาสี m_c
        for col in ["Ticker", "TimeUpdate", "Price", "Chg", "%Chg", "Value (M)"]:
            if col in data.columns: styles.at[data.index[i], col] = m_c
            
        # ช่อง Signal แยกตามสัญญาณ BUY/SELL
        if "Signal" in data.columns:
            styles.at[data.index[i], "Signal"] = 'color: #00FF00' if row['Signal'] == "BUY" else ('color: #FF0000' if row['Signal'] == "SELL" else 'color: #FFD700')
        
        if "Prev" in data.columns: styles.at[data.index[i], "Prev"] = 'color: #FFD700'
        if "RSI" in data.columns:
            styles.at[data.index[i], "RSI"] = 'color: #FF0000' if row['RSI'] < 30 else ('color: #00FF00' if row['RSI'] > 70 else 'color: #FFD700')
    return styles

# --- 4. NAVIGATION ---
def go(p, m=None):
    st.query_params['page'] = p
    if m: st.query_params['market'] = m
    st.rerun()

def hdr(t, s):
    st.markdown(f'<div style="text-align: center;"><h1 style="color: #FFD700; margin:0;">{t}</h1><p style="color: #1E90FF;">{s}</p></div>', unsafe_allow_html=True)

# --- 5. DISPATCHER ---
t_now = datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S 📅 %d/%m/%Y")

if curr_p == 'Home':
    hdr("TRADING HOME", t_now)
    if st.button("🇹🇭 ตลาดหุ้นไทย"): go('SubMenu', 'th')
    if st.button("🇺🇸 ตลาดหุ้นอเมริกา"): go('SubMenu', 'us')
    st.write('---')

elif curr_p == 'SubMenu':
    f = "🇹🇭" if curr_m == 'th' else "🇺🇸"
    hdr(f"{f} MENU", t_now)
    if st.button("📋 WATCHLIST"): go('Watch', curr_m)
    if st.button("🔍 MARKET SCAN"): go('Scan', curr_m)
    if st.button("🏠 กลับหน้าหลัก"): go('Home')

elif curr_p == 'Watch':
    f = "🇹🇭" if curr_m == 'th' else "🇺🇸"
    hdr(f"{f} WATCHLIST", t_now)
    if st.button("⬅ กลับเมนูตลาด"): go('SubMenu', curr_m)
    with st.expander("⚙️ Manage List", expanded=False):
        nt = st.text_input("Ticker:", placeholder="e.g. BANPU", key="in_w").upper()
        if st.button("➕ Add"): manage_storage(curr_m, nt, "add"); st.rerun()
        st.markdown('<div class="del-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Delete"): manage_storage(curr_m, nt, "delete"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    res = [fetch_data(t, curr_m) for t in manage_storage(curr_m)]
    res = [r for r in res if r]
    if res:
        df = pd.DataFrame(res)
        st.dataframe(df.style.apply(apply_styles, axis=None).format({"Prev":"{:.2f}","Price":"{:.2f}","Chg":"{:+.2f}","%Chg":"{:+.2f}%","Value (M)":"{:.2f}M","RSI":"{:.2f}"}), 
                     use_container_width=True, hide_index=True, column_order=["Ticker","Prev","Price","Chg","%Chg","Value (M)","RSI","TimeUpdate"])

elif curr_p == 'Scan':
    f = "🇹🇭" if curr_m == 'th' else "🇺🇸"
    hdr(f"{f} SCAN", t_now)
    if st.button("⬅ กลับเมนูตลาด"): go('SubMenu', curr_m)
    new_results = [fetch_data(t, curr_m) for t in manage_storage(curr_m)]
    new_results = [r for r in new_results if r and r['Signal'] != "-"]
    if new_results:
        new_df = pd.DataFrame(new_results)
        combined = pd.concat([new_df, st.session_state.signal_history]).drop_duplicates(subset=['Ticker', 'Signal'], keep='first')
        combined = combined.sort_values(by="RawTime", ascending=False).head(30)
        st.session_state.signal_history = combined
    if not st.session_state.signal_history.empty:
        st.dataframe(st.session_state.signal_history.style.apply(apply_styles, axis=None).format({"Prev":"{:.2f}","Price":"{:.2f}","Chg":"{:+.2f}","%Chg":"{:+.2f}%"}), 
                     use_container_width=True, hide_index=True, column_order=["Ticker","Prev","Price","Chg","%Chg","Signal","TimeUpdate"])

time.sleep(60); st.rerun()
