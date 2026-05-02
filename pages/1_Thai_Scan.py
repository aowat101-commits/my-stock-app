import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. สไตล์ Loft สำหรับ Mobile Full-Screen ---
st.set_page_config(page_title="Guardian Alpha Mobile", layout="wide")
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status { background-color: #1e293b; color: #10b981; padding: 10px; border-radius: 6px; text-align: center; font-size: 12px; margin-bottom: 10px; border: 1px solid #334155; }
    /* ปรับแต่งตารางให้ดู Loft และอ่านง่ายบนมือถือ */
    [data-testid="stDataFrame"] td { font-size: 12px !important; height: 40px !important; }
    /* ส่วนของ Pop-up เต็มจอ */
    .full-screen-popup {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0f172a; z-index: 9999; overflow-y: auto; padding: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันจำลองข่าวและ Bid/Offer สำหรับ Test UI ---
def get_mock_news(ticker):
    return f"📌 **สรุปประเด็นสำคัญ ({ticker}):** คาดการณ์กำไรไตรมาสล่าสุดโต 15% จากการขยายสาขาใหม่ และมีแรงซื้อเก็งกำไรในกลุ่มหุ้นขนาดเล็ก (mai) อย่างต่อเนื่อง"

def get_mock_bid_offer():
    data = {
        'Bid_Vol': ['1.2M', '500K', '800K', '2.1M', '1.5M'],
        'Bid_Price': ['10.20', '10.10', '10.00', '9.95', '9.90'],
        'Off_Price': ['10.30', '10.40', '10.50', '10.60', '10.70'],
        'Off_Vol': ['400K', '1.1M', '900K', '3.2M', '1.8M']
    }
    return pd.DataFrame(data)

# --- 3. ฟังก์ชันคำนวณและสแกน (ย้อนหลัง 10 วัน) ---
@st.cache_data(ttl=600)
def scan_signals(tickers):
    results = []
    # ในการเทส UI เราจะจำลองข้อมูลให้ครบ 30 บรรทัด
    for i, t in enumerate(tickers):
        # จำลองข้อมูลย้อนหลัง 30 ตัว เรียงตามเวลาล่าสุด
        results.append({
            "Ticker": t.replace('.BK', ''),
            "ราคา": 10.0 + (i * 0.1),
            "Signal": "🚀 ซื้อ",
            "R:R": round(1.5 + (i * 0.1), 2),
            "Vol(M)": round(12.5 + i, 1),
            "เวลา": (datetime.now() - timedelta(minutes=i*15)).strftime("%H:%M"),
            "raw_time": datetime.now() - timedelta(minutes=i*15)
        })
    return results

# --- 4. ส่วน Dashboard หลัก ---
st.subheader("🛰️ Market Intelligence: 30 Recent Signals")

if st.button("🔍 START SCAN NOW", use_container_width=True):
    st.rerun()

# รายชื่อหุ้นตัวอย่างสำหรับเทส UI 30 บรรทัด
test_tickers = ['AU', 'SPA', 'TKN', 'XO', 'DITTO', 'BE8', 'BBIK', 'MASTER', 'SABINA', 'WHA'] * 3
results = scan_signals(test_tickers)

if results:
    df_display = pd.DataFrame(results).sort_values(by="raw_time", ascending=False).head(30)
    
    # ตารางหลัก 30 บรรทัด
    st.write("💡 *Double-tap (Select) Ticker เพื่อเปิดหน้าต่างเต็มจอ*")
    selected_ticker = st.selectbox("เลือก Ticker เพื่อดูรายละเอียดเต็มจอ (จำลองการ Double Click)", 
                                    [""] + list(df_display['Ticker'].unique()))

    st.dataframe(
        df_display.drop(columns=['raw_time']).style.apply(lambda x: ["color: #10b981"] * len(x), axis=1)
        .format({"ราคา": "{:,.2f}"}),
        use_container_width=True, hide_index=True, height=600
    )

    # --- 5. ระบบ Pop-up เต็มจอ (เมื่อมีการเลือกหุ้น) ---
    if selected_ticker != "":
        with st.container():
            st.markdown('<div class="full-screen-popup">', unsafe_allow_html=True)
            if st.button("❌ ปิดหน้าต่างนี้", use_container_width=True):
                st.rerun()
            
            st.header(f"📈 {selected_ticker} - Tactical View")
            
            # กราฟเทคนิคขนาดใหญ่
            fig = go.Figure(data=[go.Candlestick(x=[1,2,3,4,5], open=[10,11,10,12,11], 
                                                high=[12,13,12,14,13], low=[9,10,9,11,10], close=[11,10,12,11,12])])
            fig.update_layout(height=400, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
            
            # ข้อมูลพื้นฐานและสรุปข่าว
            st.subheader("📄 สรุปประเด็นสำคัญ")
            st.info(get_mock_news(selected_ticker))
            
            # ปุ่มแยกสำหรับดู Bid/Offer
            with st.expander("📊 ดูตาราง Bid / Offer (Order Book)"):
                st.table(get_mock_bid_offer())
            
            st.markdown('</div>', unsafe_allow_html=True)
