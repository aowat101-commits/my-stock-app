import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP & CSS (Full Dark Mode & Red Active Button) ---
st.set_page_config(page_title="Guardian Dashboard V8.5", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
    [data-testid="stStatusWidget"], header, .stAppHeader { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp { background-color: #0f172a; }

    /* หัวข้อหน้า: กึ่งกลางและสีเหลืองเข้ม */
    .centered-yellow-title {
        text-align: center !important;
        color: #FFD700 !important;
        font-size: 24px;
        font-weight: 700;
        margin-top: -10px !important;
        margin-bottom: 0px !important;
    }
    .centered-time { text-align: center !important; color: #FFD700 !important; margin-bottom: 5px !important; margin-top: -5px !important; }

    /* หน้า Home: Welcome และ Trading Home เป็นสีเหลือง */
    .welcome-title { color: #FFD700 !important; font-size: 38px; font-weight: 800; text-align: center; letter-spacing: 8px; margin-top: 5px; }
    .trading-home { color: #FFD700 !important; font-size: 32px; font-weight: 800; text-align: center; letter-spacing: 3px; margin-bottom: 15px; }
    
    /* ตาราง: พื้นหลังดำเด็ดขาด (Dark Mode) */
    .stDataFrame [data-testid="stTable"] { background-color: #000000 !important; }
    .stDataFrame th { color: #FFD700 !important; background-color: #000000 !important; border: 0.1px solid #334155 !important; }
    .stDataFrame [data-testid="stTable"] td {
        font-size: 14px !important; 
        background-color: #000000 !important;
        color: #FFD700 !important; /* แถวว่าง/ตัวหนังสือปกติเป็นสีเหลืองเข้ม */
        border: 0.1px solid #334155 !important;
    }

    /* ส่วนจัดการหุ้น: เครื่องหมาย + สีน้ำเงินฟ้า */
    .stExpander details summary p { color: #FFD700 !important; font-weight: 500; }
    .stExpander details summary span svg { fill: #00BFFF !important; }
    
    /* ปุ่มเมนู: ขนาดกะทัดรัด */
    .stButton > button { height: 35px !important; border-radius: 8px !important; width: 100%; font-size: 12px !important; margin-bottom: -10px !important; }
    div.stButton > button[kind="primary"] { background-color: #FF0000 !important; color: white !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE LOGIC: THE GUARDIAN SWING ---
@st.cache_data(ttl=60)
def fetch_guardian_signals(ticker):
    try:
        # ดึงข้อมูลเพื่อคำนวณ Volume MA 5 วัน
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # 1. ค่าตัวแปรหลัก (Inputs)
        ema8 = ta.ema(df['Close'], length=8)
        ema20 = ta.ema(df['Close'], length=20)
        hull = ta.hma(df['Close'], length=30)
        
        # WaveTrend (9, 12)
        wt_n1, wt_n2 = 9, 12
        esa = ta.ema(df['Close'], wt_n1)
        d = ta.ema(abs(df['Close'] - esa), wt_n1)
        ci = (df['Close'] - esa) / (0.015 * d)
        wt1 = ta.ema(ci, wt_n2)
        wt2 = ta.sma(wt1, 4)

        # Volume MA 5
        vma5 = ta.sma(df['Volume'], 5)

        # ข้อมูลแท่งปัจจุบัน
        curr_price = float(df['Close'].iloc[-1])
        prev_close = float(df['Close'].iloc[-2])
        curr_vol = float(df['Volume'].iloc[-1])
        curr_vma5 = float(vma5.iloc[-1])
        curr_ema8 = float(ema8.iloc[-1])
        curr_ema20 = float(ema20.iloc[-1])
        curr_hull = float(hull.iloc[-1])
        prev_hull = float(hull.iloc[-2])
        curr_wt1 = float(wt1.iloc[-1])
        curr_wt2 = float(wt2.iloc[-1])

        # --- 2. เงื่อนไขการแจ้งเตือน (4 สัญญาณ) ---
        signal = "-"
        sig_color = "#FFD700" # สีเหลืองเข้มเริ่มต้น

        # A. Deep Buy (ค่าใหม่: กลางๆ -45 ถึง -50)
        if curr_wt1 > curr_wt2 and curr_wt1 < -47:
            signal = "🔺 DEEP BUY"
            sig_color = "#00FF00"

        # B. Buy (ค่าใหม่: Volume > 1.2x + EMA8)
        elif curr_price > curr_ema8 and curr_hull > prev_hull and curr_vol > (curr_vma5 * 1.2):
            signal = "✅ BUY"
            sig_color = "#00FF00"

        # C. P-Sell (ค่าเดิม: WT > 53)
        elif curr_wt1 < curr_wt2 and curr_wt1 > 53:
            signal = "🔶 P-SELL"
            sig_color = "#FFA500"

        # D. Sell (ค่าเดิม: หลุด EMA20 หรือ Hull แดง)
        elif curr_price < curr_ema20 or curr_hull < prev_hull:
            signal = "🚨 SELL"
            sig_color = "#FF1100"

        # ตรรกะสีตัวเลข (เทียบราคาปิดวันก่อน)
        price_color = "#00FF00" if curr_price > prev_close else "#FF1100"

        return {
            "Ticker": ticker.replace('.BK', ''),
            "Prev": f"{prev_close:.2f}",
            "Price": f"{curr_price:.2f}",
            "Signal": signal,
            "%Chg": f"{((curr_price - prev_close)/prev_close)*100:.2f}%",
            "RSI(14)": f"{float(ta.rsi(df['Close'], length=14).iloc[-1]):.2f}",
            "_pc": price_color,
            "_sc": sig_color
        }
    except: return None

# --- 3. DISPLAY FUNCTIONS ---
def get_thai_datetime():
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
    months = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    return f"📅 วัน{days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year + 543}", f"🕒 {now.strftime('%H:%M:%S')}"

def apply_guardian_style(row):
    p_c = f'color: {row["_pc"]}'
    s_c = f'color: {row["_sc"]}'
    return ['', p_c, p_c, s_c, p_c, 'color: #FFD700', '', '']

# --- 4. NAVIGATION & PAGES ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 't_watch' not in st.session_state: st.session_state.t_watch = ['PTT.BK', 'DELTA.BK', 'ADVANC.BK']
if 'u_watch' not in st.session_state: st.session_state.u_watch = ['IONQ', 'NVDA', 'IREN']

st.button("🏠 Home", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home"}), type="primary" if st.session_state.page == 'Home' else "secondary")

c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 Thai Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TW"}), type="primary" if st.session_state.page == 'TW' else "secondary")
    st.button("🇹🇭 Thai Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TS"}), type="primary" if st.session_state.page == 'TS' else "secondary")
with c2:
    st.button("🇺🇸 US Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"page": "UW"}), type="primary" if st.session_state.page == 'UW' else "secondary")
    st.button("🇺🇸 US Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US"}), type="primary" if st.session_state.page == 'US' else "secondary")

d_s, t_s = get_thai_datetime()
p_curr = st.session_state.page

if p_curr == 'Home':
    st.markdown('<p class="welcome-title">WELCOME</p><p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=1000", use_container_width=True)
    st.markdown(f'<p style="text-align:center; color:#FFD700;">{d_s}  |  {t_s}</p>', unsafe_allow_html=True)

elif p_curr in ['TW', 'UW']:
    st.markdown(f'<p class="centered-yellow-title">{"🇹🇭 Thai" if p_curr == "TW" else "🇺🇸 US"} Watchlist</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="centered-time">{t_s}</p>', unsafe_allow_html=True)
    
    with st.expander("➕ จัดการลิสต์หุ้น"):
        opts = ['PTT.BK', 'DELTA.BK', 'ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'SCB.BK', 'HANA.BK', 'KCE.BK']
        if p_curr == 'TW': st.session_state.t_watch = st.multiselect("เลือกหุ้นไทย:", opts, default=st.session_state.t_watch)
        else: st.session_state.u_watch = st.multiselect("Select US Stocks:", ['IONQ', 'NVDA', 'IREN', 'TSLA', 'SMX', 'ONDS'], default=st.session_state.u_watch)
    
    lst = st.session_state.t_watch if p_curr == 'TW' else st.session_state.u_watch
    if lst:
        data = [fetch_guardian_signals(t) for t in lst if fetch_guardian_signals(t)]
        if data:
            df_display = pd.DataFrame(data)
            st.dataframe(df_display.style.apply(apply_guardian_style, axis=1), 
                         use_container_width=True, hide_index=True, 
                         column_order=("Ticker", "Prev", "Price", "Signal", "%Chg", "RSI(14)"))

st.markdown(f'<p style="text-align:center; color:#FFD700; margin-top:20px; opacity:0.6;">PPE Guardian V8.5 | {d_s}</p>', unsafe_allow_html=True)
