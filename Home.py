import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz
import time
import os

# --- 1. MEMORY SYSTEM ---
def manage_list(mode, ticker=None, action="load"):
    file_path = f"{mode}_list.txt"
    defaults = ['PTT', 'DELTA', 'ADVANC', 'EA', 'NEX', 'JTS'] if mode == "th" else ['IONQ', 'NVDA', 'IREN']
    if not os.path.exists(file_path):
        with open(file_path, "w") as f: f.write(",".join(defaults))
    with open(file_path, "r") as f:
        data = f.read().strip()
        current_data = data.split(",") if data else defaults
    if action == "add" and ticker and ticker not in current_data:
        current_data.append(ticker)
        with open(file_path, "w") as f: f.write(",".join(current_data))
    elif action == "delete" and ticker and ticker in current_data:
        current_data.remove(ticker)
        with open(file_path, "w") as f: f.write(",".join(current_data))
    return current_data

# --- 2. UI SETUP (เพิ่มการปิด Sidebar แบบถาวร) ---
# บรรทัดนี้สำคัญมาก: initial_sidebar_state="collapsed" คือการสั่งปิดแถบข้างตั้งแต่เริ่ม
st.set_page_config(page_title="PPE Guardian V9.9", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* ซ่อนแถบ Sidebar และปุ่มลูกศรเปิด Sidebar ทันที */
    [data-testid="stSidebar"], .st-emotion-cache-10o48ve, .st-emotion-cache-6qob1r {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        width: 0px !important;
    }
    
    /* CSS เดิมของคุณมิลค์ */
    h1, h2, h3, p, span, label { color: #FFD700 !important; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
    [data-testid="stStatusWidget"], header, .stAppHeader { display: none !important; }
    .stApp { background-color: #0f172a; }
    .classic-header { color: #1E90FF !important; font-size: 14px; font-weight: 600; margin-bottom: 10px; text-align: center; }
    .stTextInput > div > div > input { background-color: #1e293b !important; color: #FFD700 !important; border: 1px solid #FFD700 !important; }
    .stDataFrame [data-testid="stTable"] { background-color: #000000 !important; }
    .stDataFrame th { color: #FFD700 !important; background-color: #000000 !important; border: 0.1px solid #334155 !important; }
    .stDataFrame td { font-size: 13px !important; color: #FFD700 !important; border: 0.1px solid #334155 !important; }
    .stButton > button { height: 35px !important; border-radius: 8px !important; width: 100%; font-size: 14px !important; font-weight: 600 !important; }
    div.stButton > button[kind="primary"] { background-color: #FF0000 !important; color: white !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE ENGINE (EMA 8 + Wave Trend) ---
@st.cache_data(ttl=60)
def fetch_verified_data(ticker, mode):
    try:
        symbol = f"{ticker.upper()}.BK" if ".BK" not in ticker.upper() and mode in ['TW', 'TS'] else ticker.upper()
        df = yf.download(symbol, period="7d", interval="1h", progress=False)
        if df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        ema8 = ta.ema(df['Close'], 8); ema20 = ta.ema(df['Close'], 20)
        hull = ta.hma(df['Close'], 30); vma5 = ta.sma(df['Volume'], 5)
        esa = ta.ema(df['Close'], 9); d = ta.ema(abs(df['Close'] - esa), 9)
        ci = (df['Close'] - esa) / (0.015 * d); wt1 = ta.ema(ci, 12); wt2 = ta.sma(wt1, 4)

        s_label, s_col, found_time, raw_time, icon = "-", "#FFD700", "-", None, ""
        for i in range(len(df)-1, 0, -1):
            cp, h_curr, h_prev = float(df['Close'].iloc[i]), hull.iloc[i], hull.iloc[i-1]
            w1, w2, vol, v5, e8 = wt1.iloc[i], wt2.iloc[i], df['Volume'].iloc[i], vma5.iloc[i], ema8.iloc[i]
            if cp > e8 and h_curr > h_prev and vol > (v5 * 1.2): s_label, s_col, icon = "BUY", "#00FF00", "🚀 "
            elif w1 > w2 and w1 < -47 and cp > e8: s_label, s_col, icon = "DEEP BUY", "#00FF00", "▲ "
            elif w1 < w2 and w1 > 53: s_label, s_col, icon = "P-SELL", "#FFA500", "🔶 "
            elif cp < ema20.iloc[i] or h_curr < h_prev: s_label, s_col, icon = "SELL", "#FF1100", "🚨 "
            if s_label != "-":
                raw_time = df.index[i].astimezone(pytz.timezone('Asia/Bangkok'))
                found_time = raw_time.strftime("%H:%M %d/%m"); break

        if s_label == "-": return None
        c_cp, c_pp = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2])
        chg, t_val = c_cp - c_pp, (c_cp * float(df['Volume'].iloc[-1])) / 1_000_000
        return {"Ticker": ticker.upper(), "Prev": f"{c_pp:.2f}", "Price": f"{c_cp:.2f}", "Chg": f"{chg:+.2f}", "%Chg": f"{(chg/c_pp)*100:.2f}%", "Signal": f"{icon}{s_label}", "Value (M)": f"{t_val:.2f}M", "TimeUpdate": found_time, "RawTime": raw_time, "PriceCol": "#00FF00" if chg > 0 else "#FF1100", "SigCol": s_col}
    except: return None

def apply_style(row):
    return [f'color: {row["SigCol"]}' if col in ["Ticker", "Signal", "TimeUpdate"] else (f'color: {row["PriceCol"]}' if col in ["Price", "Chg", "%Chg"] else '') for col in row.index]

# --- 4. NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 'manage_mode' not in st.session_state: st.session_state.manage_mode = False

st.button("🏠 HOME", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home"}), type="primary" if st.session_state.page == 'Home' else "secondary")
c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 THAI WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TW"}), type="primary" if st.session_state.page == 'TW' else "secondary")
    st.button("🇹🇭 THAI MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TS"}), type="primary" if st.session_state.page == 'TS' else "secondary")
with c2:
    st.button("🇺🇸 US WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "UW"}), type="primary" if st.session_state.page == 'UW' else "secondary")
    st.button("🇺🇸 US MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US"}), type="primary" if st.session_state.page == 'US' else "secondary")

p = st.session_state.page
dt_now = datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%H:%M:%S | %d/%m/%Y')
st.write(f'<div class="classic-header">PPE Guardian V9.9 | {dt_now}</div>', unsafe_allow_html=True)

# --- 5. CONTENT ---
if p == 'Home':
    st.write('<div style="text-align:center; padding:10px;"><span style="color:#FFD700; font-size:30px; font-weight:900;">WELCOME</span><br><span style="color:#FFD700; font-size:35px; font-weight:900;">TRADING HOME</span></div>', unsafe_allow_html=True)
    cl, cm, cr = st.columns([1, 1.5, 1]); cm.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)

elif p in ['TW', 'UW', 'TS', 'US']:
    m_key = "th" if p in ['TW', 'TS'] else "us"
    curr_list = manage_list(m_key)
    if 'W' in p:
        with st.expander("➕ Manage Watchlist", expanded=True):
            new_t = st.text_input("Ticker:").upper()
            if new_t: manage_list(m_key, new_t, "add"); st.rerun()
            if st.button("🛠️ Edit Mode"): st.session_state.manage_mode = not st.session_state.manage_mode; st.rerun()
    else:
        if st.button("🔄 Manual Refresh"): st.cache_data.clear(); st.rerun()

    results = [fetch_verified_data(t, p) for t in curr_list]
    results = [r for r in results if r is not None]
    if results:
        df = pd.DataFrame(results)
        if 'S' in p: df = df.sort_values(by="RawTime", ascending=False).head(30)
        cols = ["Ticker", "Prev", "Price", "Chg", "%Chg", "Value (M)", "TimeUpdate"] if 'W' in p else ["Ticker", "Prev", "Price", "Chg", "%Chg", "Signal", "TimeUpdate"]
        st.dataframe(df.style.apply(apply_style, axis=1), use_container_width=True, hide_index=True, column_order=cols)
        if 'W' in p and st.session_state.manage_mode:
            st.write("---")
            dc = st.columns(6)
            for i, t in enumerate(curr_list):
                if dc[i % 6].button(f"✖ {t}", key=f"del_{t}", type="primary"): manage_list(m_key, t, "delete"); st.rerun()

if 'S' in p: time.sleep(300); st.rerun()
