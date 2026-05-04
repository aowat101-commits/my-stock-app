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
        with open(file_path, "w") as f: f.write("PTT,DELTA,ADVANC")
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
    st.session_state.signal_history = pd.DataFrame(columns=["Ticker", "Price", "Chg", "%Chg", "Signal", "TimeUpdate", "RawTime", "m_chg"])

if 'page' not in st.query_params: st.query_params['page'] = 'Home'
curr_p = st.query_params.get('page', 'Home')
curr_m = st.query_params.get('market', 'th')

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
        margin: 10px auto !important;
    }
    [data-testid="stDataFrame"] { background-color: #1e293b !important; border-radius: 12px !important; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        font-weight: 400 !important; background-color: #1e293b !important;
        color: #cbd5e1 !important; border-bottom: 1px solid #334155 !important;
    }
    .del-btn button { color: #FF4B4B !important; border-color: #FF4B4B !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ENGINE ---
def fetch_data_thai(ticker):
    try:
        sym = f"{ticker.upper()}.BK"
        t_obj = yf.Ticker(sym)
        hist_d = t_obj.history(period="10d", interval="1d")
        if hist_d.empty: return None
        vma5 = hist_d['Volume'].iloc[-6:-1].mean()
        curr_vol = hist_d['Volume'].iloc[-1]
        prev_close = float(hist_d['Close'].iloc[-2])
        
        df = t_obj.history(period="1mo", interval="1h")
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        e8 = ta.ema(df['Close'], length=8); e20 = ta.ema(df['Close'], length=20)
        hma30 = ta.hma(df['Close'], length=30)
        ap = (df['High'] + df['Low'] + df['Close']) / 3
        esa = ta.ema(ap, length=9); d = ta.ema(abs(ap - esa), length=9)
        ci = (ap - esa) / (0.015 * d); tci = ta.ema(ci, length=12)
        wt1 = tci; wt2 = ta.sma(wt1, length=3)
        
        cp = float(t_obj.fast_info['last_price'])
        chg = cp - prev_close
        pct_chg = (chg / prev_close) * 100
        
        sig = "-"
        if wt1.iloc[-1] > wt2.iloc[-1] and wt1.iloc[-1] < -45 and cp > e8.iloc[-1]:
            sig = "P-BUY (Deep)"
            if cp > e20.iloc[-1] and hma30.iloc[-1] > hma30.iloc[-2] and curr_vol > (vma5 * 1.2):
                sig = "BUY: Strong Vol"
        elif (wt1.iloc[-1] < wt2.iloc[-1] and wt1.iloc[-1] > 53) or cp < e8.iloc[-1]:
            sig = "P-SALE"
            if cp < e20.iloc[-1] or hma30.iloc[-1] < hma30.iloc[-2]:
                sig = "EXIT"

        now = datetime.now(pytz.timezone("Asia/Bangkok"))
        return {"Ticker": ticker.upper(), "Price": cp, "Chg": chg, "%Chg": pct_chg, 
                "Signal": sig, "TimeUpdate": now.strftime("%H:%M:%S %d/%m"), 
                "RawTime": now, "m_chg": chg}
    except: return None

def apply_styles(data):
    if data.empty: return data.style
    styler = data.style.set_table_styles([{'selector': 'td, th', 'props': [('background-color', '#1e293b')]}])
    def row_style(row):
        val = row.get('m_chg', 0)
        m_c = 'color: #00FF00' if val > 0 else ('color: #FF0000' if val < 0 else 'color: #FFD700')
        styles = [f'background-color: #1e293b; {m_c}; font-weight: 400'] * len(row)
        if "Signal" in row.index:
            sig_val = str(row['Signal']); sig_idx = list(row.index).index("Signal")
            s_c = 'color: #00FF00' if "BUY" in sig_val else ('color: #FF0000' if sig_val in ["EXIT", "P-SALE"] else 'color: #FFD700')
            styles[sig_idx] = f'background-color: #1e293b; {s_c}; font-weight: 400'
        return styles
    return styler.apply(row_style, axis=1)

# --- 4. NAVIGATION ---
def go(p, m=None):
    st.query_params['page'] = p
    if m: st.query_params['market'] = m
    st.rerun()

def hdr(t):
    t_now = datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S 📅 %d/%m/%Y")
    st.markdown(f'''<div style="text-align: center;"><h1 style="color: #FFD700; margin-bottom: 5px; font-weight: 500;">{t}</h1>
    <p style="color: #1E90FF; font-weight: 400; font-size: 16px;">{t_now} | PPE GUARDIAN V16.14</p></div>''', unsafe_allow_html=True)

# --- 5. PAGE LOGIC ---
if curr_p == 'Home':
    hdr("TRADING HOME")
    if st.button("🇹🇭 ตลาดหุ้นไทย"): go('SubMenu', 'th')
    if st.button("🇺🇸 ตลาดหุ้นอเมริกา"): go('SubMenu', 'us')
    st.write('---')
    st.markdown('<div style="display: flex; justify-content: center;"><img src="https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000" width="380" style="border-radius: 12px;"></div>', unsafe_allow_html=True)

elif curr_p == 'SubMenu':
    f = "🇹🇭" if curr_m == 'th' else "🇺🇸"
    hdr(f"{f} MENU")
    if st.button("📋 WATCHLIST"): go('Watch', curr_m)
    if st.button("🔍 MARKET SCAN"): go('Scan', curr_m)
    if st.button("🏠 กลับหน้าหลัก"): go('Home')

elif curr_p == 'Watch':
    f = "🇹🇭" if curr_m == 'th' else "🇺🇸"
    hdr(f"{f} WATCHLIST")
    if st.button("⬅ กลับเมนูตลาด"): go('SubMenu', curr_m)
    with st.expander("⚙️ Manage List", expanded=False):
        nt = st.text_input("Ticker:", key="in_w").upper()
        if st.button("➕ Add"): manage_storage(curr_m, nt, "add"); st.rerun()
        st.markdown('<div class="del-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Delete"): manage_storage(curr_m, nt, "delete"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    res = [fetch_data_thai(t) for t in manage_storage(curr_m)]
    res = [r for r in res if r]
    if res:
        df = pd.DataFrame(res)
        # คืนค่าคอลัมน์ให้ครบ 6 คอลัมน์ (Ticker, Price, Chg, %Chg, Signal, TimeUpdate)
        st.dataframe(apply_styles(df).format({"Price":"{:.2f}","Chg":"{:+.2f}","%Chg":"{:+.2f}%"}), use_container_width=True, hide_index=True, column_order=["Ticker","Price","Chg","%Chg","Signal","TimeUpdate"])

elif curr_p == 'Scan':
    f = "🇹🇭" if curr_m == 'th' else "🇺🇸"
    hdr(f"{f} SCAN")
    if st.button("⬅ กลับเมนูตลาด"): go('SubMenu', curr_m)
    new_res = [fetch_data_thai(t) for t in manage_storage(curr_m)]
    new_res = [r for r in new_res if r and r['Signal'] != "-"]
    if new_res:
        new_df = pd.DataFrame(new_res)
        combined = pd.concat([new_df, st.session_state.signal_history], ignore_index=True).drop_duplicates(subset=['Ticker', 'Signal'], keep='first')
        st.session_state.signal_history = combined.sort_values(by="RawTime", ascending=False).head(30)
    
    if not st.session_state.signal_history.empty:
        # คืนค่าคอลัมน์ให้ครบตามเดิม
        st.dataframe(apply_styles(st.session_state.signal_history).format({"Price":"{:.2f}","Chg":"{:+.2f}","%Chg":"{:+.2f}%"}), use_container_width=True, hide_index=True, column_order=["Ticker","Price","Chg","%Chg","Signal","TimeUpdate"])

time.sleep(600); st.rerun()
