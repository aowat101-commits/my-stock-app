import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. ปรับแต่ง UI ให้เป็น Ultra-Slim สำหรับ Mobile ---
st.set_page_config(page_title="Guardian Mobile", layout="wide")
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    /* บีบตารางให้เล็กที่สุดแต่ยังอ่านออกและตัดระบบ Sort หัวตารางออก */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { 
        font-size: 10.5px !important; padding: 2px !important;
    }
    /* ซ่อนไอคอน Sort เพื่อความสะอาดตาบนมือถือ */
    button[title="Sort column"] { display: none !important; }
    
    .stDataFrame { height: 420px; }
    .mobile-overlay {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: #0f172a; z-index: 100000; overflow-y: auto; padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันจำลองข้อมูล (Summary & B/O) ---
def get_mock_summary_brief(ticker):
    return f"📌 **{ticker} สรุป:** ราคางัดตัวขึ้นพร้อม Vol. หนาแน่น มีสัญญาณสะสมในหุ้นกลุ่ม mai รับโปรเจกต์ใหม่ไตรมาส 2"

def get_mock_bo_slim():
    return pd.DataFrame({
        'Bid_V': ['1.2M', '500K'],
        'Px': ['10.20', '10.15'],
        'Off_V': ['400K', '1.1M']
    })

# --- 3. ฟังก์ชันดึงหุ้นย้อนหลัง 20 ตัว (Test UI) ---
@st.cache_data
def get_slim_test_20():
    tickers = ['AU', 'SPA', 'TKN', 'XO', 'DITTO', 'BE8', 'BBIK', 'MASTER', 'SABINA', 'WHA', 
               'SAPPE', 'SISB', 'SNNP', 'ICHI', 'KAMART', 'COCOCO', 'KLINIQ', 'PLANB', 'MC', 'CHG']
    results = []
    now = datetime.now(pytz.timezone('Asia/Bangkok'))
    for i, t in enumerate(tickers):
        prev_c = 12.0 + i
        curr_p = prev_c * (1 + np.random.uniform(-0.03, 0.05))
        chg = ((curr_p - prev_c) / prev_c) * 100
        
        results.append({
            "Ticker": t,
            "Prev": prev_c,
            "Price": curr_p,
            "Chg%": chg,
            "Signal": "🚀 BUY",
            "Time": (now - timedelta(minutes=i*15)).strftime("%H:%M"),
            "Date": (now - timedelta(minutes=i*15)).strftime("%d/%m/%y"),
            "raw_t": now - timedelta(minutes=i*15)
        })
    return pd.DataFrame(results)

# --- 4. หน้าจอหลัก (Main Interface) ---
st.subheader("🛰️ Guardian: Mobile Alpha (Color Fixed)")

if st.button("🔄 REFRESH SCAN", use_container_width=True):
    st.rerun()

df_slim = get_slim_test_20()
selected = st.selectbox("🎯 Tap to View Details", ["--- Select Ticker ---"] + list(df_slim['Ticker']))

# ฟังก์ชันกำหนดสีตัวอักษร (เขียว-แดง)
def apply_color_logic(val):
    if isinstance(val, (int, float)):
        color = '#10b981' if val > 0 else '#ef4444' if val < 0 else '#ffffff'
        return f'color: {color}'
    return 'color: #ffffff'

# แสดงตารางพร้อมการเปลี่ยนสี (ใช้ .map แทน .applymap เพื่อแก้ Error)
st.dataframe(
    df_slim.drop(columns=['raw_t']).style.format({
        "Prev": "{:.2f}",
        "Price": "{:.2f}",
        "Chg%": "{:.2f}"
    }).map(apply_color_logic, subset=['Price', 'Chg%']),
    use_container_width=True, 
    hide_index=True
)

# --- 5. Pop-up วิเคราะห์เต็มจอ ---
if selected != "--- Select Ticker ---":
    with st.container():
        st.markdown('<div class="mobile-overlay">', unsafe_allow_html=True)
        if st.button("❌ CLOSE", use_container_width=True):
            st.rerun()
        
        st.markdown(f"### 📈 {selected}")
        fig = go.Figure(data=[go.Candlestick(x=[1,2,3,4,5], open=[10,11,10,12,11], 
                                            high=[12,13,12,14,13], low=[9,10,9,11,10], close=[11,10,12,11,12])])
        fig.update_layout(height=300, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.info(get_mock_summary_brief(selected))
        if st.button("📊 View Bid / Offer", use_container_width=True):
            st.table(get_mock_bo_slim())
        st.markdown('</div>', unsafe_allow_html=True)
