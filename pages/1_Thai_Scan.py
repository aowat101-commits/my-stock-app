import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP ---
st.set_page_config(page_title="PPE Guardian V8.5", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    h1, h2, h3, p, span, label { color: #FFD700 !important; }
    .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
    [data-testid="stStatusWidget"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    [data-testid="stExpander"] details summary p { color: #FFD700 !important; font-weight: 700 !important; font-size: 16px !important; }
    .stMultiSelect label p { color: #FFD700 !important; font-size: 14px !important; }

    .stDataFrame [data-testid="stTable"] { background-color: #000000 !important; }
    .stDataFrame th { color: #FFD700 !important; background-color: #000000 !important; border: 0.1px solid #334155 !important; }
    .stDataFrame [data-testid="stTable"] td { font-size: 13px !important; background-color: #000000 !important; color: #FFD700 !important; border: 0.1px solid #334155 !important; }

    .stButton > button { height: 35px !important; border-radius: 8px !important; width: 100%; font-size: 12px !important; margin-bottom: -10px !important; }
    div.stButton > button[kind="primary"] { background-color: #FF0000 !important; color: white !important; border: none !important; }
    .update-btn > div > button { background-color: #FFD700 !important; color: #000000 !important; font-weight: bold !important; height: 40px !important; }
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
        
        # ดึงเวลาปัจจุบัน (เอาเวลาขึ้นก่อนวันที่)
        tz = pytz.timezone('Asia/Bangkok')
        last_update = datetime.now(tz).strftime("%H:%M %d/%m")
        
        # คำนวณอินดิเคเตอร์สำหรับ Signal
        ema8, ema20 = ta.ema(df['Close'], 8), ta.ema(df['Close'], 20)
        hull = ta.hma(df['Close'], 30)
        vma5 = ta.sma(df['Volume'], 5)
        esa = ta.ema(df['Close'], 9)
        d = ta.ema(abs(df['Close'] - esa), 9)
        ci = (df['Close'] - esa) / (0.015 * d)
        wt1, wt2 = ta.ema(ci, 12), ta.sma(ta.ema(ci, 12), 4)

        # สัญญาณ Signal พร้อมสัญลักษณ์ (Emoji) ตามเวอร์ชันก่อนหน้า
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
        
        return [
            ticker.replace('.BK', ''), f"{pp:.2f}", f"{cp:.2f}", f"{chg:+.2f}", f"{(chg/pp)*100:.2f}%", 
            f"{trade_val:.2f}M" if mode == 'Watchlist' else sig, 
            last_update, 
            "#00FF00" if chg > 0 else "#FF1100", # PC
            s_col if mode == 'Scan' else val_col, # VC
            s_col # TC (สีตาม Signal)
        ]
    except: return None

def apply_style(row):
    p_c, v_c, t_c = f'color: {row.iloc[-3]}', f'color: {row.iloc[-2]}', f'color: {row.iloc[-1]}'
    return ['', '', p_c, p_c, p_c, v_c, t_c, '', '', '']

# --- 3. NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 't_watch' not in st.session_state: st.session_state.t_watch = ['PTT.BK', 'DELTA.BK']
if 'u_watch' not in st.session_state: st.session_state.u_watch = ['IONQ', 'NVDA']

st.button("🏠 HOME", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home"}), type="primary" if st.session_state.page == 'Home' else "secondary")
c_nav1, c_nav2 = st.columns(2)
with c_nav1:
    st.button("🇹🇭 THAI WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TW"}), type="primary" if st.session_state.page == 'TW' else "secondary")
    st.button("🇹🇭 THAI MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TS"}), type="primary" if st.session_state.page == 'TS' else "secondary")
with c_nav2:
    st.button("🇺🇸 US WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "UW"}), type="primary" if st.session_state.page == 'UW' else "secondary")
    st.button("🇺🇸 US MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US"}), type="primary" if st.session_state.page == 'US' else "secondary")

dt_label = f"📅 {datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%d/%m/%Y | %H:%M:%S')}"

# --- 4. CONTENT ---
p = st.session_state.page
if p == 'Home':
    st.write(f'<div style="text-align:center; padding:10px;"><span style="color:#FFD700 !important; font-size:32px; font-weight:900; letter-spacing:6px; display:block;">WELCOME</span><span style="color:#FFD700 !important; font-size:20px; font-weight:800; letter-spacing:2px; display:block;">TRADING HOME</span></div>', unsafe_allow_html=True)
    col_img1, col_img_mid, col_img2 = st.columns([1, 1.5, 1])
    with col_img_mid:
        st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.write(f'<p style="text-align:center;"><span style="color:#FFD700 !important; font-size:16px; font-weight:600;">{dt_label}</span></p>', unsafe_allow_html=True)

elif p in ['TW', 'UW', 'TS', 'US']:
    mode = 'Scan' if 'S' in p else 'Watchlist'
    col6 = "Value (M)" if mode == 'Watchlist' else "Signal"
    col7 = "Time Update"
    title_text = {"TW":"Thai Watchlist", "TS":"Thai Market Scan", "UW":"US Watchlist", "US":"US Market Scan"}[p]
    flag = "🇹🇭" if "T" in p else "🇺🇸"
    
    st.write(f'<div style="text-align:center; margin-bottom:10px;"><span style="color:#FFD700 !important; font-size:22px; font-weight:900;">{flag} {title_text}</span><br><span style="color:#FFD700 !important; font-size:14px;">{dt_label}</span></div>', unsafe_allow_html=True)
    
    if mode == 'Scan':
        st.markdown('<div class="update-btn">', unsafe_allow_html=True)
        if st.button("🔄 Update Market Data"): st.cache_data.clear()
        st.markdown('</div>', unsafe_allow_html=True)
        t_list = ['PTT.BK', 'DELTA.BK', 'ADVANC.BK', 'AOT.BK'] if p=="TS" else ['IONQ', 'NVDA', 'IREN', 'TSLA']
    else:
        with st.expander("➕ Manage Your Watchlist"):
            if p == 'TW': st.session_state.t_watch = st.multiselect("Select Stocks:", ['PTT.BK', 'DELTA.BK', 'ADVANC.BK', 'AOT.BK', 'CPALL.BK'], default=st.session_state.t_watch)
            else: st.session_state.u_watch = st.multiselect("Select Stocks:", ['IONQ', 'NVDA', 'IREN', 'TSLA', 'SMX', 'ONDS'], default=st.session_state.u_watch)
        t_list = st.session_state.t_watch if p == 'TW' else st.session_state.u_watch

    res = [fetch_guardian_engine(t, mode) for t in t_list if fetch_guardian_engine(t, mode)]
    if res:
        df = pd.DataFrame(res, columns=["Ticker", "Prev", "Price", "Chg", "%Chg", col6, col7, "PC", "VC", "TC"])
        st.dataframe(df.style.apply(apply_style, axis=1), use_container_width=True, hide_index=True, column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", col6, col7))

st.write(f'<p style="text-align:center; margin-top:20px;"><span style="color:#FFD700 !important; font-size:12px; opacity:0.7;">PPE Guardian V8.5 | Por Piang Electric Plus</span></p>', unsafe_allow_html=True)
