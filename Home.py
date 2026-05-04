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

# --- 2. UI SETUP & CSS (คงเดิมจาก V16.13) ---
st.set_page_config(page_title="PPE Guardian V16.14", layout="wide", initial_sidebar_state="collapsed")

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
        font-weight: 500 !important; color: #FFD700 !important; 
        background-color: #1e293b !important; border: 2px solid #FFD700 !important; 
        margin: 10px auto !important; display: block !important;
    }
    .del-btn button { color: #FF4B4B !important; border-color: #FF4B4B !important; }
    [data-testid="stDataFrame"] { background-color: #1e293b !important; border-radius: 12px !important; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        font-weight: 400 !important; background-color: #1e293b !important;
        color: #cbd5e1 !important; border-bottom: 1px solid #334155 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. THE GUARDIAN SWING ENGINE (แก้ไขเฉพาะเงื่อนไข) ---
def fetch_data(ticker, mode):
    try:
        sym = f"{ticker.upper()}.BK" if mode == "th" else ticker.upper()
        t_obj = yf.Ticker(sym)
        hist_d = t_obj.history(period="10d", interval="1d")
        if hist_d.empty: return None
        
        vma5 = hist_d['Volume'].iloc[-6:-1].mean()
        curr_vol = hist_d['Volume'].iloc[-1]
        prev_close = float(hist_d['Close'].iloc[-2])
        current_price = float(t_obj.fast_info['last_price'])
        
        df = t_obj.history(period="1mo", interval="1h")
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Indicators
        e8 = ta.ema(df['Close'], 8); e20 = ta.ema(df['Close'], 20)
        h = ta.hma(df['Close'], 30); rsi = ta.rsi(df['Close'], 14)
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa = ta.ema(ap, 9); d = ta.ema(abs(ap - esa), 9)
        ci = (ap - esa) / (0.015 * d); tci = ta.ema(ci, 12)
        wt1 = tci; wt2 = ta.sma(wt1, 3)
        
        chg = current_price - prev_close
        pct_chg = (chg / prev_close) * 100
        
        # --- 4 SIGNAL NAMES (P-BUY, BUY, P-SELL, SELL) ---
        sig = "-"
        if wt1.iloc[-1] > wt2.iloc[-1] and wt1.iloc[-1] < -45 and current_price > e8.iloc[-1]:
            sig = "P-BUY"
            if current_price > e20.iloc[-1] and h.iloc[-1] > h.iloc[-2] and curr_vol > (vma5 * 1.2):
                sig = "BUY"
        elif (wt1.iloc[-1] < wt2.iloc[-1] and wt1.iloc[-1] > 53) or current_price < e8.iloc[-1]:
            sig = "P-SELL"
            if current_price < e20.iloc[-1] or h.iloc[-1] < h.iloc[-2]:
                sig = "SELL"
        
        now = datetime.now(pytz.timezone("Asia/Bangkok"))
        return {"Ticker": ticker.upper(), "Prev": prev_close, "Price": current_price, 
                "Chg": chg, "%Chg": pct_chg, "Value (M)": (current_price * curr_vol) / 1_000_000, 
                "RSI": rsi.iloc[-1] if not rsi.empty else 0, "TimeUpdate": now.strftime("%H:%M:%S %d/%m"), 
                "RawTime": now, "Signal": sig, "m_chg": chg}
    except: return None

def apply_styles(data):
    styler = data.style.set_table_styles([{'selector': 'td, th', 'props': [('background-color', '#1e293b')]}])
    def row_style(row):
        m_c = 'color: #00FF00' if row['m_chg'] > 0 else ('color: #FF0000' if row['m_chg'] < 0 else 'color: #FFD700')
        styles = [f'background-color: #1e293b; {m_c}; font-weight: 400'] * len(row)
        if "Signal" in data.columns:
            idx_sig = data.columns.get_loc("Signal")
            sig_c = 'color: #00FF00' if "BUY" in row['Signal'] else ('color: #FF0000' if "SELL" in row['Signal'] else 'color: #FFD700')
            styles[idx_sig] = f'background-color: #1e293b; {sig_c}; font-weight: 400'
        return styles
    return styler.apply(row_style, axis=1)

# --- 4. NAVIGATION ---
def go(p, m=None):
    st.query_params['page'] = p
    if m: st.query_params['market'] = m
    st.rerun()

def hdr(t):
    t_now = datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S 📅 %d/%m/%Y")
    st.markdown(f'<div style="text-align: center;"><h1 style="color: #FFD700; margin-bottom: 5px;">{t}</h1>'
                f'<p style="color: #1E90FF;">{t_now} | PPE GUARDIAN V16.14</p></div>', unsafe_allow_html=True)

# --- 5. PAGE LOGIC ---
if curr_p == 'Home':
    hdr("TRADING HOME")
    if st.button("🇹🇭 ตลาดหุ้นไทย"): go('SubMenu', 'th')
    if st.button("🇺🇸 ตลาดหุ้นอเมริกา"): go('SubMenu', 'us')

elif curr_p == 'SubMenu':
    f = "🇹🇭" if curr_m == 'th' else "🇺🇸"
    hdr(f"{f} MENU")
    if st.button("📋 WATCHLIST"): go('Watch', curr_m)
    if st.button("🔍 MARKET SCAN"): go('Scan', curr_m)
    if st.button("🏠 กลับหน้าหลัก"): go('Home')

elif curr_p == 'Watch':
    hdr("TH WATCHLIST")
    if st.button("⬅ กลับเมนูตลาด"): go('SubMenu', curr_m)
    res = [fetch_data(t, curr_m) for t in manage_storage(curr_m)]
    res = [r for r in res if r]
    if res:
        df = pd.DataFrame(res)
        # ล็อก 8 คอลัมน์เดิม: Ticker, Prev, Price, Chg, %Chg, Value(M), RSI, TimeUpdate
        st.dataframe(apply_styles(df).format({"Prev":"{:.2f}","Price":"{:.2f}","Chg":"{:+.2f}","%Chg":"{:+.2f}%","Value (M)":"{:.2f}M","RSI":"{:.2f}"}), 
                     use_container_width=True, hide_index=True, column_order=["Ticker","Prev","Price","Chg","%Chg","Value (M)","RSI","TimeUpdate"])

elif curr_p == 'Scan':
    hdr("TH SCAN")
    if st.button("⬅ กลับเมนูตลาด"): go('SubMenu', curr_m)
    new_res = [fetch_data(t, curr_m) for t in manage_storage(curr_m)]
    new_res = [r for r in new_res if r and r['Signal'] != "-"]
    if new_res:
        new_df = pd.DataFrame(new_res)
        combined = pd.concat([new_df, st.session_state.signal_history]).drop_duplicates(subset=['Ticker', 'Signal'], keep='first')
        st.session_state.signal_history = combined.sort_values(by="RawTime", ascending=False).head(30)
    if not st.session_state.signal_history.empty:
        # ล็อก 7 คอลัมน์: Ticker, Prev, Price, Chg, %Chg, Signal, TimeUpdate
        st.dataframe(apply_styles(st.session_state.signal_history).format({"Prev":"{:.2f}","Price":"{:.2f}","Chg":"{:+.2f}","%Chg":"{:+.2f}%"}), 
                     use_container_width=True, hide_index=True, column_order=["Ticker","Prev","Price","Chg","%Chg","Signal","TimeUpdate"])

time.sleep(600); st.rerun()
