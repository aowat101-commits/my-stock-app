import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP: ล็อกสีเหลืองเข้มเด็ดขาด ---
st.set_page_config(page_title="Guardian V9.3", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"], header, footer {display: none !important;}
    section[data-testid="stSidebar"] { display: none !important; }

    /* บังคับสีเหลืองเข้มให้ตัวหนังสือพื้นฐานทั้งหมด */
    html, body, [data-testid="stWidgetLabel"], .stMarkdown p, .stMarkdown h3 {
        color: #FFD700 !important;
    }

    .home-box {
        background-color: #050a18 !important;
        padding: 40px 15px;
        border-radius: 20px;
        text-align: center;
        border: 2px solid #FFD700;
    }
    
    /* หัวข้อหน้า Home */
    .w-yellow { color: #FFD700 !important; font-size: 42px; font-weight: 800; letter-spacing: 10px; margin: 0; }
    .t-yellow { color: #FFD700 !important; font-size: 32px; font-weight: 800; margin-top: 10px; }

    /* ปุ่มเมนู */
    .stButton > button { 
        width: 100% !important; 
        border-radius: 10px !important; 
        height: 50px !important; 
        border: 1px solid #FFD700 !important;
        color: #FFD700 !important;
    }

    /* ตาราง Watchlist: บังคับหัวตารางสีเหลือง */
    .stDataFrame th { color: #FFD700 !important; }
    .stDataFrame [data-testid="stTable"] td { 
        font-size: 14px !important; 
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCTIONS ---
def get_dt_now():
    tz = pytz.timezone('Asia/Bangkok')
    n = datetime.now(tz)
    d = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"][n.weekday()]
    m = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"][n.month-1]
    return f"📅 วัน{d}, {n.day} {m} {n.year + 543}", f"🕒 {n.strftime('%H:%M:%S')}"

@st.cache_data(ttl=60)
def fetch_stock_v93(ticker):
    try:
        df = yf.download(ticker, period="35d", interval="1h", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        c, p, pp = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2]), float(df['Close'].iloc[-3])
        cv, cp = c - p, ((c - p) / p) * 100
        rsi = ta.rsi(df['Close'], length=14)
        cr = float(rsi.iloc[-1]) if not rsi.empty else 0
        
        # สีเขียว/แดงสว่าง
        g, r = "#00FF00", "#FF3D00"
        mc = g if cv > 0 else (r if cv < 0 else "#FFD700")
        pc = g if p > pp else (r if p < pp else "#FFD700")
        
        return {"Ticker": ticker.replace('.BK', ''), "Prev": f"{p:.2f}", "Price": f"{c:.2f}", 
                "Chg": f"{cv:+.2f}", "%Chg": f"{cp:.2f}%", "RSI(14)": f"{cr:.2f}", 
                "_mc": mc, "_pc": pc}
    except: return None

def apply_color_v93(row):
    m, p = f'color: {row["_mc"]}', f'color: {row["_pc"]}'
    return [m, p, m, m, m, "color: #FFD700", "", ""]

# --- 3. APP ---
if 'pg' not in st.session_state: st.session_state.pg = 'Home'
if 'tw' not in st.session_state: st.session_state.tw = ['DELTA.BK', 'ADVANC.BK']
if 'uw' not in st.session_state: st.session_state.uw = ['IONQ', 'NVDA']

st.button("🏠 Home", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "Home"}), type="primary" if st.session_state.pg == 'Home' else "secondary")

c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 Thai Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "TW"}))
    st.button("🇹🇭 Thai Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "TS"}))
with c2:
    st.button("🇺🇸 US Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "UW"}))
    st.button("🇺🇸 US Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"pg": "US"}))

d_s, t_s = get_dt_now()
curr = st.session_state.pg

if curr == 'Home':
    st.markdown(f"""
    <div class="home-box">
        <p class="w-yellow">WELCOME</p>
        <p class="t-yellow">TRADING HOME</p>
        <div style="padding: 20px 0;">
            <img src="https://images.unsplash.com/photo-1611974714658-d78e19277f21?q=80&w=1000" 
                 style="width: 90%; border-radius: 12px; border: 1px solid #FFD700;"
                 onerror="this.style.display='none'">
        </div>
        <p style="color: #FFD700; margin-top: 20px;">{d_s} | {t_s}</p>
    </div>
    """, unsafe_allow_html=True)

elif curr in ['TW', 'UW']:
    st.markdown(f"<h3 style='text-align:center;'>{'🇹🇭 Thai Watchlist' if curr == 'TW' else '🇺🇸 US Watchlist'}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;'>{t_s}</p>", unsafe_allow_html=True)
    with st.expander("➕ จัดการลิสต์หุ้น"):
        opts = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK', 'HANA.BK', 'KCE.BK'] if curr == 'TW' else ['IONQ', 'NVDA', 'IREN', 'TSLA', 'SMX', 'ONDS']
        if curr == 'TW': st.session_state.tw = st.multiselect("เลือกหุ้นไทย:", opts, default=st.session_state.tw)
        else: st.session_state.uw = st.multiselect("Select US Stocks:", opts, default=st.session_state.uw)
    
    lst = st.session_state.tw if curr == 'TW' else st.session_state.uw
    if lst:
        data = [fetch_stock_v93(t) for t in lst if fetch_stock_v93(t)]
        if data:
            st.dataframe(pd.DataFrame(data).style.apply(apply_color_v93, axis=1), use_container_width=True, hide_index=True, column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))

st.markdown(f'<p style="text-align:center; font-size:12px; margin-top:50px; color: #FFD700; opacity: 0.6;">PPE Guardian V9.3 | {d_s}</p>', unsafe_allow_html=True)
