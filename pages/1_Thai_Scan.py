import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP & COMPACT STYLE ---
st.set_page_config(page_title="PPE Guardian V8.5", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    h1, h2, h3, p, span, label { color: #FFD700 !important; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
    [data-testid="stStatusWidget"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    [data-testid="stExpander"] details summary p { color: #FFD700 !important; font-weight: 700 !important; font-size: 16px !important; }
    
    .stDataFrame [data-testid="stTable"] { background-color: #000000 !important; }
    .stDataFrame th { color: #FFD700 !important; background-color: #000000 !important; border: 0.1px solid #334155 !important; }
    .stDataFrame [data-testid="stTable"] td { font-size: 13px !important; background-color: #000000 !important; color: #FFD700 !important; border: 0.1px solid #334155 !important; }

    .stButton > button { height: 35px !important; border-radius: 8px !important; width: 100%; font-size: 12px !important; margin-bottom: -10px !important; }
    div.stButton > button[kind="primary"] { background-color: #FF0000 !important; color: white !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE ENGINE ---
@st.cache_data(ttl=60)
def fetch_guardian_engine(ticker, mode='TW'):
    try:
        # เติม .BK ให้อัตโนมัติสำหรับโหมดไทย
        symbol = f"{ticker.upper()}.BK" if ".BK" not in ticker.upper() and mode in ['TW', 'TS'] else ticker.upper()
        df = yf.download(symbol, period="60d", interval="1d", progress=False)
        
        if df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        cp, pp = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2])
        chg = cp - pp
        trade_val = (cp * float(df['Volume'].iloc[-1])) / 1_000_000
        
        tz = pytz.timezone('Asia/Bangkok')
        last_update = datetime.now(tz).strftime("%H:%M %d/%m")
        
        ema8, ema20 = ta.ema(df['Close'], 8), ta.ema(df['Close'], 20)
        hull = ta.hma(df['Close'], 30)
        vma5 = ta.sma(df['Volume'], 5)
        esa = ta.ema(df['Close'], 9)
        d = ta.ema(abs(df['Close'] - esa), 9)
        ci = (df['Close'] - esa) / (0.015 * d)
        wt1, wt2 = ta.ema(ci, 12), ta.sma(ta.ema(ci, 12), 4)

        sig, s_col = "-", "#FFD700"
        if cp > ema8.iloc[-1] and hull.iloc[-1] > hull.iloc[-2] and df['Volume'].iloc[-1] > (vma5.iloc[-1] * 1.2):
            sig, s_col = "✅ BUY", "#00FF00"
        elif wt1.iloc[-1] > wt2.iloc[-1] and wt1.iloc[-1] < -47:
            sig, s_col = "🔺 DEEP BUY", "#00FF00"
        elif wt1.iloc[-1] < wt2.iloc[-1] and wt1.iloc[-1] > 53:
            sig, s_col = "🔶 P-SELL", "#FFA500"
        elif cp < ema20.iloc[-1] or hull.iloc[-1] < hull.iloc[-2]:
            sig, s_col = "🚨 SELL", "#FF1100"

        val_col = "#6b7280"
        if trade_val > 100: val_col = "#A855F7"
        elif trade_val >= 10: val_col = "#06B6D4"
        
        return [ticker.upper(), f"{pp:.2f}", f"{cp:.2f}", f"{chg:+.2f}", f"{(chg/pp)*100:.2f}%", 
                f"{trade_val:.2f}M" if 'W' in mode else sig, last_update, 
                "#00FF00" if chg > 0 else "#FF1100", 
                s_col if 'S' in mode else val_col, s_col]
    except: return None

def apply_style(row):
    p_c, v_c, t_c = f'color: {row.iloc[-3]}', f'color: {row.iloc[-2]}', f'color: {row.iloc[-1]}'
    return ['', '', p_c, p_c, p_c, v_c, t_c, '', '', '']

# --- 3. SESSION STATE MANAGEMENT ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 't_watch' not in st.session_state: st.session_state.t_watch = ['PTT', 'DELTA', 'ADVANC', 'TFG']
if 'u_watch' not in st.session_state: st.session_state.u_watch = ['IONQ', 'NVDA', 'IREN']

# --- 4. NAVIGATION ---
st.button("🏠 HOME", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home"}), type="primary" if st.session_state.page == 'Home' else "secondary")
c_nav1, c_nav2 = st.columns(2)
with c_nav1:
    st.button("🇹🇭 THAI WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TW"}), type="primary" if st.session_state.page == 'TW' else "secondary")
    st.button("🇹🇭 THAI MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TS"}), type="primary" if st.session_state.page == 'TS' else "secondary")
with c_nav2:
    st.button("🇺🇸 US WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "UW"}), type="primary" if st.session_state.page == 'UW' else "secondary")
    st.button("🇺🇸 US MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US"}), type="primary" if st.session_state.page == 'US' else "secondary")

# --- 5. CONTENT ---
tz = pytz.timezone('Asia/Bangkok')
dt_label = f"📅 {datetime.now(tz).strftime('%d/%m/%Y | %H:%M:%S')}"
p = st.session_state.page

if p == 'Home':
    st.write(f'<div style="text-align:center; padding:10px;"><span style="color:#FFD700 !important; font-size:32px; font-weight:900; letter-spacing:6px; display:block;">WELCOME</span><span style="color:#FFD700 !important; font-size:20px; font-weight:800; letter-spacing:2px; display:block;">TRADING HOME</span></div>', unsafe_allow_html=True)
    c_img_l, c_img_m, c_img_r = st.columns([1, 1.5, 1])
    with c_img_m: st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.write(f'<p style="text-align:center;"><span style="color:#FFD700 !important; font-size:16px; font-weight:600;">{dt_label}</span></p>', unsafe_allow_html=True)

elif p in ['TW', 'UW', 'TS', 'US']:
    col6 = "Value (M)" if 'W' in p else "Signal"
    title = {"TW":"Thai Watchlist", "TS":"Thai Market Scan", "UW":"US Watchlist", "US":"US Market Scan"}[p]
    flag = "🇹🇭" if "T" in p else "🇺🇸"
    
    st.write(f'<div style="text-align:center; margin-bottom:10px;"><span style="color:#FFD700 !important; font-size:22px; font-weight:900;">{flag} {title}</span><br><span style="color:#FFD700 !important; font-size:14px;">{dt_label}</span></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Manage Your Watchlist"):
        # ระบบ Freedom Input: พิมพ์ชื่อหุ้นที่ต้องการเพิ่มได้อิสระ
        current_list = st.session_state.t_watch if 'T' in p else st.session_state.u_watch
        new_stocks = st.multiselect("พิมพ์ชื่อหุ้นเพื่อเพิ่ม (เช่น ALT, TFG):", 
                                   options=list(set(current_list + ['ALT', 'TFG', 'OR', 'DELTA', 'PTT'])), 
                                   default=current_list)
        
        if 'T' in p: st.session_state.t_watch = new_stocks
        else: st.session_state.u_watch = new_stocks
        
        t_list = new_stocks

    res = [fetch_guardian_engine(t, p) for t in t_list if fetch_guardian_engine(t, p)]
    if res:
        df = pd.DataFrame(res, columns=["Ticker", "Prev", "Price", "Chg", "%Chg", col6, "Time Update", "PC", "VC", "TC"])
        st.dataframe(df.style.apply(apply_style, axis=1), use_container_width=True, hide_index=True, column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", col6, "Time Update"))

st.write(f'<p style="text-align:center; margin-top:20px;"><span style="color:#FFD700 !important; font-size:12px; opacity:0.7;">PPE Guardian V8.5 | Por Piang Electric Plus</span></p>', unsafe_allow_html=True)
