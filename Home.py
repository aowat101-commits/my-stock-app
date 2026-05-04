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

# --- 2. UI SETUP ---
st.set_page_config(page_title="PPE Guardian V16.14", layout="wide", initial_sidebar_state="collapsed")

if 'signal_history' not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=["Ticker", "Prev", "Price", "Chg", "%Chg", "Signal", "TimeUpdate", "RawTime", "m_chg"])

if 'page' not in st.query_params: st.query_params['page'] = 'Home'
curr_p = st.query_params.get('page', 'Home')
curr_m = st.query_params.get('market', None)

# CSS บังคับกึ่งกลางแบบเจาะจงชั้นในสุด
st.markdown("""
    <style>
    [data-testid="stSidebar"], header, .stAppHeader { display: none !important; }
    .stApp { background-color: #0f172a; }
    .stApp .main .block-container {
        display: block !important;
        width: 100% !important;
        text-align: center !important;
    }
    div.stButton {
        display: flex !important;
        justify-content: center !important;
        margin: 0 auto !important;
    }
    .stButton > button { 
        height: 52px !important; width: 320px !important;
        border-radius: 14px !important; font-size: 18px !important; 
        font-weight: 500 !important; color: #FFD700 !important; 
        background-color: #1e293b !important; border: 2px solid #FFD700 !important; 
    }
    [data-testid="stDataFrame"] { margin: 0 auto !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ENGINE ---
def fetch_data(ticker, mode):
    try:
        sym = f"{ticker.upper()}.BK" if mode == "th" else ticker.upper()
        t_obj = yf.Ticker(sym)
        hist_d = t_obj.history(period="5d", interval="1d")
        if hist_d.empty: return None
        vma5 = hist_d['Volume'].iloc[-5:-1].mean()
        curr_vol = hist_d['Volume'].iloc[-1]
        prev_close = float(hist_d['Close'].iloc[-2])
        current_price = float(t_obj.fast_info['last_price'])
        
        df = t_obj.history(period="1mo", interval="1h")
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        e8 = ta.ema(df['Close'], 8); e20 = ta.ema(df['Close'], 20)
        h = ta.hma(df['Close'], 30); rsi = ta.rsi(df['Close'], 14)
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa = ta.ema(ap, 9); d = ta.ema(abs(ap - esa), 9)
        ci = (ap - esa) / (0.015 * d); tci = ta.ema(ci, 12)
        wt1 = tci; wt2 = ta.sma(wt1, 3)
        
        chg = current_price - prev_close
        sig = "-"
        if wt1.iloc[-1] > wt2.iloc[-1] and wt1.iloc[-1] < -45 and current_price > e8.iloc[-1]:
            sig = "P-BUY"
            if current_price > e20.iloc[-1] and h.iloc[-1] > h.iloc[-2] and curr_vol > (vma5 * 1.2): sig = "BUY"
        elif (wt1.iloc[-1] < wt2.iloc[-1] and wt1.iloc[-1] > 53) or current_price < e8.iloc[-1]:
            sig = "P-SELL"
            if current_price < e20.iloc[-1] or h.iloc[-1] < h.iloc[-2]: sig = "SELL"
        
        now = datetime.now(pytz.timezone("Asia/Bangkok"))
        return {"Ticker": ticker.upper(), "Prev": prev_close, "Price": current_price, "Chg": chg, "%Chg": (chg/prev_close)*100, 
                "Value (M)": (current_price * curr_vol)/1_000_000, "RSI": rsi.iloc[-1] if not rsi.empty else 0, 
                "TimeUpdate": now.strftime("%H:%M:%S %d/%m"), "RawTime": now, "Signal": sig, "m_chg": chg}
    except: return None

def apply_styles(data):
    def row_style(row):
        m_c = '#00FF00' if row['m_chg'] > 0 else ('#FF0000' if row['m_chg'] < 0 else '#FFD700')
        styles = [f'color: {m_c}; font-weight: 400'] * len(row)
        if "Signal" in row.index:
            sig_c = '#00FF00' if "BUY" in str(row['Signal']) else ('#FF0000' if "SELL" in str(row['Signal']) else '#FFD700')
            styles[list(row.index).index("Signal")] = f'color: {sig_c}; font-weight: 400'
        return styles
    return data.style.apply(row_style, axis=1)

def go(p, m=None):
    st.query_params['page'] = p
    if m: st.query_params['market'] = m
    st.rerun()

def hdr(t):
    t_now = datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S 📅 %d/%m/%Y")
    st.markdown(f'<div style="text-align: center;"><h1 style="color: #FFD700; margin-bottom: 5px;">{t}</h1>'
                f'<p style="color: #1E90FF; font-size: 16px;">{t_now} | V16.14</p></div>', unsafe_allow_html=True)

# --- 4. PAGE LOGIC ---
if curr_p == 'Home':
    hdr("TRADING HOME")
    # บังคับปุ่มกึ่งกลาง
    st.button("🇹🇭 ตลาดหุ้นไทย", on_click=go, args=('SubMenu', 'th'))
    st.button("🇺🇸 ตลาดหุ้นอเมริกา", on_click=go, args=('SubMenu', 'us'))
    # บังคับรูปกึ่งกลาง
    st.markdown('<div style="display: flex; justify-content: center; width: 100%;"><hr style="border: 1px solid #1e293b; width: 320px;"></div>', unsafe_allow_html=True)
    st.markdown('<div style="display: flex; justify-content: center;"><img src="https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000" width="380" style="border-radius: 12px;"></div>', unsafe_allow_html=True)

elif curr_p == 'SubMenu':
    hdr(f"{'🇹🇭' if curr_m == 'th' else '🇺🇸'} MENU")
    st.button("📋 WATCHLIST", on_click=go, args=('Watch', curr_m))
    st.button("🔍 MARKET SCAN", on_click=go, args=('Scan', curr_m))
    st.button("🏠 กลับหน้าหลัก", on_click=go, args=('Home',))

elif curr_p == 'Watch':
    hdr("WATCHLIST")
    st.button("⬅ กลับเมนูตลาด", on_click=go, args=('SubMenu', curr_m))
    res = [fetch_data(t, curr_m) for t in manage_storage(curr_m)]
    if res:
        df = pd.DataFrame([r for r in res if r])
        st.dataframe(apply_styles(df).format({"Prev":"{:.2f}","Price":"{:.2f}","Chg":"{:+.2f}","%Chg":"{:.2f}%","Value (M)":"{:.2f}M","RSI":"{:.2f}"}), 
                     use_container_width=True, hide_index=True, column_order=["Ticker","Prev","Price","Chg","%Chg","Value (M)","RSI","TimeUpdate"])

elif curr_p == 'Scan':
    hdr("SCAN")
    st.button("⬅ กลับเมนูตลาด", on_click=go, args=('SubMenu', curr_m))
    new_res = [fetch_data(t, curr_m) for t in manage_storage(curr_m)]
    new_active = [r for r in new_res if r and r['Signal'] in ["P-BUY", "BUY", "P-SELL", "SELL"]]
    
    if new_active:
        new_df = pd.DataFrame(new_active)
        for idx, row in new_df.iterrows():
            match = st.session_state.signal_history[(st.session_state.signal_history['Ticker'] == row['Ticker']) & (st.session_state.signal_history['Signal'] == row['Signal'])]
            if not match.empty:
                new_df.at[idx, 'TimeUpdate'] = match.iloc[0]['TimeUpdate']
                new_df.at[idx, 'RawTime'] = match.iloc[0]['RawTime']
        
        combined = pd.concat([new_df, st.session_state.signal_history]).drop_duplicates(subset=['Ticker', 'Signal'], keep='first')
        st.session_state.signal_history = combined.sort_values(by="RawTime", ascending=False).head(30)

    if not st.session_state.signal_history.empty:
        st.dataframe(apply_styles(st.session_state.signal_history).format({"Prev":"{:.2f}","Price":"{:.2f}","Chg":"{:+.2f}","%Chg":"{:.2f}%"}), 
                     use_container_width=True, hide_index=True, column_order=["Ticker","Prev","Price","Chg","%Chg","Signal","TimeUpdate"])

time.sleep(600); st.rerun()
