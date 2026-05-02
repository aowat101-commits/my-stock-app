import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. สไตล์ Loft สำหรับ Mobile (เน้นความกระชับของตาราง) ---
st.set_page_config(page_title="Guardian Alpha Mobile", layout="wide")
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status { background-color: #1e293b; color: #10b981; padding: 10px; border-radius: 6px; text-align: center; font-size: 12px; margin-bottom: 10px; border: 1px solid #334155; }
    [data-testid="stDataFrame"] td { font-size: 12px !important; }
    
    /* หน้าต่าง Pop-up เต็มจอ */
    .full-screen-popup {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: #0f172a; z-index: 99999; overflow-y: auto; padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันจำลองข้อมูล (News & B/O) ---
def get_news_summary(ticker):
    return f"📌 **สรุปประเด็น {ticker}:** ราคางัดตัวขึ้นพร้อมวอลุ่มหนาแน่น มีแรงซื้อเก็งกำไรรับข่าวโครงการใหม่ในไตรมาส 2"

def get_bid_offer_table():
    data = {'Bid_Vol': ['1.5M', '800K', '2.1M'], 'Price': ['10.50', '10.45', '10.40'], 'Off_Vol': ['900K', '1.2M', '3.5M']}
    return pd.DataFrame(data)

# --- 3. ฟังก์ชันดึงข้อมูลย้อนหลัง 20 ตัว (Test UI) ---
@st.cache_data
def get_test_signals_v2():
    tickers = ['AU', 'SPA', 'TKN', 'XO', 'DITTO', 'BE8', 'BBIK', 'MASTER', 'SABINA', 'WHA', 
               'SAPPE', 'SISB', 'SNNP', 'ICHI', 'KAMART', 'COCOCO', 'KLINIQ', 'PLANB', 'MC', 'CHG']
    results = []
    now = datetime.now()
    for i, t in enumerate(tickers):
        close_prev = 10.0 + i
        price_now = close_prev * (1 + (np.random.uniform(-0.02, 0.05)))
        change_pct = ((price_now - close_prev) / close_prev) * 100
        
        results.append({
            "Ticker": t,
            "ราคาปิดวันก่อนหน้า": round(close_prev, 2),
            "ราคา": round(price_now, 2),
            "%เปลี่ยนแปลง": round(change_pct, 2),
            "Signal": "🚀 ซื้อ",
            "เวลา": (now - timedelta(minutes=i*20)).strftime("%H:%M"),
            "วันที่": (now - timedelta(minutes=i*20)).strftime("%d/%m/%y"),
            "raw_time": now - timedelta(minutes=i*20)
        })
    return pd.DataFrame(results)

# --- 4. Dashboard หลัก ---
st.subheader("🛰️ Intelligence Dashboard (20 Recent Signals)")

if st.button("🔍 START SCAN (SET100 + sSET/MAI)", use_container_width=True):
    st.rerun()

df_test = get_test_signals_v2()

# ระบบเลือกหุ้นเพื่อเปิด Pop-up (ใช้ Selectbox แทนการแตะค้างเพื่อความชัวร์บน Mobile)
selected_ticker = st.selectbox("🎯 เลือก Ticker เพื่อเปิดหน้าต่างวิเคราะห์เต็มจอ", ["--- เลือกหุ้น ---"] + list(df_test['Ticker']))

# แสดงตารางตามลำดับและรูปแบบที่ต้องการ
st.dataframe(
    df_test.drop(columns=['raw_time']).style.apply(lambda x: ["color: #10b981"] * len(x), axis=1)
    .format({
        "ราคาปิดวันก่อนหน้า": "{:.2f}",
        "ราคา": "{:.2f}",
        "%เปลี่ยนแปลง": "{:.2f}"
    }),
    use_container_width=True, hide_index=True, height=500
)

# --- 5. ระบบ Pop-up เต็มจอ ---
if selected_ticker != "--- เลือกหุ้น ---":
    with st.container():
        st.markdown('<div class="full-screen-popup">', unsafe_allow_html=True)
        if st.button("❌ ปิดหน้าต่าง (BACK TO LIST)", use_container_width=True):
            st.rerun()
        
        st.header(f"📈 {selected_ticker} Analysis")
        
        # กราฟเทคนิคขนาดใหญ่
        fig = go.Figure(data=[go.Candlestick(x=[1,2,3,4,5], open=[10,11,10,12,11], 
                                            high=[12,13,12,14,13], low=[9,10,9,11,10], close=[11,10,12,11,12])])
        fig.update_layout(height=450, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # สรุปข่าวสำคัญ
        st.subheader("📄 สรุปประเด็นสำคัญ")
        st.info(get_news_summary(selected_ticker))
        
        # ปุ่มแยกสำหรับดู Bid/Offer
        with st.expander("📊 กดเพื่อดูตาราง Bid / Offer"):
            st.table(get_bid_offer_table())
            
        st.markdown('</div>', unsafe_allow_html=True)
