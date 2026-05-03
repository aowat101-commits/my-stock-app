import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP: ตรวจสอบ CSS ทีละบรรทัด ---
st.set_page_config(page_title="Guardian V9.1", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* ปิดส่วนประกอบที่ทำให้รกตา */
    [data-testid="stStatusWidget"], header, footer {display: none !important;}
    section[data-testid="stSidebar"] { display: none !important; }

    /* หน้า Home: บังคับสีเข้มและตัวหนังสือสว่าง 100% */
    .home-card {
        background-color: #0f172a !important;
        padding: 40px 20px;
        border-radius: 20px;
        text-align: center;
        border: 2px solid #1e293b;
    }
    .w-head { color: #FFFFFF !important; font-size: 45px; font-weight: 800; letter-spacing: 12px; margin-bottom: 5px; }
    .t-head { color: #FFD700 !important; font-size: 35px; font-weight: 800; letter-spacing: 3px; margin-bottom: 30px; }
    .dt-text { color: #E2E8F0 !important; font-size: 16px; margin-top: 25px; }

    /* ปุ่มเมนู: ปรับขนาดให้พอดี ไม่ซ้อนกัน */
    .stButton > button { 
        width: 100% !important; 
        border-radius: 12px !important; 
        height: 50px !important; 
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    
    /* ตาราง: ปรับสีตัวหนังสือให้ตัดกับพื้นหลัง PC/Mobile */
    .stDataFrame [data-testid="stTable"] td { 
        font-size: 14px !important; 
        font-weight: 500 !important;
        color: inherit; 
    }
    h3 { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE FUNCTIONS: เช็คความถูกต้องของข้อมูล ---
def fetch_thai_dt():
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    d_list = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
    m_list = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    return f"📅 วัน{d_list[now.weekday()]}, {now.day} {m_list[now.month-1]} {now.year + 543}", f"🕒 {now.strftime('%H:%M:%S')}"

@st.cache_data(ttl=60)
def get_stock_data(ticker):
    try:
        df = yf.download(ticker, period="35d", interval="1h", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        c = float(df['Close'].iloc[-1])
        p = float(df['Close'].iloc[-2])
        pp = float(df['Close'].iloc[-3])
        cv = c - p
        cp = (cv / p) * 100
        rsi = ta.rsi(df['Close'], length=14)
        r_val = float(rsi.iloc[-1]) if not rsi.empty else 0
        
        # สีเขียว/แดง ที่สว่างชัดเจน
        g, r = "#00E676", "#FF1744" 
        mc = g if cv > 0 else (r if cv < 0 else "inherit")
        pc = g if p > pp else (r if p < pp else "inherit")
        
        return {"Ticker": ticker.replace('.BK', ''), "Prev": f"{p:.2f}", "Price": f"{c:.2f}", 
                "Chg": f"{cv:+.2f}", "%Chg": f"{cp:.2f}%", "RSI(14)": f"{r_val:.2f}", 
                "_mc": mc, "_pc": pc}
    except: return None

def style_row_v9(row):
    m_style = f'color: {row["_mc"]}'
    p_style = f'color: {row["_pc"]}'
    return [m_style, p_style, m_style, m_style, m_style, "color: inherit", "", ""]

# --- 3. APP LOGIC ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 'tw_list' not in st.session_state: st.session_state.tw_list = ['PTT.BK', 'DELTA.BK']
if 'uw_list' not in st.session_state: st.session_state.uw_list = ['IONQ', 'NVDA']

# เมนูปุ่มกด
st.button("🏠 Home", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home"}), type="primary" if st.session_state.page == 'Home' else "secondary")

c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 Thai Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TW"}))
    st.button("🇹🇭 Thai Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"page": "TS"}))
with c2:
    st.button("🇺🇸 US Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"page": "UW"}))
    st.button("🇺🇸 US Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US"}))

d_str, t_str = fetch_thai_dt()
p_curr = st.session_state.page

# --- 4. PAGE RENDERING ---
if p_curr == 'Home':
    st.markdown(f"""
    <div class="home-card">
        <p class="w-head">WELCOME</p>
        <p class="t-head">TRADING HOME</p>
        <div style="width: 100%; display: flex; justify-content: center;">
            <img src="https://images.unsplash.com/photo-1611974714658-d78e19277f21?q=80&w=1200" 
                 style="max-width: 90%; border-radius: 12px; display: block;">
        </div>
        <p class="dt-text">{d_str} | {t_str}</p>
    </div>
    """, unsafe_allow_html=True)

elif p_curr in ['TW', 'UW']:
    st.markdown(f"### {'🇹🇭 Thai Watchlist' if p_curr == 'TW' else '🇺🇸 US Watchlist'}")
    st.markdown(f"<p style='text-align:center;'>{t_str}</p>", unsafe_allow_html=True)
    with st.expander("➕ จัดการลิสต์หุ้น"):
        opts = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK', 'HANA.BK', 'KCE.BK', 'JMART.BK', 'JMT.BK'] if p_curr == 'TW' else ['IONQ', 'NVDA', 'IREN', 'TSLA', 'SMX', 'ONDS', 'MARA', 'MSTR']
        if p_curr == 'TW': st.session_state.tw_list = st.multiselect("เลือกหุ้น:", opts, default=st.session_state.tw_list)
        else: st.session_state.uw_list = st.multiselect("Select Stocks:", opts, default=st.session_state.uw_list)
    
    selected = st.session_state.tw_list if p_curr == 'TW' else st.session_state.uw_list
    if selected:
        res_data = [get_stock_data(t) for t in selected if get_stock_data(t)]
        if res_data:
            st.dataframe(pd.DataFrame(res_data).style.apply(style_row_v9, axis=1), use_container_width=True, hide_index=True, column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))

elif p_curr in ['TS', 'US']:
    st.markdown(f"### {'🇹🇭 Thai' if p_curr == 'TS' else '🇺🇸 US'} Market Scan")
    st.markdown(f"<p style='text-align:center;'>{t_str}</p>", unsafe_allow_html=True)
    st.info("Scanner is monitoring market signals...")

st.markdown(f'<p style="text-align:center; font-size:12px; margin-top:50px; opacity:0.5;">PPE Guardian V9.1 | {d_str}</p>', unsafe_allow_html=True)
