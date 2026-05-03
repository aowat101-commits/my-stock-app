import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP: ล็อกสไตล์ให้คงที่ที่สุด ---
st.set_page_config(page_title="Guardian V9.2", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* ปิดส่วนที่ทำให้หน้าจอเคลื่อน */
    [data-testid="stStatusWidget"], header, footer {display: none !important;}
    section[data-testid="stSidebar"] { display: none !important; }

    /* หน้า Home: ล็อกสีน้ำเงินเข้มและตัวหนังสือขาว/ทอง เท่านั้น */
    .home-container {
        background-color: #0b1120 !important;
        padding: 40px 10px !important;
        border-radius: 15px !important;
        text-align: center !important;
        color: white !important;
        min-height: 400px;
    }
    .w-text { color: #FFFFFF !important; font-size: 40px; font-weight: 800; letter-spacing: 10px; margin: 0; }
    .t-text { color: #FFD700 !important; font-size: 30px; font-weight: 800; margin-top: 10px; }
    .status-info { color: #cbd5e1 !important; font-size: 15px; margin-top: 30px; }

    /* ปุ่มเมนู: จัดให้เต็มความกว้างและสีชัด */
    .stButton > button { 
        width: 100% !important; 
        border-radius: 10px !important; 
        height: 50px !important; 
        font-weight: 600 !important;
    }

    /* ตาราง Watchlist: ตัวอักษรปกติ ไม่หนา */
    .stDataFrame [data-testid="stTable"] td { 
        font-size: 14px !important; 
        font-weight: 400 !important; 
    }
    h3 { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCTIONS: เช็คข้อมูลให้แม่นยำ ---
def get_current_dt():
    tz = pytz.timezone('Asia/Bangkok')
    n = datetime.now(tz)
    d = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"][n.weekday()]
    m = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"][n.month-1]
    return f"📅 วัน{d}, {n.day} {m} {n.year + 543}", f"🕒 {n.strftime('%H:%M:%S')}"

@st.cache_data(ttl=60)
def fetch_data_safe(ticker):
    try:
        df = yf.download(ticker, period="35d", interval="1h", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        c, p, pp = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2]), float(df['Close'].iloc[-3])
        cv, cp = c - p, ((c - p) / p) * 100
        rsi = ta.rsi(df['Close'], length=14)
        r_val = float(rsi.iloc[-1]) if not rsi.empty else 0
        
        # สีสว่างมองเห็นง่าย
        g, r = "#00E676", "#FF1744"
        mc = g if cv > 0 else (r if cv < 0 else "inherit")
        pc = g if p > pp else (r if p < pp else "inherit")
        
        return {"Ticker": ticker.replace('.BK', ''), "Prev": f"{p:.2f}", "Price": f"{c:.2f}", 
                "Chg": f"{cv:+.2f}", "%Chg": f"{cp:.2f}%", "RSI(14)": f"{r_val:.2f}", 
                "_mc": mc, "_pc": pc}
    except: return None

def style_watchlist_row(row):
    mc, pc = f'color: {row["_mc"]}', f'color: {row["_pc"]}'
    return [mc, pc, mc, mc, mc, "color: inherit", "", ""]

# --- 3. APP NAVIGATION ---
if 'pg' not in st.session_state: st.session_state.pg = 'Home'
if 'tw' not in st.session_state: st.session_state.tw = ['PTT.BK', 'DELTA.BK']
if 'uw' not in st.session_state: st.session_state.uw = ['IONQ', 'NVDA']

st.button("🏠 Home", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "Home"}), type="primary" if st.session_state.pg == 'Home' else "secondary")

c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 Thai Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "TW"}))
    st.button("🇹🇭 Thai Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "TS"}))
with c2:
    st.button("🇺🇸 US Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "UW"}))
    st.button("🇺🇸 US Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "US"}))

d_info, t_info = get_current_dt()
curr_pg = st.session_state.pg

# --- 4. PAGE CONTENT ---
if curr_pg == 'Home':
    st.markdown(f"""
    <div class="home-container">
        <p class="w-text">WELCOME</p>
        <p class="t-text">TRADING HOME</p>
        <div style="padding: 20px 0;">
            <img src="https://images.unsplash.com/photo-1611974714658-d78e19277f21?q=80&w=1000" 
                 style="width: 90%; border-radius: 10px; border: 1px solid #334155;"
                 onerror="this.style.display='none'">
        </div>
        <p class="status-info">{d_info} | {t_info}</p>
    </div>
    """, unsafe_allow_html=True)

elif curr_pg in ['TW', 'UW']:
    st.markdown(f"### {'🇹🇭 Thai Watchlist' if curr_pg == 'TW' else '🇺🇸 US Watchlist'}")
    st.markdown(f"<p style='text-align:center;'>{t_info}</p>", unsafe_allow_html=True)
    with st.expander("➕ จัดการลิสต์หุ้น"):
        opts = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK', 'HANA.BK', 'KCE.BK'] if curr_pg == 'TW' else ['IONQ', 'NVDA', 'IREN', 'TSLA', 'SMX', 'ONDS']
        if curr_pg == 'TW': st.session_state.tw = st.multiselect("เลือกหุ้น:", opts, default=st.session_state.tw)
        else: st.session_state.uw = st.multiselect("Select Stocks:", opts, default=st.session_state.uw)
    
    selected_list = st.session_state.tw if curr_pg == 'TW' else st.session_state.uw
    if selected_list:
        data_rows = [fetch_data_safe(t) for t in selected_list if fetch_data_safe(t)]
        if data_rows:
            st.dataframe(pd.DataFrame(data_rows).style.apply(style_watchlist_row, axis=1), use_container_width=True, hide_index=True, column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))

elif curr_pg in ['TS', 'US']:
    st.markdown(f"### {'🇹🇭 Thai' if curr_pg == 'TS' else '🇺🇸 US'} Market Scan")
    st.markdown(f"<p style='text-align:center;'>{t_info}</p>", unsafe_allow_html=True)
    st.info("Scanner is monitoring signals...")

st.markdown(f'<p style="text-align:center; font-size:12px; margin-top:50px; opacity:0.5;">PPE Guardian V9.2 | {d_info}</p>', unsafe_allow_html=True)
