import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

# 1. ตั้งค่าหน้าจอและ CSS สำหรับตารางสไตล์ Dark Premium (ไม่มีขีดวิ่งสีฟ้า)
st.set_page_config(page_title="SET100 Premium Board", layout="wide")

st.markdown("""
    <style>
    /* ซ่อนขีดวิ่งสีฟ้าและ Spinner ด้านบน */
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    
    .main { background-color: #050a14; }
    
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        color: white;
        background-color: #0b111e;
        border-radius: 10px;
        overflow: hidden;
    }
    .custom-table th {
        background-color: #161e2e;
        color: #94a3b8;
        text-align: left;
        padding: 15px;
        font-size: 14px;
        border-bottom: 2px solid #1e293b;
    }
    .custom-table td {
        padding: 15px;
        border-bottom: 1px solid #1e293b;
        font-size: 16px;
    }
    .pos { color: #10b981; font-weight: bold; }
    .neg { color: #ef4444; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น SET100
SET100_LIST = [
    'ADVANC.BK', 'AOT.BK', 'BBL.BK', 'BDMS.BK', 'CPALL.BK', 'CPN.BK', 'DELTA.BK', 
    'GULF.BK', 'KBANK.BK', 'PTT.BK', 'PTTEP.BK', 'SCB.BK', 'SCC.BK', 'TRUE.BK'
]

st.title("📊 TH SET100 Live Market Board")

# --- Sidebar: ปรับหน่วยเป็นนาที และเพิ่มปุ่มอัปเดต ---
st.sidebar.header("⏱️ Live Settings")
# ตัวเลือกหน่วยเป็นนาที
refresh_minutes = st.sidebar.slider("ความถี่รีเฟรชอัตโนมัติ (นาที)", 0.5, 10.0, 1.0, step=0.5)[cite: 1]
refresh_seconds = int(refresh_minutes * 60)[cite: 1]

# ปุ่มกดอัปเดตแบบ Manual
if st.sidebar.button("🔄 อัปเดตข้อมูลตอนนี้"):[cite: 1]
    st.rerun()

def fetch_data_html():
    html_content = ""
    for ticker in SET100_LIST:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="20d")
            if len(hist) > 1:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change = current - prev
                p_change = (change / prev) * 100
                
                # RSI (14)
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 100

                style = "pos" if change > 0 else "neg" if change < 0 else ""
                sign = "+" if change > 0 else ""

                html_content += f"""
                <tr>
                    <td><b>{ticker.replace('.BK','')}</b></td>
                    <td>฿{prev:,.2f}</td>
                    <td>฿{current:,.2f}</td>
                    <td class="{style}">{sign}{change:.2f}</td>
                    <td class="{style}">{sign}{p_change:.2f}%</td>
                    <td style="color:#60a5fa">{rsi:.2f}</td>
                </tr>
                """
        except: continue
    return html_content

# --- ส่วนแสดงผล ---
table_placeholder = st.empty()
info_placeholder = st.empty()

while True:
    rows = fetch_data_html()
    
    full_table = f"""
    <table class="custom-table">
        <thead>
            <tr>
                <th>Ticker</th>
                <th>ปิดก่อนหน้า</th>
                <th>ล่าสุด</th>
                <th>เปลี่ยนแปลง</th>
                <th>%</th>
                <th>RSI</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    """
    
    # แสดงผลตารางด้วยคำสั่งที่ถูกต้องเพียงครั้งเดียว
    table_placeholder.markdown(full_table, unsafe_allow_html=True)[cite: 1]
    
    info_placeholder.caption(f"อัปเดตล่าสุด: {datetime.now().strftime('%H:%M:%S')} | รีเฟรชทุก {refresh_minutes} นาที")[cite: 1]
    
    time.sleep(refresh_seconds)[cite: 1]
    st.rerun()