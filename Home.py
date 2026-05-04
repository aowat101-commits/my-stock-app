import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz
import time
import os

# --- 1. SEPARATED ENGINE (ระบบจัดการไฟล์แยกจากกัน) ---
def manage_storage(mode, ticker=None, action="load"):
    file_path = f"{mode}_list.txt"
    if not os.path.exists(file_path):
        with open(file_path, "w") as f: f.write("PTT" if mode=="th" else "NVDA")
    
    with open(file_path, "r") as f:
        data = f.read().strip()
        current_data = [x.strip().upper() for x in data.split(",") if x.strip()]
    
    if action == "add" and ticker:
        ticker = ticker.strip().upper()
        if ticker not in current_data:
            current_data.append(ticker)
            with open(file_path, "w") as f: f.write(",".join(current_data))
    elif action == "delete" and ticker:
        if ticker in current_data:
            current_data.remove(ticker)
            with open(file_path, "w") as f: f.write(",".join(current_data))
    return current_data

# แยกถังเก็บข้อมูลสัญญาณ (History)
if 'th_logs' not in st.session_state: st.session_state.th_logs = pd.DataFrame()
if 'us_logs' not in st.session_state: st.session_state.us_logs = pd.DataFrame()
if 'keys_seen' not in st.session_state: st.session_state.keys_seen = set()

# --- 2. INDICATOR ENGINE (สูตรเดิมของคุณมิลค์) ---
@st.cache_data(ttl=60)
def get_signal(ticker, market):
    try:
        # แยก Logic การดึงชื่อหุ้น: ไทยเติม .BK / US ไม่เติม
        symbol = f"{ticker}.BK" if market == "th" and ".BK" not in ticker else ticker
        df = yf.download(symbol, period="7d", interval="1h", progress=False)
        if df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # คำนวณ Indicators
        ema8 = ta.ema(df['Close'], 8); ema20 = ta.ema(df['Close'], 20)
        hull = ta.hma(df['Close'], 30); vma5 = ta.sma(df['Volume'], 5)
        esa = ta.ema(df['Close'], 9); d = ta.ema(abs(df['Close'] - esa), 9)
        ci = (df['Close'] - esa) / (0.015 * d); wt1 = ta.ema(ci, 12); wt2 = ta.sma(wt1, 4)

        cp = float(df['Close'].iloc[-1]); h_curr = hull.iloc[-1]; h_prev = hull.iloc[-2]
        w1 = wt1.iloc[-1]; w2 = wt2.iloc[-2]; vol = df['Volume'].iloc[-1]
        v5 = vma5.iloc[-1]; e8 = ema8.iloc[-1]
        
        last_time = df.index[-1].astimezone(pytz.timezone('Asia/Bangkok'))
        is_closed = (datetime.now(pytz.timezone('Asia/Bangkok')) - last_time) > timedelta(minutes=55)

        # Logic สัญญาณ
        label, col = "-", "#FFD700"
        if cp > e8 and h_curr > h_prev and vol > (v5 * 1.2): label, col = "BUY", "#00FF00"
        elif w1 > w2 and w1 < -47 and cp > e8: label, col = "DEEP BUY", "#00FF00"
        elif w1 < w2 and w1 > 53: label, col = "P-SELL", "#FFA500"
        elif cp < ema20.iloc[-1] or h_curr < h_prev: label, col = "SELL", "#FF1100"

        if label == "-": return None
        # V10.0-11.0: ถ้ากลางแท่งเทียนให้โชว์ DEEP BUY
        display_label = "DEEP BUY" if not is_closed and label == "BUY" else label

        res = {"Ticker": ticker, "Price": f"{cp:.2f}", "Signal": display_label, "Time": last_time.strftime("%H:%M"), "SigCol": col}
        
        # บันทึกประวัติแยกฝั่ง
        key = f"{market}_{ticker}_{display_label}_{last_time.strftime('%H')}"
        if key not in st.session_state.keys_seen:
            st.session_state.keys_seen.add(key)
            if market == "th": st.session_state.th_logs = pd.concat([pd.DataFrame([res]), st.session_state.th_logs], ignore_index=True)
            else: st.session_state.us_logs = pd.concat([pd.DataFrame([res]), st.session_state.us_logs], ignore_index=True)
        return res
    except: return None

# --- 3. UI DISPLAY ---
st.set_page_config(page_title="PPE V11.0", layout="wide")
st.markdown("<style>.stApp { background-color: #0f172a; } h1,h2,h3,p,span { color: #FFD700 !important; }</style>", unsafe_allow_html=True)

# ส่วนเลือกตลาด (สวิตช์หลัก)
market_select = st.radio("📡 SELECT MARKET:", ["🇹🇭 THAI MARKET", "🇺🇸 US MARKET"], horizontal=True)
mode = "th" if "THAI" in market_select else "us"

tab1, tab2 = st.tabs(["📋 WATCHLIST", "🔍 SIGNAL HISTORY"])

with tab1:
    # Gap การแอดหุ้นแยกตามหน้าจอ
    new_t = st.text_input(f"Add Stock to {market_select}:").upper()
    if st.button("➕ Confirm Add"):
        manage_storage(mode, new_t, "add")
        st.cache_data.clear(); st.rerun()
    
    st.write("---")
    stocks = manage_storage(mode)
    data = [get_signal(s, mode) for s in stocks]
    if data:
        st.dataframe(pd.DataFrame([d for d in data if d]), use_container_width=True, hide_index=True)
        # ปุ่มลบหุ้น
        cols = st.columns(5)
        for i, s in enumerate(stocks):
            if cols[i%5].button(f"✖ {s}", key=f"del_{s}"):
                manage_storage(mode, s, "delete")
                st.cache_data.clear(); st.rerun()

with tab2:
    if st.button("🔄 Manual Refresh"): st.cache_data.clear(); st.rerun()
    # รันสแกนเพื่ออัปเดต History
    for s in manage_storage(mode): get_signal(s, mode)
    
    # แสดงประวัติเฉพาะตลาดที่เลือก
    hist_df = st.session_state.th_logs if mode == "th" else st.session_state.us_history
    st.dataframe(st.session_state.th_logs if mode == "th" else st.session_state.us_logs, use_container_width=True, hide_index=True)

# Auto Refresh 10 นาที
time.sleep(600); st.rerun()
