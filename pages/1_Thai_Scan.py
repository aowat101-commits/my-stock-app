import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP (บังคับล้างค่าสีเดิม) ---
st.set_page_config(page_title="PPE Guardian V8.5", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* ล้างค่าสีพื้นฐานของ Streamlit */
    h1, h2, h3, p, span, label { color: #FFD700 !important; }
    
    .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
    [data-testid="stStatusWidget"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    /* แก้ไขส่วนจัดการหุ้นที่สีมืด */
    [data-testid="stExpander"] details summary p { 
        color: #FFD700 !important; 
        font-weight: 900 !important; 
        font-size: 22px !important; 
    }
    
    /* ตาราง Dark Mode */
    .stDataFrame [data-testid="stTable"] { background-color: #000000 !important; }
    .stDataFrame th { color: #FFD700 !important; background-color: #000000 !important; border: 0.1px solid #334155 !important; }
    .stDataFrame [data-testid="stTable"] td { 
        font-size: 14px !important; 
        background-color: #000000 !important; 
        color: #FFD700 !important; 
        border: 0.1px solid #334155 !important; 
    }

    /* ปุ่มเมนู */
    .stButton > button { height: 38px !important; border-radius: 8px !important; width: 100%; font-size: 13px !important; margin-bottom: -10px !important; }
    div.stButton > button[kind="primary"] { background-color: #FF0000 !important; color: white !important; border: none !important; }
    
    /* ปุ่มอัปเดตภาษาอังกฤษ */
    .update-btn > div > button { 
        background-color: #FFD700 !important; 
        color: #000000 !important; 
        font-weight: bold !important; 
        height: 45px !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE ENGINE ---
@st.cache_data(ttl=60)
def fetch_guardian_engine(ticker, mode='Watchlist'):
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        cp, pp = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2])
        chg = cp - pp
        trade_val = (cp * float(df['Volume'].iloc[-1])) / 1_000_000
        
        sig, s_col = "-", "#FFD700"
        if mode == 'Scan':
            ema8, ema20 = ta.ema(df['Close'], 8), ta.ema(df['Close'], 20)
            hull = ta.hma(df['Close'], 30)
            vma5 = ta.sma(df['Volume'], 5)
            esa = ta.ema(df['Close'], 9)
            d = ta.ema(abs(df['Close'] - esa), 9)
            ci = (df['Close'] - esa) / (0.015 * d)
            wt1, wt2 = ta.ema(ci, 12), ta.sma(ta.ema(ci, 12), 4)
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
        
        return [ticker.replace('.BK', ''), f"{pp:.2f}", f"{cp:.2f}", f"{chg:+.2f}", f"{(chg/pp)*100:.2f}%", 
                f"{trade_val:.2f}M" if mode == 'Watchlist' else sig, 
                f"{float(ta.rsi(df['Close'], 14).iloc[-1]):.2f}", "#00FF00" if chg > 0 else "#FF1100", 
                s_col if mode == 'Scan' else val_col]
    except: return None

def apply_style(row):
    p_c, v_c = f'color: {row.iloc[-2]}', f'color: {row.iloc[-1]}'
    return ['', '', p_c, p_c, p_c, v_c, 'color: #FFD700', '', '']

# --- 3. NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 't_watch' not in st.session_state: st.session_state.t_watch = ['PTT.BK', 'DELTA.BK']
if 'u_watch' not in st.session_state: st.session_state.u_watch = ['IONQ', 'NVDA']

st.button("🏠 HOME", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home"}), type="primary" if st.session_state.page == 'Home' else "secondary")
c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 THAI WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TW"}), type="primary" if st.session_state.page == 'TW' else "secondary")
    st.button("🇹🇭 THAI MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TS"}), type="primary" if st.session_state.page == 'TS' else "secondary")
with c2:
    st.button("🇺🇸 US WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "UW"}), type="primary" if st.session_state.page == 'UW' else "secondary")
    st.button("🇺🇸 US MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US"}), type="primary" if st.session_state.page == 'US' else "secondary")

tz = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz)
dt_label = f"📅 {now.strftime('%d/%m/%Y')} | 🕒 {now.strftime('%H:%M:%S')}"

# --- 4. CONTENT ---
p = st.session_state.page
if p == 'Home':
    # ล็อกสีเหลืองทองแบบฝังลงใน HTML ลึกที่สุด
    st.write(f'<div style="text-align:center; padding:20px;"><span style="color:#FFD700 !important; font-size:64px; font-weight:900; letter-spacing:12px; display:block; filter: drop-shadow(0px 0px 5px #000);">WELCOME</span><span style="color:#FFD700 !important; font-size:42px; font-weight:800; letter-spacing:4px; display:block; filter: drop-shadow(0px 0px 5px #000);">TRADING HOME</span></div>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.write(f'<p style="text-align:center;"><span style="color:#FFD700 !important; font-size:22px; font-weight:600;">{dt_label}</span></p>', unsafe_allow_html=True)

elif p in ['TW', 'UW', 'TS', 'US']:
    mode = 'Scan' if 'S' in p else 'Watchlist'
    col6 = "Value (M)" if mode == 'Watchlist' else "Signal"
    title_text = {"TW":"Thai Watchlist", "TS":"Thai Market Scan", "UW":"US Watchlist", "US":"US Market Scan"}[p]
    flag = "🇹🇭" if "T" in p else "🇺🇸"
    
    st.write(f'<div style="text-align:center;"><span style="color:#FFD700 !important; font-size:38px; font-weight:900; filter: drop-shadow(0px 0px 5px #000);">{flag} {title_text}</span><br><span style="color:#FFD700 !important; font-size:18px;">{dt_label}</span></div>', unsafe_allow_html=True)
    
    if mode == 'Scan':
        st.markdown('<div class="update-btn">', unsafe_allow_html=True)
        if st.button("🔄 Update Market Data"): st.cache_data.clear()
        st.markdown('</div>', unsafe_allow_html=True)
        t_list = ['PTT.BK', 'DELTA.BK', 'AOT.BK'] if p=="TS" else ['IONQ', 'NVDA', 'IREN']
    else:
        with st.expander("➕ Manage Your Watchlist"):
            st.session_state.t_watch = st.multiselect("Select Stocks:", ['PTT.BK', 'DELTA.BK', 'ADVANC.BK'], default=st.session_state.t_watch) if p == 'TW' else st.multiselect("Select Stocks:", ['IONQ', 'NVDA', 'IREN'], default=st.session_state.u_watch)
        t_list = st.session_state.t_watch if p == 'TW' else st.session_state.u_watch

    res = [fetch_guardian_engine(t, mode) for t in t_list if fetch_guardian_engine(t, mode)]
    if res:
        df = pd.DataFrame(res, columns=["Ticker", "Prev", "Price", "Chg", "%Chg", col6, "RSI(14)", "PC", "VC"])
        st.dataframe(df.style.apply(apply_style, axis=1), use_container_width=True, hide_index=True, column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", col6, "RSI(14)"))

st.write(f'<p style="text-align:center; margin-top:50px;"><span style="color:#FFD700 !important; opacity:0.7;">PPE Guardian V8.5 | Por Piang Electric Plus</span></p>', unsafe_allow_html=True)
