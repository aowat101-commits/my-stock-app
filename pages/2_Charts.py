import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าหน้าจอและใส่ CSS (ห้ามลบ unsafe_allow_html=True ตอนเรียกใช้)
st.set_page_config(page_title="SET100 Premium", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .main { background-color: #050a14; }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        color: white;
        background-color: #0b111e;
        border-radius: 10px;
    }
    .custom-table th { background-color: #161e2e; color: #94a3b8; padding: 15px; text-align: left; }
    .custom-table td { padding: 15px; border-bottom: 1px solid #1e293b; }
    .pos { color: #10b981; font-weight: bold; }
    .neg { color: #ef4444; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น (เอาแค่ตัวหลักๆ มาทดสอบก่อน ถ้าผ่านค่อยเพิ่มให้ครบครับ)
tickers = ['ADVANC.BK', 'AOT.BK', 'BBL.BK', 'CPALL.BK', 'DELTA.BK', 'KBANK.BK', 'PTT.BK', 'SCB.BK']

st.title("📊 TH SET100 Premium Board")

# ดึงข้อมูล
all_rows = ""
for t in tickers:
    try:
        stock = yf.Ticker(t)
        h = stock.history(period="20d")
        if not h.empty:
            now = h['Close'].iloc[-1]
            prev = h['Close'].iloc[-2]
            diff = now - prev
            pct = (diff / prev) * 100
            
            # RSI 14
            delta = h['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
            rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 100

            style = "pos" if diff > 0 else "neg"
            all_rows += f"""
            <tr>
                <td><b>{t.replace('.BK','')}</b></td>
                <td>฿{prev:,.2f}</td>
                <td>฿{now:,.2f}</td>
                <td class="{style}">{diff:+.2f}</td>
                <td class="{style}">{pct:+.2f}%</td>
                <td style="color:#60a5fa">{rsi:.2f}</td>
            </tr>
            """
    except: continue

# 3. จุดสำคัญ: ต้องใช้คำสั่งนี้เพื่อให้ HTML แสดงผลเป็นตาราง
full_html = f"""
<table class="custom-table">
    <thead>
        <tr>
            <th>Ticker</th><th>ปิดก่อนหน้า</th><th>ล่าสุด</th><th>เปลี่ยนแปลง</th><th>%</th><th>RSI</th>
        </tr>
    </thead>
    <tbody>
        {all_rows}
    </tbody>
</table>
"""

st.markdown(full_html, unsafe_allow_html=True) # <--- ตัวนี้คือหัวใจสำคัญครับ

st.caption(f"อัปเดตเมื่อ: {datetime.now().strftime('%H:%M:%S')}")

# ปุ่มกดรีเฟรชแบบแมนนวล (ป้องกันระบบค้าง)
if st.button("Update Data"):
    st.rerun()