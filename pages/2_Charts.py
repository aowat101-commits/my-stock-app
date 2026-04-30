import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าหน้าจอและ CSS สำหรับตารางสไตล์ Dark Premium
st.set_page_config(page_title="SET100 Premium", layout="wide")

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

# 2. รายชื่อหุ้นที่ต้องการแสดง (SET100 ตัวหลัก)
SET100_LIST = [
    'ADVANC.BK', 'AOT.BK', 'BBL.BK', 'BDMS.BK', 'CPALL.BK', 'CPN.BK', 'DELTA.BK', 
    'GULF.BK', 'KBANK.BK', 'PTT.BK', 'PTTEP.BK', 'SCB.BK', 'SCC.BK', 'TRUE.BK'
]

st.title("📊 TH SET100 Live Market Board")

# ส่วนดึงข้อมูลและเตรียมแถวตาราง
all_rows = ""
for ticker in SET100_LIST:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="20d")
        if len(hist) > 1:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            diff = current - prev
            pct = (diff / prev) * 100
            
            # คำนวณ RSI (14)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
            rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 100

            style = "pos" if diff > 0 else "neg" if diff < 0 else ""
            sign = "+" if diff > 0 else ""

            all_rows += f"""
            <tr>
                <td><b>{ticker.replace('.BK','')}</b></td>
                <td>฿{prev:,.2f}</td>
                <td>฿{current:,.2f}</td>
                <td class="{style}">{sign}{diff:.2f}</td>
                <td class="{style}">{sign}{pct:.2f}%</td>
                <td style="color:#60a5fa">{rsi:.2f}</td>
            </tr>
            """
    except:
        continue

# 3. รวมร่างเป็น HTML Table ตัวเดียว (ลบส่วนเกินที่ทำให้เกิดปัญหาออกแล้ว)
full_html_table = f"""
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
        {all_rows}
    </tbody>
</table>
"""

# แสดงผลเพียงครั้งเดียวด้วยคำสั่งที่ถูกต้อง
st.markdown(full_html_table, unsafe_allow_html=True)

st.caption(f"อัปเดตเมื่อ: {datetime.now().strftime('%H:%M:%S')}")

if st.button("Update Data"):
    st.rerun()