import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP ---
st.set_page_config(page_title="Guardian Dashboard V8.5", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
    [data-testid="stStatusWidget"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    .centered-yellow-title { text-align: center !important; color: #FFD700 !important; font-size: 24px; font-weight: 700; margin-top: -10px !important; }
    .centered-time { text-align: center !important; color: #FFD700 !important; margin-bottom: 5px !important; margin-top: -5px !important; }
    
    .stDataFrame [data-testid="stTable"] { background-color: #000000 !important; }
    .stDataFrame th { color: #FFD700 !important; background-color: #000000 !important; border: 0.1px solid #334155 !important; }
    .stDataFrame [data-testid="stTable"] td { font-size: 14px !important; background-color: #000000 !important; color: #FFD700 !important; border: 0.1px solid #334155 !important; }

    .stButton > button { height: 35px !important; border-radius: 8px !important; width: 100%; font-size: 12px !important; margin-bottom: -10px !important; }
    div.stButton > button[kind="primary"] { background-color: #FF0000 !important; color: white !important; border: none !important; }
    .scan-btn > div > button { background-color: #FFD700 !important; color: #000000 !important; font-weight: bold !important; height: 45px !important; margin-top: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE LOGIC (The Guardian Swing) ---
@st.cache_data(ttl=60)
def fetch_guardian_v85(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # Technicals
        ema8, ema20 = ta.ema(df['Close'], 8), ta.ema(df['Close'], 20)
        hull = ta.hma(df['Close'], 30)
        vma5 = ta.sma(df['Volume'], 5)
        
        esa = ta.ema(df['Close'], 9)
        d = ta.ema(abs(df['Close'] - esa), 9)
        ci = (df['Close'] - esa) / (0.015 * d)
        wt1, wt2 = ta.ema(ci, 12), ta.sma(ta.ema(ci, 12), 4)

        cp, pp = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2])
        chg = cp - pp
        
        # Signals
        sig, s_col = "-", "#FFD700"
        if cp > ema8.iloc[-1] and hull.iloc[-1] > hull.iloc[-2] and df['Volume'].iloc[-1] > (vma5.iloc[-1] * 1.2):
            sig, s_col = "✅ BUY", "#00FF00"
        elif wt1.iloc[-1] > wt2.iloc[-1] and wt1.iloc[-1] < -47:
            sig, s_col = "🔺 DEEP BUY", "#00FF00"
        elif wt1.iloc[-1] < wt2.iloc[-1] and wt1.iloc[-1] > 53:
            sig, s_col = "🔶 P-SELL", "#FFA500"
        elif cp < ema20.iloc[-1] or hull.iloc[-1] < hull.iloc[-2]:
            sig, s_col = "🚨 SELL", "#FF1100"

        return {
            "Ticker": ticker.replace('.BK', ''), "Prev": f"{pp:.2f}", "Price": f"{cp:.2f}",
            "Chg": f"{chg:+.2f}", "%Chg": f"{(chg/pp)*100:.2f}%", "Signal": sig,
            "RSI(14)": f"{float(ta.rsi(df['Close'], 14).iloc[-1]):.2f}",
            "_pc": "#00FF00" if chg > 0 else "#FF1100", "_sc": s_col
        }
    except: return None

def apply_guardian_style(row):
    p_c, s_c = f'color: {row["_pc"]}', f'color: {row["_sc"]}'
    # บังคับคืนค่าสีให้ครบ 7 คอลัมน์ตามลำดับที่แสดงในตาราง
    return ['', '', p_c, p_c, p_c, s_c, 'color: #FFD700']

# --- 3. NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
st.button("🏠 Home", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home"}), type="primary" if st.session_state.page == 'Home' else "secondary")
c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 Thai Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TW"}), type="primary" if st.session_state.page == 'TW' else "secondary")
    st.button("🇹🇭 Thai Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TS"}), type="primary" if st.session_state.page == 'TS' else "secondary")
with c2:
    st.button("🇺🇸 US Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"page": "UW"}), type="primary" if st.session_state.page == 'UW' else "secondary")
    st.button("🇺🇸 US Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US"}), type="primary" if st.session_state.page == 'US' else "secondary")

tz = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz)
dt_label = f"📅 {now.strftime('%d/%m/%Y')} | 🕒 {now.strftime('%H:%M:%S')}"
p = st.session_state.page

# --- 4. CONTENT ---
if p in ['TW', 'UW', 'TS', 'US']:
    title = {"TW":"🇹🇭 Thai Watchlist", "TS":"🇹🇭 Thai Market Scan", "UW":"🇺🇸 US Watchlist", "US":"🇺🇸 US Market Scan"}[p]
    st.markdown(f'<p class="centered-yellow-title">{title}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="centered-time">{dt_label}</p>', unsafe_allow_html=True)
    
    if "Scan" in title:
        st.markdown('<div class="scan-btn">', unsafe_allow_html=True)
        if st.button("🔍 เริ่มสแกนหาจังหวะเทรด"):
            st.cache_data.clear()
            st.toast("กำลังสแกน...")
        st.markdown('</div>', unsafe_allow_html=True)
        tickers = ['PTT.BK', 'DELTA.BK', 'ADVANC.BK', 'AOT.BK', 'CPALL.BK'] if p=="TS" else ['IONQ', 'NVDA', 'IREN', 'TSLA']
    else:
        with st.expander("➕ จัดการลิสต์หุ้น"):
            tickers = st.multiselect("เลือกหุ้น:", ['PTT.BK', 'DELTA.BK', 'ADVANC.BK', 'AOT.BK'], default=['PTT.BK', 'DELTA.BK'])
    
    data = [fetch_guardian_v85(t) for t in tickers if fetch_guardian_v85(t)]
    if data:
        # ส่วนสำคัญ: ตรวจสอบและแสดงผลตาราง
        df_final = pd.DataFrame(data)
        st.dataframe(df_final.style.apply(apply_guardian_style, axis=1), use_container_width=True, hide_index=True,
                     column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "Signal", "RSI(14)"))

else: # Home
    st.markdown('<p class="welcome-title">WELCOME</p><p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)

st.markdown(f'<p style="text-align:center; color:#FFD700; margin-top:20px; opacity:0.6;">PPE Guardian V8.5 | {dt_label}</p>', unsafe_allow_html=True)
