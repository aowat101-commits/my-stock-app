import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz
import time

# --- 1. UI SETUP & CLASSIC STYLE ---
st.set_page_config(page_title="PPE Guardian V9.1", layout="wide", initial_sidebar_state="collapsed")

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

# --- 2. CORE ENGINE (1H Signal Lookback with New Icons) ---
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

        s_label, s_col, found_time, raw_time = "-", "#FFD700", "-", None
        for i in range(len(df)-1, 0, -1):
            cp = float(df['Close'].iloc[i]); h_curr, h_prev = hull.iloc[i], hull.iloc[i-1]
            w1, w2 = wt1.iloc[i], wt2.iloc[i]; vol, v5 = df['Volume'].iloc[i], vma5.iloc[i]
            
            if cp > ema8.iloc[i] and h_curr > h_prev and vol > (v5 * 1.2):
                s_label, s_col = "🚀 BUY", "#00FF00"
                raw_time = df.index[i].astimezone(pytz.timezone('Asia/Bangkok'))
                found_time = raw_time.strftime("%H:%M %d/%m"); break
            elif w1 > w2 and w1 < -47:
                s_label, s_col = "▲ DEEP BUY", "#00FF00"
                raw_time = df.index[i].astimezone(pytz.timezone('Asia/Bangkok'))
                found_time = raw_time.strftime("%H:%M %d/%m"); break
            elif w1 < w2 and w1 > 53:
                s_label, s_col = "🔶 P-SELL", "#FFA500"
                raw_time = df.index[i].astimezone(pytz.timezone('Asia/Bangkok'))
                found_time = raw_time.strftime("%H:%M %d/%m"); break
            elif cp < ema20.iloc[i] or h_curr < h_prev:
                s_label, s_col = "🚨 SELL", "#FF1100"
                raw_time = df.index[i].astimezone(pytz.timezone('Asia/Bangkok'))
                found_time = raw_time.strftime("%H:%M %d/%m"); break

        if s_label == "-": return None # กรองออกถ้าไม่มีสัญญาณ

        c_cp, c_pp = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2])
        chg, t_val = c_cp - c_pp, (c_cp * float(df['Volume'].iloc[-1])) / 1_000_000
        col6_val = f"{t_val:.2f}M" if 'W' in mode else s_label
        v_col = "#6b7280" if 'W' in mode else s_col
        if 'W' in mode:
            if t_val > 100: v_col = "#A855F7"
            elif t_val >= 10: v_col = "#06B6D4"

        return {"Ticker": ticker.upper(), "Prev": f"{c_pp:.2f}", "Price": f"{c_cp:.2f}", 
                "Chg": f"{chg:+.2f}", "%Chg": f"{(chg/c_pp)*100:.2f}%", 
                "Col6": col6_val, "TimeUpdate": found_time, "RawTime": raw_time,
                "PriceCol": "#00FF00" if chg > 0 else "#FF1100", "ValCol": v_col, "SigCol": s_col}
    except: return None

def apply_style(row):
    # แถวแรก Ticker เปลี่ยนสีตามสัญญาณ
    t_c = f'color: {row["SigCol"]}'
    p_c = f'color: {row["PriceCol"]}'
    v_c = f'color: {row["ValCol"]}'
    s_c = f'color: {row["SigCol"]}'
    return [t_c, '', p_c, p_c, p_c, v_c, s_c, '', '', '']

# --- 3. SESSION & NAVIGATION ---
if 't_list' not in st.session_state: st.session_state.t_list = ['PTT', 'DELTA', 'ADVANC', 'TFG', 'ALT']
if 'u_list' not in st.session_state: st.session_state.u_list = ['IONQ', 'NVDA', 'IREN']
if 'page' not in st.session_state: st.session_state.page = 'Home'

st.button("🏠 HOME", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home"}), type="primary" if st.session_state.page == 'Home' else "secondary")
c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 THAI WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TW"}), type="primary" if st.session_state.page == 'TW' else "secondary")
    st.button("🇹🇭 THAI MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TS"}), type="primary" if st.session_state.page == 'TS' else "secondary")
with c2:
    st.button("🇺🇸 US WATCHLIST", use_container_width=True, on_click=lambda: st.session_state.update({"page": "UW"}), type="primary" if st.session_state.page == 'UW' else "secondary")
    st.button("🇺🇸 US MARKET SCAN", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US"}), type="primary" if st.session_state.page == 'US' else "secondary")

# --- 4. CONTENT ---
p = st.session_state.page
now_tz = datetime.now(pytz.timezone('Asia/Bangkok'))
dt_str = now_tz.strftime('%H:%M:%S | %d/%m/%Y')

if p == 'Home':
    st.write('<div style="text-align:center; padding:5px;"><span style="color:#FFD700; font-size:30px; font-weight:900; letter-spacing:5px;">WELCOME</span></div>', unsafe_allow_html=True)
    st.write('<div style="text-align:center; padding:5px;"><span style="color:#FFD700; font-size:35px; font-weight:900; letter-spacing:2px;">TRADING HOME</span></div>', unsafe_allow_html=True)
    cl, cm, cr = st.columns([1, 1.5, 1]); cm.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.write(f'<div class="classic-header">PPE Guardian V9.1 | {dt_str}</div>', unsafe_allow_html=True)

elif p in ['TW', 'UW', 'TS', 'US']:
    col6_label = "Value (M)" if 'W' in p else "Signal"
    f_t = {"TW":"🇹🇭 THAI WATCHLIST", "TS":"🇹🇭 THAI MARKET SCAN", "UW":"🇺🇸 US WATCHLIST", "US":"🇺🇸 US MARKET SCAN"}[p]
    st.write(f'<div style="text-align:center; margin-bottom:10px;"><span style="color:#FFD700; font-size:24px; font-weight:900;">{f_t}</span></div>', unsafe_allow_html=True)
    st.write(f'<div class="classic-header">PPE Guardian V9.1 | {dt_str}</div>', unsafe_allow_html=True)
    
    if 'W' in p:
        with st.expander("➕ Manage Your Watchlist", expanded=True):
            cin, cbtn = st.columns([3, 1])
            with cin:
                new = st.text_input("Add Stock:", key=f"in_{p}").upper()
                if new and new not in (st.session_state.t_list if 'T' in p else st.session_state.u_list):
                    (st.session_state.t_list if 'T' in p else st.session_state.u_list).append(new); st.rerun()
            if st.button("🗑️ Clear All"):
                if 'T' in p: st.session_state.t_list = []
                else: st.session_state.u_list = []
                st.rerun()
    else:
        if st.button("🔄 Manual Refresh Scan"): st.cache_data.clear()

    d_l = st.session_state.t_list if 'T' in p else st.session_state.u_list
    results = [fetch_guardian_engine(t, p) for t in d_l]
    results = [r for r in results if r is not None]

    if results:
        # แปลงเป็น DataFrame
        df = pd.DataFrame(results)
        # ถ้าเป็นหน้า Scan ให้เรียงตามเวลาล่าสุด และเอาแค่ 30 บรรทัด
        if 'S' in p:
            df = df.sort_values(by="RawTime", ascending=False).head(30)
        
        # ปรับแต่งการแสดงผลตาราง
        display_df = df[["Ticker", "Prev", "Price", "Chg", "%Chg", "Col6", "TimeUpdate"]]
        display_df.columns = ["Ticker", "Prev", "Price", "Chg", "%Chg", col6_label, "Time Update"]
        
        st.dataframe(df.style.apply(apply_style, axis=1), use_container_width=True, hide_index=True, 
                     column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", col6_label, "Time Update"))

time.sleep(300) 
st.rerun()
