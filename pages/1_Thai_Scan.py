import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. UI SETUP & DEEP CSS INJECTION ---
st.set_page_config(page_title="Guardian V8.8", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* 1. ลบส่วนเกินและจัดการพื้นหลัง */
    [data-testid="stStatusWidget"], header, footer {display: none !important;}
    section[data-testid="stSidebar"] { display: none !important; }
    
    /* 2. บังคับหัวข้ออยู่ตรงกลางและสีชัดเจน */
    .stMarkdown h3 { text-align: center !important; width: 100%; margin-top: -10px !important; color: var(--text-color) !important; }
    .stMarkdown p { text-align: center !important; width: 100%; color: var(--text-color) !important; font-size: 14px; }

    /* 3. จัดการสีในตารางแบบเด็ดขาด (รองรับทั้ง Light/Dark) */
    [data-testid="stTable"] { color: var(--text-color) !important; }
    .stDataFrame [data-testid="stTable"] td { 
        font-size: 14px !important; 
        font-weight: 400 !important; 
        padding: 8px !important;
    }
    /* บังคับสีหัวตาราง */
    .stDataFrame th { color: var(--text-color) !important; background-color: rgba(128,128,128,0.1) !important; }

    /* 4. ปุ่มเมนูแบบเต็มความกว้าง */
    .stButton > button { width: 100% !important; border-radius: 10px !important; height: 45px !important; }
    
    .welcome-title { color: #ffffff !important; font-size: 40px; font-weight: 800; text-align: center; letter-spacing: 5px; }
    .trading-home { color: #ffcc00 !important; font-size: 30px; font-weight: 800; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE LOGIC ---
def get_thai_dt():
    tz = pytz.timezone('Asia/Bangkok')
    n = datetime.now(tz)
    d = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"][n.weekday()]
    m = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"][n.month-1]
    return f"📅 วัน{d}, {n.day} {m} {n.year + 543}", f"🕒 {n.strftime('%H:%M:%S')}"

@st.cache_data(ttl=60)
def fetch_v8_8(ticker):
    try:
        df = yf.download(ticker, period="35d", interval="1h", progress=False)
        if df.empty or len(df) < 15: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        c, p, pp = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2]), float(df['Close'].iloc[-3])
        cv = c - p
        cp = (cv / p) * 100
        rsi = ta.rsi(df['Close'], length=14)
        cr = float(rsi.iloc[-1]) if not rsi.empty else 0
        
        # สี High Contrast (เน้นมองเห็นชัดบนพื้นขาว/ดำ)
        green, red = "#00AA00", "#FF0000"
        
        main_c = green if cv > 0 else (red if cv < 0 else "default")
        prev_c = green if p > pp else (red if p < pp else "default")

        return {
            "Ticker": ticker.replace('.BK', ''),
            "Prev": f"{p:.2f}", "Price": f"{c:.2f}",
            "Chg": f"{cv:+.2f}", "%Chg": f"{cp:.2f}%", "RSI(14)": f"{cr:.2f}",
            "_m": main_c, "_p": prev_c
        }
    except: return None

def apply_final_style(row):
    # 'default' จะทำให้ Streamlit ใช้สีพื้นฐานของเครื่องเอง (ขาว/ดำ)
    m = f'color: {row["_m"]}' if row["_m"] != "default" else ""
    p = f'color: {row["_p"]}' if row["_p"] != "default" else ""
    return [m, p, m, m, m, "", "", ""]

# --- 3. APP STRUCTURE ---
if 'page' not in st.session_state: st.session_state.page = 'Home'
if 't_w' not in st.session_state: st.session_state.t_w = ['DELTA.BK', 'ADVANC.BK']
if 'u_w' not in st.session_state: st.session_state.u_w = ['IONQ', 'NVDA']

st.button("🏠 Home", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Home"}), type="primary" if st.session_state.page == 'Home' else "secondary")

c1, c2 = st.columns(2)
with c1:
    st.button("🇹🇭 Thai Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Thai Watchlist"}))
    st.button("🇹🇭 Thai Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"page": "Thai Scan"}))
with c2:
    st.button("🇺🇸 US Watchlist", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US Watchlist"}))
    st.button("🇺🇸 US Market Scan", use_container_width=True, on_click=lambda: st.session_state.update({"page": "US Scan"}))

d_str, t_str = get_thai_dt()
pg = st.session_state.page

if pg == 'Home':
    st.markdown('<p class="welcome-title">WELCOME</p><p class="trading-home">TRADING HOME</p>', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1611974714658-d78e19277f21?q=80&w=1200", use_container_width=True)
    st.markdown(f"<p>{d_str} | {t_str}</p>", unsafe_allow_html=True)

elif "Watchlist" in pg:
    st.markdown(f"### {'🇹🇭 Thai Watchlist' if 'Thai' in pg else '🇺🇸 US Watchlist'}")
    st.markdown(f"<p>{t_str}</p>", unsafe_allow_html=True)
    
    with st.expander("➕ เพิ่ม/ลด หุ้นในลิสต์"):
        opts = ['ADVANC.BK', 'AOT.BK', 'CPALL.BK', 'DELTA.BK', 'PTT.BK', 'SCB.BK', 'JMART.BK', 'JMT.BK', 'HANA.BK', 'KCE.BK'] if "Thai" in pg else ['IONQ', 'NVDA', 'IREN', 'TSLA', 'SMX', 'ONDS']
        if "Thai" in pg: st.session_state.t_w = st.multiselect("เลือกหุ้นไทย:", opts, default=st.session_state.t_w)
        else: st.session_state.u_w = st.multiselect("Select US Stocks:", opts, default=st.session_state.u_w)

    lst = st.session_state.t_w if "Thai" in pg else st.session_state.u_w
    if lst:
        res = [fetch_v8_8(t) for t in lst if fetch_v8_8(t)]
        if res:
            st.dataframe(pd.DataFrame(res).style.apply(apply_final_style, axis=1), use_container_width=True, hide_index=True, column_order=("Ticker", "Prev", "Price", "Chg", "%Chg", "RSI(14)"))

elif "Scan" in pg:
    st.markdown(f"### {'🇹🇭 Thai Market Scan' if 'Thai' in pg else '🇺🇸 US Market Scan'}")
    st.markdown(f"<p>{t_str}</p>", unsafe_allow_html=True)
    st.info("Scanner is Active...")

st.markdown(f'<p style="font-size:12px; margin-top:50px; opacity:0.5;">PPE Guardian V8.8 | {d_str}</p>', unsafe_allow_html=True)
