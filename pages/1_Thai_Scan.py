import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. ปรับแต่ง UI ให้เหมาะสมกับ Mobile Screens ---
st.set_page_config(page_title="Guardian Mobile", layout="wide")
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    /* ปรับตัวอักษรตารางให้เล็กลงแต่ชัดเจนสำหรับมือถือ */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { 
        font-size: 11px !important; padding: 4px !important; 
    }
    /* ปรับความสูงของตารางและระยะห่าง */
    .stDataFrame { height: 450px; }
    /* สไตล์ Pop-up เต็มจอ */
    .full-screen-overlay {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: #0f172a; z-index: 100000; overflow-y: auto; padding: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันจำลองข้อมูล (News Summary & Bid/Offer) ---
def get_mock_summary(ticker):
    return f"📌 **สรุป ({ticker}):** ราคาทะลุแนวต้านสำคัญด้วยวอลุ่มหนาแน่น มีแรงซื้อสะสมชัดเจนในกลุ่ม mai รับข่าวดีโครงการใหญ่ช่วงกลางปี"

def get_mock_bo():
    return pd.DataFrame({
        'Bid_V': ['1.2M', '500K', '800K'],
        'Price': ['10.20', '10.15', '10.10'],
        'Off_V': ['400K', '1.1M', '900K']
    })

# --- 3. ฟังก์ชันดึงหุ้นย้อนหลัง 20 ตัว (Test UI) ---
@st.cache_data
def get_test_ui_20():
    tickers = ['AU', 'SPA', 'TKN', 'XO', 'DITTO', 'BE8', 'BBIK', 'MASTER', 'SABINA', 'WHA', 
               'SAPPE', 'SISB', 'SNNP', 'ICHI', 'KAMART', 'COCOCO', 'KLINIQ', 'PLANB', 'MC', 'CHG']
    results = []
    now = datetime.now(pytz.timezone('Asia/Bangkok'))
    for i, t in enumerate(tickers):
        prev_close = 12.0 + i
        curr_price = prev_close * (1 + np.random.uniform(-0.01, 0.04))
        chg = ((curr_price - prev_close) / prev_close) * 100
        
        results.append({
            "Ticker": t,
            "ราคาปิดวันก่อนหน้า": prev_close,
            "ราคา": curr_price,
            "%เปลี่ยนแปลง": chg,
            "Signal": "🚀 ซื้อ",
            "เวลา": (now - timedelta(minutes=i*15)).strftime("%H:%M"),
            "วันที่": (now - timedelta(minutes=i*15)).strftime("%d/%m/%y"),
            "raw_time": now - timedelta(minutes=i*15)
        })
    return pd.DataFrame(results)

# --- 4. หน้าจอหลัก (Main Interface) ---
st.subheader("🛰️ Guardian Intelligence: Mobile UI Test")

if st.button("🔄 SCAN ALL (SET100 + sSET/MAI)", use_container_width=True):
    st.rerun()

df_20 = get_test_ui_20()

# ส่วนเลือกหุ้นเพื่อ Pop-up (ปรับให้เลือกง่ายบนมือถือ)
selected = st.selectbox("🎯 เลือกหุ้นเพื่อดูรายละเอียด (Full-Screen)", ["--- เลือก Ticker ---"] + list(df_20['Ticker']))

# แสดงตารางเรียงจากซ้ายไปขวาตามสั่ง และทศนิยม 2 ตำแหน่ง
st.dataframe(
    df_20.drop(columns=['raw_time']).style.format({
        "ราคาปิดวันก่อนหน้า": "{:.2f}",
        "ราคา": "{:.2f}",
        "%เปลี่ยนแปลง": "{:.2f}"
    }).apply(lambda x: ["color: #10b981" if x.name == "%เปลี่ยนแปลง" and x.value > 0 else "color: #ffffff"] * len(x), axis=1),
    use_container_width=True, hide_index=True
)

# --- 5. Pop-up เต็มจอ (Mobile Tactical View) ---
if selected != "--- เลือก Ticker ---":
    with st.container():
        st.markdown('<div class="full-screen-overlay">', unsafe_allow_html=True)
        if st.button("❌ ปิดหน้าต่างนี้", use_container_width=True):
            st.rerun()
        
        st.markdown(f"### 📈 {selected} Analysis")
        
        # กราฟ Candlestick ขนาดพอดีมือถือ
        fig = go.Figure(data=[go.Candlestick(x=[1,2,3,4,5], open=[10,11,10,12,11], 
                                            high=[12,13,12,14,13], low=[9,10,9,11,10], close=[11,10,12,11,12])])
        fig.update_layout(height=350, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # ส่วนสรุปข่าวและปุ่ม Bid/Offer
        st.info(get_mock_summary(selected))
        
        if st.button("📊 ดูตาราง Bid / Offer", use_container_width=True):
            st.table(get_mock_bo())
            
        st.markdown('</div>', unsafe_allow_html=True)
