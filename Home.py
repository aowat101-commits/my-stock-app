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

# --- 2. UI SETUP & CSS ---
st.set_page_config(page_title="PPE Guardian V16.6", layout="wide", initial_sidebar_state="collapsed")

if 'signal_history' not in st.session_state:
    st.session_state.signal_history = pd.DataFrame(columns=["Ticker", "Prev", "Price", "Chg", "%Chg", "Signal", "TimeUpdate", "RawTime", "p_sig", "m_chg"])

if 'page' not in st.query_params: st.query_params['page'] = 'Home'
curr_p = st.query_params.get('page', 'Home')
curr_m = st.query_params.get('market', None)

st.markdown("""
    <style>
    [data-testid="stSidebar"], header, .stAppHeader { display: none !important; }
    .stApp { background-color: #0f172a; }
    
    /* 🎯 ล็อกปุ่มกึ่งกลางถาวรด้วย CSS Deep Selector */
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
        font-weight: bold !important; color: #FFD700 !important; 
        background-color: #1e293b !important; border: 2px solid #FFD700 !important; 
        margin: 10px auto !important; display: block !important;
    }
    .del-btn button { color: #FF4B4B !important; border-color: #FF4B4B !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HIGH ACCURACY ENGINE ---
def fetch_data(ticker, mode):
    try:
        sym = f"{ticker.upper()}.BK" if mode == "th" else ticker.upper()
        ticker_obj = yf.Ticker(sym)
        # ดึงราคาจากชุดข้อมูลที่ไวที่สุด (Fast Info)
        fast = ticker_obj.fast_info
        df = ticker_obj.history(period="1mo", interval="1h")
        
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # คำนวณอินดิเคเตอร์
        e8 = ta.ema(df['Close'], 8); h = ta.hma(df['Close'], 30)
        wt1 = ta.ema((df['Close'] - ta.ema(df['Close'], 9)) / (0.015 * ta.ema(abs(df['Close'] - ta.ema(df['Close'], 9)), 9)), 12)
        wt2 = ta.sma(wt1, 4); rsi = ta.rsi(df['Close'], length=14)
        
        cp = fast['last_price'] # ราคาล่าสุดจริงจากระบบ
        c_pp = float(df['Close'].iloc[-2])
        p_p_c = float(df['Close'].iloc[-3])
        
        sig = "-"
        if cp > e8.iloc[-1] and h.iloc[-1] > h.iloc[-2]: sig = "BUY"
        elif wt1.iloc[-1] > wt2.iloc[-2] and wt1.iloc[-1] < -47: sig = "DEEP BUY"
        elif cp < ta.ema(df['Close'], 20).iloc[-1]: sig = "SELL"
        
        now = datetime.now(pytz.timezone("Asia/Bangkok"))
        return {"Ticker": ticker.upper(), "Prev": c_pp, "Price": cp, "Chg": cp - c_pp, 
                "%Chg": ((cp - c_pp) / c_pp) * 100, "Value (M)": (cp * fast['last_volume']) / 1_000_000, 
                "RSI": rsi.iloc[-1] if not rsi.empty else 0, "TimeUpdate": now.strftime("%H:%M:%S %d/%m"), 
                "RawTime": now, "Signal": sig, "p_sig": c_pp - p_p_c, "m_chg": cp - c_pp}
    except: return None

def apply_styles(data):
    styles = pd.DataFrame('', index=data.index, columns=data.columns)
    for i in range(len(data)):
        row = data.iloc[i]
        s_c = 'color: #00FF00' if row['Signal'] in ["BUY", "DEEP BUY"] else 'color: #FF0000'
        for c in ["Ticker", "Signal", "TimeUpdate"]: styles.at[data.index[i], c] = s_c
        p_c = 'color: #00FF00' if row['p_sig'] > 0 else ('color: #FF0000' if row['p_sig'] < 0 else 'color: #FFD700')
        styles.at[data.index[i], "Prev"] = p_c
        m_c = 'color: #00FF00' if row['m_chg'] > 0 else ('color: #FF0000' if row['m_chg'] < 0 else 'color: #FFD700')
        for c in ["Price", "Chg", "%Chg", "Value (M)"]: 
            if c in data.columns: styles.at[data.index[i], c] = m_c
    return styles

# --- 4. NAVIGATION ---
def go(p, m=None):
    st.query_params['page'] = p
    if m: st.query_params['market'] = m
    st.rerun()

def hdr(t, s):
    st.markdown(f'<div style="text-align: center;"><h1 style="color: #FFD700; margin:0;">{t}</h1><p style="color: #1E90FF;">{s}</p></div>', unsafe_allow_html=True)

# --- 5. PAGE LOGIC ---
t_now = datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S 📅 %d/%m/%Y")

if curr_p == 'Home':
    hdr("TRADING HOME", t_now)
    if st.button("🇹🇭 ตลาดหุ้นไทย"): go('SubMenu', 'th')
    if st.button("🇺🇸 ตลาดหุ้นอเมริกา"): go('SubMenu', 'us')
    st.write('---')
    st.markdown(f'<div style="display: flex; justify-content: center;"><img src="https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000" width="380" style="border-radius: 12px;"></div>', unsafe_allow_html=True)

elif curr_p == 'SubMenu':
    f = "🇹🇭" if curr_m == 'th' else "🇺🇸"
    hdr(f"{f} MENU", t_now)
    if st.button("📋 WATCHLIST"): go('Watch', curr_m)
    if st.button("🔍 MARKET SCAN"): go('Scan', curr_m)
    if st.button("🏠 กลับหน้าหลัก"): go('Home')

elif curr_p == 'Watch':
    f = "🇹🇭" if curr_m == 'th' else "🇺🇸"
    hdr(f"🇹🇭 WATCHLIST", t_now)
    if st.button("⬅ กลับเมนูตลาด"): go('SubMenu', curr_m)
    with st.expander("⚙️ Manage List", expanded=False):
        nt = st.text_input("Ticker:", placeholder="e.g. PTT", key="in_w").upper()
        if st.button("➕ Add"): manage_storage(curr_m, nt, "add"); st.rerun()
        st.markdown('<div class="del-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Delete"): manage_storage(curr_m, nt, "delete"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    res = [fetch_data(t, curr_m) for t in manage_storage(curr_m)]
    res = [r for r in res if r]
    if res:
        df = pd.DataFrame(res)
        st.dataframe(df.style.apply(apply_styles, axis=None).format({"Prev":"{:.2f}","Price":"{:.2f}","Chg":"{:+.2f}","%Chg":"{:+.2f}%","Value (M)":"{:.2f}M","RSI":"{:.2f}"}), 
                     use_container_width=True, hide_index=True, column_order=["Ticker","Prev","Price","Chg","%Chg","Value (M)","RSI","TimeUpdate"])

elif curr_p == 'Scan':
    f = "🇹🇭" if curr_m == 'th' else "🇺🇸"
    hdr(f"🇹🇭 SCAN", t_now)
    if st.button("⬅ กลับเมนูตลาด"): go('SubMenu', curr_m)
    new_results = [fetch_data(t, curr_m) for t in manage_storage(curr_m)]
    new_results = [r for r in new_results if r and r['Signal'] != "-"]
    if new_results:
        new_df = pd.DataFrame(new_results)
        combined = pd.concat([new_df, st.session_state.signal_history]).drop_duplicates(subset=['Ticker', 'Signal'], keep='first')
        combined = combined.sort_values(by="RawTime", ascending=False).head(30)
        st.session_state.signal_history = combined
    if not st.session_state.signal_history.empty:
        st.dataframe(st.session_state.signal_history.style.apply(apply_styles, axis=None).format({"Prev":"{:.2f}","Price":"{:.2f}","Chg":"{:+.2f}","%Chg":"{:+.2f}%"}), 
                     use_container_width=True, hide_index=True, column_order=["Ticker","Prev","Price","Chg","%Chg","Signal","TimeUpdate"])

time.sleep(60); st.rerun()
