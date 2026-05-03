import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz
import time
import os

# --- 1. MEMORY HELPERS ---
TH_FILE = "th_watchlist.txt"
US_FILE = "us_watchlist.txt"

def load_list(file_path, defaults):
    if not os.path.exists(file_path):
        with open(file_path, "w") as f: f.write(",".join(defaults))
        return defaults
    with open(file_path, "r") as f:
        data = f.read().strip()
        return data.split(",") if data else []

def save_list(file_path, data_list):
    with open(file_path, "w") as f: f.write(",".join(data_list))

# --- 2. UI SETUP ---
st.set_page_config(page_title="PPE Guardian V9.9", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    h1, h2, h3, p, span, label { color: #FFD700 !important; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
    [data-testid="stStatusWidget"], header, .stAppHeader { display: none !important; }
    .stApp { background-color: #0f172a; }
    .classic-header { color: #1E90FF !important; font-size: 14px; font-weight: 600; margin-bottom: 10px; text-align: center; }
    .stTextInput > div > div > input { background-color: #1e293b !important; color: #FFD700 !important; border: 1px solid #FFD700 !important; }
    [data-testid="stExpander"] details summary p { color: #FFD700 !important; font-weight: 700 !important; font-size: 16px !important; }
    .stDataFrame [data-testid="stTable"] { background-color: #000000 !important; }
    .stDataFrame th { color: #FFD700 !important; background-color: #000000 !important; border: 0.1px solid #334155 !important; }
    .stDataFrame [data-testid="stTable"] td { font-size: 13px !important; color: #FFD700 !important; border: 0.1px solid #334155 !important; }
    .stButton > button { height: 35px !important; border-radius: 8px !important; width: 100%; font-size: 14px !important; font-weight: 600 !important; }
    div.stButton > button[kind="primary"] { background-color: #FF0000 !important; color: white !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE ENGINE ---
@st.cache_data(ttl=60)
def fetch_guardian_engine(ticker, mode):
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
            
            if cp > e8 and h_curr > h_prev and vol > (v5 * 1.2):
                s_label, s_col, icon = "BUY", "#00FF00", "🚀 "
                raw_time = df.index[i].astimezone(pytz.timezone('Asia/Bangkok'))
                found_time = raw_time.strftime("%H:%M %d/%m"); break
            elif w1 > w2 and w1 < -47 and cp > e8: 
                s_label, s_col, icon = "DEEP BUY", "#00FF00", "▲ "
                raw_time = df.index[i].astimezone(pytz.timezone('Asia/Bangkok'))
                found_time = raw_time.strftime("%H:%M %d/%m"); break
            elif w1 < w2 and w1 > 53:
                s_label, s_col, icon = "P-SELL", "#FFA500", "🔶 "
                raw_time = df.index[i].astimezone(pytz.timezone('Asia/Bangkok'))
                found_time = raw_time.strftime("%H:%M %d/%m"); break
            elif cp < ema20.iloc[i] or h_curr < h_prev:
                s_label, s_col, icon = "SELL", "#FF1100", "🚨 "
                raw_time = df.index[i].astimezone(pytz.timezone('Asia/Bangkok'))
                found_time = raw_time.strftime("%H:%M %d/%m"); break

        if s_label == "-": return None
        c_cp, c_pp = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2])
        chg = c_cp - c_pp
        t_val = (c_cp * float(df['Volume'].iloc[-1])) / 1_000_000
        
        return {"Ticker": ticker.upper(), "Prev": f"{c_pp:.2f}", "Price": f"{c_cp:.2f}", 
                "Chg": f"{chg:+.2f}", "%Chg": f"{(chg/c_pp)*100:.2f}%", 
                "Signal": f"{icon}{s_label}", "Value (M)": f"{t_val:.2f}M",
                "TimeUpdate": found_time, "RawTime": raw_time,
                "PriceCol": "#00FF00" if chg > 0 else "#FF1100", 
                "SigCol": s_col}
    except: return None

def apply_style(row):
    colors = []
    for col in row.index:
        if col == "Ticker": colors.append(f'color: {row["SigCol"]}')
        elif col in ["Price", "Chg", "%Chg"]: colors.append(f'color: {row["PriceCol"]}')
        elif col == "Signal": colors.append(f'color: {row["SigCol"]}')
        elif col == "TimeUpdate": colors.append(f'color: {row["SigCol"]}')
        else: colors.append('')
    return colors

# --- 4. SESSION ---
if 't_list' not in st.session_state: st.session_state.t_list = load_list(TH_FILE, ['PTT', 'DELTA', 'ADVANC'])
if 'u_list' not in st.session_state: st.session_state.u_list = load_list(US_FILE, ['IONQ', 'NVDA', 'IREN'])
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 'manage_mode' not in st.session_state: st.session_state.manage_mode = False

# --- 5. NAVIGATION ---
st.button("🏠 HOME", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home"}), type="primary" if st.session_state.page == 'Home' else "secondary")
c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 THAI WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TW"}), type="primary" if st.session_state.page == 'TW' else "secondary")
    st.button("🇹🇭 THAI MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TS"}), type="primary" if st.session_state.page == 'TS' else "secondary")
with c2:
    st.button("🇺🇸 US WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "UW"}), type="primary" if st.session_state.page == 'UW' else "secondary")
    st.button("🇺🇸 US MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US"}), type="primary" if st.session_state.page == 'US' else "secondary")

p = st.session_state.page
dt_str = datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%H:%M:%S | %d/%m/%Y')
st.write(f'<div class="classic-header">PPE Guardian V9.9 | {dt_str}</div>', unsafe_allow_html=True)

# --- 6. CONTENT LOGIC ---
if p == 'Home':
    st.write('<div style="text-align:center; padding:5px;"><span style="color:#FFD700; font-size:30px; font-weight:900; letter-spacing:5px;">WELCOME</span></div>', unsafe_allow_html=True)
    st.write('<div style="text-align:center; padding:5px;"><span style="color:#FFD700; font-size:35px; font-weight:900; letter-spacing:2px;">TRADING HOME</span></div>', unsafe_allow_html=True)
    cl, cm, cr = st.columns([1, 1.5, 1]); cm.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)

elif p in ['TW', 'UW', 'TS', 'US']:
    f_t = {"TW":"🇹🇭 THAI WATCHLIST", "TS":"🇹🇭 THAI MARKET SCAN", "UW":"🇺🇸 US WATCHLIST", "US":"🇺🇸 US MARKET SCAN"}[p]
    st.write(f'<div style="text-align:center; margin-bottom:10px;"><span style="color:#FFD700; font-size:24px; font-weight:900;">{f_t}</span></div>', unsafe_allow_html=True)
    
    if 'W' in p:
        with st.expander("➕ Manage Your Watchlist", expanded=True):
            new = st.text_input("Ticker Name:").upper()
            if new:
                curr = st.session_state.t_list if 'T' in p else st.session_state.u_list
                if new not in curr:
                    curr.append(new); save_list(TH_FILE if 'T' in p else US_FILE, curr); st.rerun()
            if st.button("🛠️ Edit Watchlist (Delete Mode)"):
                st.session_state.manage_mode = not st.session_state.manage_mode; st.rerun()
    else:
        if st.button("🔄 Manual Refresh Scan"): st.cache_data.clear(); st.rerun()

    d_l = st.session_state.t_list if 'T' in p else st.session_state.u_list
    results = [fetch_guardian_engine(t, p) for t in d_l]
    results = [r for r in results if r is not None]

    if results:
        df = pd.DataFrame(results)
        if 'S' in p: df = df.sort_values(by="RawTime", ascending=False).head(30)
        
        # จัดคอลัมน์ตามหน้า
        cols = ["Ticker", "Prev", "Price", "Chg", "%Chg", "Value (M)", "TimeUpdate"] if 'W' in p else ["Ticker", "Prev", "Price", "Chg", "%Chg", "Signal", "TimeUpdate"]
        st.dataframe(df.style.apply(apply_style, axis=1), use_container_width=True, hide_index=True, column_order=cols)
        
        if 'W' in p and st.session_state.manage_mode:
            st.write("---")
            st.write("⚠️ **Delete Items:**")
            dc = st.columns(6)
            for i, t in enumerate(d_l):
                if dc[i % 6].button(f"✖ {t}", key=f"del_{t}", type="primary"):
                    d_l.remove(t); save_list(TH_FILE if 'T' in p else US_FILE, d_l); st.rerun()
    else:
        st.write('<p style="text-align:center; opacity:0.6;">No data found.</p>', unsafe_allow_html=True)

if 'S' in p:
    time.sleep(300); st.rerun()
