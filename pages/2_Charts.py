import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

# 1. ตั้งค่าหน้าจอและสไตล์ Dark Premium
st.set_page_config(page_title="SET100 Premium Board", layout="wide")

st.markdown("""
    <style>
    /* ซ่อนขีดวิ่งสีฟ้าและ Spinner */
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

# 2. รายชื่อหุ้น SET100 (ใช้ลิสต์เดิมของคุณ)
tickers = [
    'ADVANC.BK', 'AOT.BK', 'BBL.BK', 'BDMS.BK', 'CPALL.BK', 'DELTA.BK', 
    'GULF.BK', 'KBANK.BK', 'PTT.BK', 'SCB.BK', 'SCC.BK', 'TRUE.BK'
]

st.title("📊 TH SET100 Live Market Board")

# --- Sidebar: ปรับช่วงเวลาเป็น 1-60 นาที และปุ่มกด ---
st.sidebar.header("⏱️ Live Settings")
# ปรับช่วงการรีเฟรชเป็น 1-60 นาที ตามคำขอ
refresh_min = st.sidebar.slider("ความถี่รีเฟรชอัตโนมัติ (นาที)", 1, 60, 1)[cite: 1]
refresh_sec = refresh_min * 60[cite: 1]

if st.sidebar.button("🔄 อัปเดตตอนนี้"):[cite: 1]
    st.rerun()

def get_table_content():
    html_rows = ""
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="20d")
            if len(hist) > 1:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                diff = curr - prev
                pct = (diff / prev) * 100
                
                # RSI 14
                delta = hist['Close'].diff()
                up = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
                down = -delta.clip(upper=0).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (up / down))) if down != 0 else 100

                style = "pos" if diff > 0 else "neg" if diff < 0 else ""
                sign = "+" if diff > 0 else ""

                html_rows += f"""
                <tr>
                    <td><b>{t.replace('.BK','')}</b></td>
                    <td>฿{prev:,.2f}</td>
                    <td>฿{curr:,.2f}</td>
                    <td class="{style}">{sign}{diff:.2f}</td>
                    <td class="{style}">{sign}{pct:.2f}%</td>
                    <td style="color:#60a5fa">{rsi:.2f}</td>
                </tr>
                """
        except:
            continue
    return html_rows

# --- ส่วนแสดงผลหลัก ---
# ใช้ Placeholder เพื่อให้ข้อมูลอัปเดตทับที่เดิมและหน้านิ่งที่สุด
table_placeholder = st.empty()
info_placeholder = st.empty()

while True:
    rows = get_table_content()
    
    full_table_html = f"""
    <table class="custom-table">
        <thead>
            <tr>
                <th>Ticker</th>
                <th>ราคาปิดก่อนหน้า</th>
                <th>ราคาล่าสุด</th>
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
    
    # แสดงตารางเพียงจุดเดียวเพื่อป้องกันโค้ดหลุด
    table_placeholder.markdown(full_table_html, unsafe_allow_html=True)[cite: 1]
    
    info_placeholder.caption(f"อัปเดตเมื่อ: {datetime.now().strftime('%H:%M:%S')} | รีเฟรชทุก {refresh_min} นาที")[cite: 1]
    
    time.sleep(refresh_sec)[cite: 1]
    st.rerun()