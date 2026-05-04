import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz
import time
import os

# --- 1. MEMORY & HISTORY SYSTEM ---
def manage_list(mode, ticker=None, action="load"):
    file_path = f"{mode}_list.txt"
    defaults = ['PTT', 'DELTA', 'ADVANC'] if mode == "th" else ['IONQ', 'NVDA', 'IREN']
    if not os.path.exists(file_path):
        with open(file_path, "w") as f: f.write(",".join(defaults))
    
    # อ่านข้อมูลล่าสุดจากไฟล์เสมอ
    with open(file_path, "r") as f:
        data = f.read().strip()
        current_data = [x for x in data.split(",") if x] if data else defaults
    
    if action == "add" and ticker:
        ticker = ticker.strip().upper()
        if ticker and ticker not in current_data:
            current_data.append(ticker)
            with open(file_path, "w") as f: f.write(",".join(current_data))
    elif action == "delete" and ticker:
        if ticker in current_data:
            current_data.remove(ticker)
            with open(file_path, "w") as f: f.write(",".join(current_data))
    return current_data

if 'signal_history' not in st.session_state:
    st.session_state.signal_history = pd.DataFrame()
if 'last_alert_key' not in st.session_state:
    st.session_state.last_alert_key = set()

# --- 2. UI SETUP ---
st.set_page_config(page_title="PPE Guardian V10.0", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stSidebar"], .st-emotion-cache-10o48ve, header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { width: 0px !important; }
    .stApp { background-color: #0f172a; }
    h1, h2, h3, p, span, label { color: #FFD700 !important; }
    .block-container { padding: 0.5rem 0.2rem !important; }
    .classic-header { color: #1E90FF !important; font-size: 13px; font-weight: 600; text-align: center; margin-bottom: 5px; }
    .stDataFrame [data-testid="stTable"] td { font-size: 11px !important; padding: 2px !important; }
    .stDataFrame [data-testid="stTable"] th { font-size: 11px !important; color: #FFD700 !important; }
    .stButton > button { height: 35px !important; border-radius: 8px !important; font-size: 13px !important; width: 100%; }
    div.stButton > button[kind="primary"] { background-color: #FF0000 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE ENGINE ---
@st.cache_data(ttl=60) # เพิ่มระบบ Cache เพื่อความเร็ว แต่ Reset เมื่อมีการแอดหุ้น
def fetch_verified_data(ticker, mode, is_scan=False):
    try:
        symbol = f"{ticker.upper()}.BK" if ".BK" not in ticker.upper() and mode in ['TW', 'TS'] else ticker.upper()
        df = yf.download(symbol, period="7d", interval="1h", progress=False)
        if df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        ema8 = ta.ema(df['Close'], 8); ema20 = ta.ema(df['Close'], 20)
        hull = ta.hma(df['Close'], 30); vma5 = ta.sma(df['Volume'], 5)
        esa = ta.ema(df['Close'], 9); d = ta.ema(abs(df['Close'] - esa), 9)
        ci = (df['Close'] - esa) / (0.015 * d); wt1 = ta.ema(ci, 12); wt2 = ta.sma(wt1, 4)

        current_idx = len(df) - 1
        cp = float(df['Close'].iloc[current_idx])
        h_curr, h_prev = hull.iloc[current_idx], hull.iloc[current_idx-1]
        w1, w2 = wt1.iloc[current_idx], wt2.iloc[current_idx]
        vol, v5, e8 = df['Volume'].iloc[current_idx], vma5.iloc[current_idx], ema8.iloc[current_idx]
        
        last_time = df.index[-1].astimezone(pytz.timezone('Asia/Bangkok'))
        is_candle_closed = (datetime.now(pytz.timezone('Asia/Bangkok')) - last_time) > timedelta(minutes=55)

        s_label, s_col = "-", "#FFD700"
        if cp > e8 and h_curr > h_prev and vol > (v5 * 1.2): s_label, s_col = "BUY", "#00FF00"
        elif w1 > w2 and w1 < -47 and cp > e8: s_label, s_col = "DEEP BUY", "#00FF00"
        elif w1 < w2 and w1 > 53: s_label, s_col = "P-SELL", "#FFA500"
        elif cp < ema20.iloc[current_idx] or h_curr < h_prev: s_label, s_col = "SELL", "#FF1100"

        if s_label == "-": return None
        
        display_label = s_label
        if not is_candle_closed and s_label == "BUY": display_label = "DEEP BUY"

        c_pp = float(df['Close'].iloc[-2])
        chg = cp - c_pp
        val_raw = (cp * float(df['Volume'].iloc[-1])) / 1_000_000
        v_col = "#808080" if val_raw <= 10 else ("#00BFFF" if val_raw <= 100 else "#FF00FF")

        res = {
            "Ticker": ticker.upper(), "Prev": f"{c_pp:.2f}", "Price": f"{cp:.2f}", 
            "Chg": f"{chg:+.2f}", "%Chg": f"{(chg/c_pp)*100:.2f}%", 
            "Signal": display_label, "Value (M)": f"{val_raw:.2f}M",
            "TimeUpdate": last_time.strftime("%H:%M %d/%m"), "RawTime": last_time,
            "PriceCol": "#00FF00" if chg > 0 else "#FF1100", "SigCol": s_col, "ValCol": v_col,
            "Market": "th" if mode in ['TW', 'TS'] else "us"
        }

        alert_key = f"{ticker}_{display_label}_{last_time.strftime('%Y%m%d%H')}"
        if is_scan and alert_key not in st.session_state.last_alert_key:
            st.session_state.last_alert_key.add(alert_key)
            new_row = pd.DataFrame([res])
            st.session_state.signal_history = pd.concat([new_row, st.session_state.signal_history], ignore_index=True)

        return res
    except: return None

def apply_style(row):
    return [f'color: {row["SigCol"]}' if col in ["Ticker", "Signal", "TimeUpdate"] else 
            (f'color: {row["PriceCol"]}' if col in ["Price", "Chg", "%Chg"] else 
            (f'color: {row["ValCol"]}' if col == "Value (M)" else '')) for col in row.index]

# --- 4. NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 'edit_mode' not in st.session_state: st.session_state.edit_mode = False
p = st.session_state.page

st.button("🏠 HOME", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home", "edit_mode": False}), type="primary" if p == 'Home' else "secondary")
c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 THAI WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TW", "edit_mode": False}), type="primary" if p == 'TW' else "secondary")
    st.button("🇹🇭 THAI MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TS", "edit_mode": False}), type="primary" if p == 'TS' else "secondary")
with c2:
    st.button("🇺🇸 US WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "UW", "edit_mode": False}), type="primary" if p == 'UW' else "secondary")
    st.button("🇺🇸 US MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US", "edit_mode": False}), type="primary" if p == 'US' else "secondary")

st.write(f'<div class="classic-header">PPE Guardian V10.0 | {datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

# --- 5. CONTENT ---
if p == 'Home':
    st.write('<div style="text-align:center; padding:10px;"><span style="color:#FFD700; font-size:30px; font-weight:900;">WELCOME</span><br><span style="color:#FFD700; font-size:35px; font-weight:900;">TRADING HOME</span></div>', unsafe_allow_html=True)
    cl, cm, cr = st.columns([1, 1.5, 1]); cm.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)

elif p in ['TW', 'UW', 'TS', 'US']:
    m_key = "th" if p in ['TW', 'TS'] else "us"
    
    if 'W' in p:
        with st.expander(f"➕ Manage {m_key.upper()} List", expanded=True):
            new_t = st.text_input(f"Add Ticker:", key=f"in_{m_key}").upper()
            ca, ce = st.columns(2)
            if ca.button("✅ Add"):
                if new_t: 
                    manage_list(m_key, new_t, "add")
                    st.cache_data.clear() # ล้าง Cache ทันทีที่แอด
                    st.rerun()
            if ce.button("🛠️ Toggle Edit"):
                st.session_state.edit_mode = not st.session_state.edit_mode
                st.rerun()
        
        # ย้ายการอ่านไฟล์มาไว้ "หลัง" ปุ่มกด เพื่อให้ข้อมูลเป็นปัจจุบันที่สุด
        curr_list = manage_list(m_key)
        results = [fetch_verified_data(t, p) for t in curr_list]
        results = [r for r in results if r is not None]
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df.style.apply(apply_style, axis=1), use_container_width=True, hide_index=True, column_order=["Ticker", "Prev", "Price", "Chg", "%Chg", "Value (M)", "TimeUpdate"])
            if st.session_state.edit_mode:
                st.write("---")
                st.write("🗑️ **Select to Remove:**")
                del_cols = st.columns(4)
                for i, t in enumerate(curr_list):
                    if del_cols[i % 4].button(f"✖ {t}", key=f"d_{t}"): 
                        manage_list(m_key, t, "delete")
                        st.cache_data.clear()
                        st.rerun()

    else:
        # ย้ายปุ่มมาไว้ฝั่งซ้ายแทนตัวหนังสือ US Signal History
        c_btn, c_spacer = st.columns([1, 3])
        if c_btn.button("🔄 Manual Refresh"): 
            st.cache_data.clear()
            st.rerun()
        
        curr_list = manage_list(m_key)
        for t in curr_list: fetch_verified_data(t, p, is_scan=True)
        if not st.session_state.signal_history.empty:
            df_hist = st.session_state.signal_history
            filtered_df = df_hist[df_hist['Market'] == m_key]
            st.dataframe(filtered_df.style.apply(apply_style, axis=1), use_container_width=True, hide_index=True, column_order=["Ticker", "Prev", "Price", "Chg", "%Chg", "Signal", "TimeUpdate"])

time.sleep(600)
st.rerun()
