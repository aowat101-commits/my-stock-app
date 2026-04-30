import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

# 1. การตั้งค่าหน้าจอและสไตล์ Dark Premium
st.set_page_config(page_title="SET100 Premium Board", layout="wide")

st.markdown("""
    <style>
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
        border-bottom: 2px solid #1e293b;
    }
    .custom-table td {
        padding: 15px;
        border-bottom: 1px solid #1e293b;
    }
    .pos { color: #10b981; font-weight: bold; }
    .neg { color: #ef4444; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น
SET100_LIST = ['ADVANC.BK', 'AOT.BK', 'BBL.BK', 'BDMS.BK', 'CPALL.BK', 'DELTA.BK', 'KBANK.BK', 'PTT.BK', 'SCB.BK', 'SCC.BK']

st.title("📊 TH SET100 Live Market Board")

# --- Sidebar: ปรับหน่วยเป็นนาที ---
st.sidebar.header("⏱️ Live Settings")
refresh_min = st.sidebar.slider("รีเฟรชอัตโนมัติ (นาที)", 0.5, 10.0, 1.0, step=0.5)
refresh_sec = int(refresh_min * 60)

if st.sidebar.button("🔄 อัปเดตตอนนี้"):
    st.rerun()

def get_table_html():
    rows = ""
    for ticker in SET100_LIST:
        try:
            stock = yf.Ticker(ticker)
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

                val_style = "pos" if diff > 0 else "neg"
                rows += f"""
                <tr>
                    <td><b>{ticker.replace('.BK','')}</b></td>
                    <td>฿{prev:,.2f}</td>
                    <td>฿{curr:,.2f}</td>
                    <td class="{val_style}">{diff:+.2f}</td>
                    <td class="{val_style}">{pct:+.2f}%</td>
                    <td style="color:#60a5fa">{rsi:.2f}</td>
                </tr>
                """
        except: continue
    return rows

# --- ส่วนแสดงผล ---
t_place = st.empty()
i_place = st.empty()

while True:
    table_rows = get_table_html()
    
    full_html = f"""
    <table class="custom-table">
        <thead>
            <tr>
                <th>Ticker</th><th>ปิดก่อนหน้า</th><th>ล่าสุด</th><th>เปลี่ยนแปลง</th><th>%</th><th>RSI</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    """
    
    # แสดงตาราง (ตรวจสอบว่าไม่มีข้อความอื่นหลุดมาบรรทัดนี้)
    t_place.markdown(full_html, unsafe_allow_html=True)
    i_place.caption(f"อัปเดตเมื่อ: {datetime.now().strftime('%H:%M:%S')} | ทุก {refresh_min} นาที")
    
    time.sleep(refresh_sec)
    st.rerun()