import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าพื้นฐานและ CSS สำหรับ Dark Theme
st.set_page_config(page_title="SET100 Premium", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    .main { background-color: #050a14; }
    .custom-table {
        width: 100%; border-collapse: collapse; color: white;
        background-color: #0b111e; border-radius: 10px; overflow: hidden;
    }
    .custom-table th {
        background-color: #161e2e; color: #94a3b8; text-align: left;
        padding: 15px; font-size: 14px; border-bottom: 2px solid #1e293b;
    }
    .custom-table td { padding: 15px; border-bottom: 1px solid #1e293b; font-size: 16px; }
    .pos { color: #10b981; font-weight: bold; }
    .neg { color: #ef4444; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นที่ต้องการ
tickers = ['ADVANC.BK', 'AOT.BK', 'BBL.BK', 'BDMS.BK', 'CPALL.BK', 'DELTA.BK', 'GULF.BK', 'KBANK.BK', 'PTT.BK', 'SCB.BK', 'SCC.BK', 'TRUE.BK']

# 3. Sidebar: แจ้งสถานะและปุ่ม Manual Refresh
st.sidebar.header("⚙️ ระบบอัปเดต")
st.sidebar.info("รีเฟรชอัตโนมัติ: ทุก 30 นาที")
if st.sidebar.button("🔄 อัปเดตข้อมูลตอนนี้"):
    st.rerun()

# 4. ฟังก์ชันจัดการข้อมูล (ห้ามมีคำสั่งแสดงผลข้างนอกฟังก์ชันนี้)
def fetch_and_build():
    all_rows = ""
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="20d")
            if not hist.empty:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff = curr - prev
                pct = (diff / prev) * 100
                delta = hist['Close'].diff()
                up = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
                down = -delta.clip(upper=0).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (up / down))) if down != 0 else 100
                style = "pos" if diff > 0 else "neg" if diff < 0 else ""
                sign = "+" if diff > 0 else ""
                all_rows += f"""
                <tr>
                    <td><b>{t.replace('.BK','')}</b></td>
                    <td>฿{prev:,.2f}</td><td>฿{curr:,.2f}</td>
                    <td class="{style}">{sign}{diff:.2f}</td>
                    <td class="{style}">{sign}{pct:.2f}%</td>
                    <td style="color:#60a5fa">{rsi:.2f}</td>
                </tr>"""
        except: continue
    return all_rows

# 5. การแสดงผล (ล็อกเวลา 30 นาทีด้วย Fragment)
@st.fragment(run_every="30m")
def show_live_board():
    st.title("📊 TH SET100 Live Market Board")
    rows = fetch_and_build()
    final_html = f"""
    <table class="custom-table">
        <thead><tr><th>Ticker</th><th>ปิดก่อนหน้า</th><th>ล่าสุด</th><th>เปลี่ยนแปลง</th><th>%</th><th>RSI</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>
    <p style='color: gray; font-size: 12px; margin-top: 10px;'>
        อัปเดตเมื่อ: {datetime.now().strftime('%H:%M:%S')} | รีเฟรชทุก 30 นาที
    </p>"""
    st.markdown(final_html, unsafe_allow_html=True)

show_live_board()
