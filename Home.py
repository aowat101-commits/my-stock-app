import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz
import time
import os

# --- 1. CORE STORAGE SYSTEM ---
def manage_storage(mode, ticker=None, action="load"):
    file_path = f"{mode}_list.txt"
    defaults = ['PTT', 'DELTA'] if mode == "th" else ['IONQ', 'NVDA']
    if not os.path.exists(file_path):
        with open(file_path, "w") as f: f.write(",".join(defaults))
    with open(file_path, "r") as f:
        data = f.read().strip()
        current_data = [x.strip().upper() for x in data.split(",") if x.strip()] if data else defaults
    if action == "add" and ticker:
        ticker = ticker.strip().upper()
        if ticker and ticker not in current_data:
            current_data.append(ticker)
            with open(file_path, "w") as f: f.write(",".join(current_data)); f.flush()
    elif action == "delete" and ticker:
        if ticker in current_data:
            current_data.remove(ticker)
            with open(file_path, "w") as f: f.write(",".join(current_data)); f.flush()
    return current_data

if 'th_logs' not in st.session_state: st.session_state.th_logs = pd.DataFrame()
if 'us_logs' not in st.session_state: st.session_state.us_logs = pd.DataFrame()

# --- 2. UI SETUP & ABSOLUTE CENTERING ---
st.set_page_config(page_title="PPE Guardian V14.4", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stSidebar"], .st-emotion-cache-10o48ve, header, .stAppHeader { display: none !important; }
    .stApp { background-color: #0f172a; }
    
    .stApp .main .block-container {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-align: center !important;
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 auto !important;
    }

    div[data-testid="stVerticalBlock"] {
        align-items: center !important;
        width: 100% !important;
    }

    .stButton > button { 
        height: 50px !important; 
        border-radius: 12px !important; 
        font-size: 17px !important; 
        font-weight: bold !important; 
        color: #FFD700 !important; 
        background-color: #1e293b !important; 
        border: 2px solid #FFD700 !important;
        width: 300px !important;
        margin: 8px auto !important;
    }

    .del-btn button { color: #FF4B4B !important; border-color: #FF4B4B !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INDICATOR ENGINE ---
@st.cache_data(ttl=60)
def fetch_verified_data(ticker, market_mode):
    try:
        symbol = f"{ticker.upper()}.BK" if market_mode == "th" and ".BK" not in ticker.upper() else ticker.upper()
        df = yf.download(symbol, period="1mo", interval="1h", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        rsi_series = ta.rsi(df['Close'], length=14)
        curr_rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else 0
        cp = float(df['Close'].iloc[-1])
        c_pp = float(df['Close'].iloc[-2])
        chg = cp - c_pp
        pct_chg = (chg / c_pp) * 100
        val_raw = (cp * df['Volume'].iloc[-1]) / 1_000_000
        last_time = df.index[-1].astimezone(pytz.timezone('Asia/Bangkok'))
        
        # สัญญาณปิดวันก่อนหน้า (คอลัมน์ที่ 2)
        prev_close = float(df['Close'].iloc[-2])
        prev_prev_close = float(df['Close'].iloc[-3])
        prev_signal = prev_close - prev_prev_close
        
        return {
            "Ticker": ticker.upper(),
            "Prev": c_pp,
            "Price": cp,
            "Chg": chg,
            "%Chg": pct_chg,
            "Value (M)": val_raw,
            "TimeUpdate": last_time.strftime("%H:%M %d/%m"),
            "RSI": curr_rsi,
            "prev_signal": prev_signal, # ใช้สำหรับคำนวณสีคอลัมน์ 2
            "main_chg": chg           # ใช้สำหรับคำนวณสีคอลัมน์หลัก
        }
    except: return None

# 🔥 ฟังก์ชันสี V9.9 เป๊ะ
def style_v99(row):
    chg = row['main_chg']
    prev_sig = row['prev_signal']
    val = row['Value (M)']
    rsi = row['RSI']
    
    # สีหลัก (Ticker, Price, Chg, %Chg, TimeUpdate)
    main_color = 'color: #00FF00' if chg > 0 else 'color: #FF0000'
    
    # สไตล์รายคอลัมน์ [Ticker, Prev, Price, Chg, %Chg, Value, TimeUpdate, RSI]
    styles = [main_color] * 8
    
    # คอลัมน์ 2: Prev
    if prev_sig > 0: styles[1] = 'color: #00FF00'
    elif prev_sig < 0: styles[1] = 'color: #FF0000'
    else: styles[1] = 'color: #B8860B' # เหลืองเข้ม
    
    # คอลัมน์ 6: Value (M)
    if val > 100: styles[5] = 'color: #BF40BF' # ม่วง
    elif val >= 10: styles[5] = 'color: #00BFFF' # ฟ้าเข้ม
    else: styles[5] = 'color: #808080' # เทา
    
    # คอลัมน์ 8: RSI
    if rsi < 30: styles[7] = 'color: #FF0000'
    elif rsi > 70: styles[7] = 'color: #00FF00'
    else: styles[7] = 'color: #B8860B' # เหลืองเข้ม
    
    return styles

# --- 4. NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
now = datetime.now(pytz.timezone("Asia/Bangkok"))
time_str = now.strftime("%H:%M:%S"); date_str = now.strftime("%d/%m/%Y")

def centered_header(title, subtitle):
    st.markdown(f"""<div style="text-align: center; width: 100%;"><h1 style="color: #FFD700; font-size: 32px; font-weight: 900; margin-bottom: 0px;">{title}</h1><p style="color: #1E90FF; font-size: 13px; margin-top: 0px; margin-bottom: 10px;">{subtitle}</p></div>""", unsafe_allow_html=True)

# --- 5. PAGE LOGIC ---
if st.session_state.page == 'Home':
    centered_header("TRADING HOME", f"{time_str} 📅 {date_str} | V14.4")
    if st.button("🇹🇭 ตลาดหุ้นไทย"): st.session_state.market = 'th'; st.session_state.page = 'SubMenu'; st.rerun()
    if st.button("🇺🇸 ตลาดหุ้นอเมริกา"): st.session_state.market = 'us'; st.session_state.page = 'SubMenu'; st.rerun()
    st.write('---')
    st.markdown(f'<div style="display: flex; justify-content: center; width: 100%; margin: 10px 0;"><img src="https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000" width="380" style="border-radius: 12px;"></div>', unsafe_allow_html=True)

elif st.session_state.page == 'SubMenu':
    m_label = "🇹🇭 THAI MENU" if st.session_state.market == 'th' else "🇺🇸 US MENU"
    centered_header(m_label, f"{time_str} 📅 {date_str} | V14.4")
    if st.button("📋 WATCHLIST"): st.session_state.page = 'Watch'; st.rerun()
    if st.button("🔍 MARKET SCAN"): st.session_state.page = 'Scan'; st.rerun()
    if st.button("🏠 กลับหน้าหลัก"): st.session_state.page = 'Home'; st.session_state.market = None; st.rerun()

elif st.session_state.page == 'Watch':
    m_code = "TH" if st.session_state.market == 'th' else "US"
    centered_header(f"📋 WATCHLIST ({m_code})", f"{time_str} 📅 {date_str} | V14.4")
    if st.button("⬅ กลับเมนูตลาด"): st.session_state.page = 'SubMenu'; st.rerun()
    
    with st.expander("⚙️ Manage List", expanded=True):
        new_t = st.text_input("Ticker:", label_visibility="collapsed", placeholder="e.g. PTT").upper()
        if st.button("➕ Add"): 
            manage_storage(st.session_state.market, new_t, "add"); st.cache_data.clear(); st.rerun()
        st.markdown('<div class="del-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Delete"): 
            manage_storage(st.session_state.market, new_t, "delete"); st.cache_data.clear(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    cl = manage_storage(st.session_state.market)
    results = [fetch_verified_data(t, st.session_state.market) for t in cl]
    results = [r for r in results if r]
    
    disp_cols = ["Ticker", "Prev", "Price", "Chg", "%Chg", "Value (M)", "TimeUpdate", "RSI"]
    calc_cols = disp_cols + ["prev_signal", "main_chg"] # คอลัมน์ที่ต้องใช้คำนวณสี

    if results:
        df = pd.DataFrame(results)
        # ใช้ calc_cols เพื่อให้มีข้อมูลสำหรับ style_v99
        styled_df = df[calc_cols].style.apply(style_v99, axis=1)\
                                .format({"Prev": "{:.2f}", "Price": "{:.2f}", "Chg": "{:+.2f}", "%Chg": "{:+.2f}%", "Value (M)": "{:.2f}M", "RSI": "{:.2f}"})\
                                .hide(subset=["prev_signal", "main_chg"], axis=1) # ซ่อนคอลัมน์คำนวณ
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.dataframe(pd.DataFrame(columns=disp_cols), use_container_width=True, hide_index=True)

time.sleep(600); st.rerun()
