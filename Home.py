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

# --- 2. UI SETUP & DEEP CSS ---
st.set_page_config(page_title="PPE Guardian V16.3", layout="wide", initial_sidebar_state="collapsed")

if 'page' not in st.query_params: st.query_params['page'] = 'Home'
curr_p = st.query_params.get('page', 'Home')
curr_m = st.query_params.get('market', None)

st.markdown("""
    <style>
    /* ปิดส่วนหัวและเมนูที่ไม่จำเป็น */
    [data-testid="stSidebar"], header, .stAppHeader { display: none !important; }
    .stApp { background-color: #0f172a; }
    
    /* 🎯 เจาะจงจัดกึ่งกลางลึกถึงระดับ Container */
    .stApp .main .block-container {
        display: flex !important; flex-direction: column !important;
        align-items: center !important; justify-content: flex-start !important;
        width: 100% !important; margin: 0 auto !important;
    }
    
    /* บังคับ Vertical Block ทุกอันให้กึ่งกลาง */
    [data-testid="stVerticalBlock"], [data-testid="stVerticalBlockBorderWrapper"] {
        display: flex !important; flex-direction: column !important;
        align-items: center !important; justify-content: center !important;
        width: 100% !important;
    }

    /* จัดการช่องว่างและตำแหน่งปุ่ม */
    div.element-container, div.stButton {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }
    
    .stButton > button { 
        height: 52px !important; 
        border-radius: 14px !important; 
        font-size: 18px !important; 
        font-weight: bold !important; 
        color: #FFD700 !important; 
        background-color: #1e293b !important; 
        border: 2px solid #FFD700 !important; 
        width: 320px !important; 
        margin: 12px auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .del-btn button { color: #FF4B4B !important; border-color: #FF4B4B !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INDICATOR ENGINE ---
@st.cache_data(ttl=20)
def fetch_data(ticker, mode):
    try:
        sym = f"{ticker.upper()}.BK" if mode == "th" else ticker.upper()
        df = yf.download(sym, period="1mo", interval="1h", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        e8 = ta.ema(df['Close'], 8); e20 = ta.ema(df['Close'], 20)
        h = ta.hma(df['Close'], 30); v5 = ta.sma(df['Volume'], 5)
        esa = ta.ema(df['Close'], 9); d = ta.ema(abs(df['Close'] - esa), 9)
        ci = (df['Close'] - esa) / (0.015 * d); wt1 = ta.ema(ci, 12); wt2 = ta.sma(wt1, 4)
        cp = float(df['Close'].iloc[-1]); hc = h.iloc[-1]; hp = h.iloc[-2]
        vol = df['Volume'].iloc[-1]; w1 = wt1.iloc[-1]; w2 = wt2.iloc[-2]
        sig = "-"
        if cp > e8.iloc[-1] and hc > hp and vol > (v5.iloc[-1] * 1.2): sig = "BUY"
        elif w1 > w2 and w1 < -47 and cp > e8.iloc[-1]: sig = "DEEP BUY"
        elif cp < e20.iloc[-1] or hc < hp: sig = "SELL"
        elif cp < e8.iloc[-1] and hc < hp: sig = "P-SELL"
        c_pp = float(df['Close'].iloc[-2]); p_p_c = float(df['Close'].iloc[-3])
        # 🕒 แสดงเวลาที่ตรวจพบสัญญาณจริงวินาทีต่อวินาที
        now_time = datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S %d/%m")
        return {"Ticker": ticker.upper(), "Prev": c_pp, "Price": cp, "Chg": cp - c_pp, "%Chg": ((cp - c_pp) / c_pp) * 100, 
                "Value (M)": (cp * vol) / 1_000_000, "TimeUpdate": now_time, "Signal": sig, "p_sig": c_pp - p_p_c, "m_chg": cp - c_pp}
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
        for c in ["Price", "Chg", "%Chg", "Value (M)"]: styles.at[data.index[i], c] = m_c
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
    hdr("TRADING HOME", f"{t_now} | V16.3")
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
    hdr(f"{f} WATCHLIST", t_now)
    if st.button("⬅ กลับเมนูตลาด"): go('SubMenu', curr_m)
    with st.expander("⚙️ Manage List", expanded=False):
        nt = st.text_input("Ticker:", placeholder="e.g. PTT", key="in_w").upper()
        if st.button("➕ Add"): manage_storage(curr_m, nt, "add"); st.cache_data.clear(); st.rerun()
        st.markdown('<div class="del-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Delete"): manage_storage(curr_m, nt, "delete"); st.cache_data.clear(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    res = [fetch_data(t, curr_m) for t in manage_storage(curr_m)]
    res = [r for r in res if r]
    if res:
        df = pd.DataFrame(res)
        st.dataframe(df.style.apply(apply_styles, axis=None).format({"Prev":"{:.2f}","Price":"{:.2f}","Chg":"{:+.2f}","%Chg":"{:+.2f}%","Value (M)":"{:.2f}M"}), 
                     use_container_width=True, hide_index=True, column_order=["Ticker","Prev","Price","Chg","%Chg","Value (M)","TimeUpdate"])

elif curr_p == 'Scan':
    f = "🇹🇭" if curr_m == 'th' else "🇺🇸"
    hdr(f"{f} SCAN", t_now)
    if st.button("⬅ กลับเมนูตลาด"): go('SubMenu', curr_m)
    res = [fetch_data(t, curr_m) for t in manage_storage(curr_m)]
    res = [r for r in res if r]
    if res:
        df = pd.DataFrame(res)
        df = df[df['Signal'] != "-"]
        if not df.empty:
            st.dataframe(df.style.apply(apply_styles, axis=None).format({"Prev":"{:.2f}","Price":"{:.2f}","Chg":"{:+.2f}","%Chg":"{:+.2f}%"}), 
                         use_container_width=True, hide_index=True, column_order=["Ticker","Prev","Price","Chg","%Chg","Signal","TimeUpdate"])
        else: st.info("No active signals. Pull down to refresh.")

time.sleep(600); st.rerun()
