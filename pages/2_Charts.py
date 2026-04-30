import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

# 1. ตั้งค่าหน้าจอและซ่อน UI ที่รบกวนสายตาด้วย CSS
st.set_page_config(page_title="SET100 Premium Board", layout="wide")
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    .main { background-color: #050a14; }
    
    /* สไตล์ตาราง Custom แบบรูป 1777543125050.jpg */
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
        padding: 12px 15px;
        font-size: 14px;
    }
    .custom-table td {
        padding: 15px;
        border-bottom: 1px solid #1e293b;
        font-size: 16px;
    }
    .pos { color: #10b981; font-weight: bold; } /* เขียวนีออน */
    .neg { color: #ef4444; font-weight: bold; } /* แดงนีออน */
    .rsi-box { color: #60a5fa; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# รายชื่อหุ้น (ใช้ลิสต์เดิมของคุณ)
SET100_FULL = ['ADVANC.BK', 'AOT.BK', 'BBL.BK', 'CPALL.BK', 'DELTA.BK', 'KBANK.BK', 'PTT.BK', 'SCB.BK', 'SCC.BK', 'TRUE.BK'] # ตัวอย่างบางส่วนเพื่อความเร็ว

# --- ส่วนควบคุมที่ Sidebar ---
st.sidebar.header("⚙️ Live Settings")
refresh_rate = st.sidebar.slider("ความถี่รีเฟรช (วินาที)", 10, 300, 30)

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def fetch_data_html():
    html_rows = ""
    for ticker in SET100_FULL:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="20d") # ดึงเผื่อคำนวณ RSI
            if len(hist) > 1:
                current = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change = current - prev_close
                p_change = (change / prev_close) * 100
                
                # คำนวณ RSI
                rsi_series = calculate_rsi(hist['Close'])
                rsi_val = rsi_series.iloc[-1]
                
                # กำหนดสีตามค่าการเปลี่ยนแปลง
                c_class = "pos" if change > 0 else "neg" if change < 0 else ""
                sign = "+" if change > 0 else ""
                
                # สร้างแถว HTML (เรียงหัวข้อตามสั่ง)
                html_rows += f"""
                <tr>
                    <td><b>{ticker.replace('.BK', '')}</b></td>
                    <td>฿{prev_close:,.2f}</td>
                    <td>฿{current:,.2f}</td>
                    <td class="{c_class}">{sign}{change:.2f}</td>
                    <td class="{c_class}">{sign}{p_change:.2f}%</td>
                    <td class="rsi-box">{rsi_val:.2f}</td>
                </tr>
                """
        except: continue
    return html_rows

# --- ส่วนแสดงผลหลัก ---
st.title("🇹🇭 SET100 Live Market Board")
table_placeholder = st.empty()
info_placeholder = st.empty()

while True:
    rows = fetch_data_html()
    
    table_html = f"""
    <table class="custom-table">
        <thead>
            <tr>
                <th>Ticker</th>
                <th>ราคาปิดก่อนหน้า</th>
                <th>ราคาล่าสุด</th>
                <th>เปลี่ยนแปลง</th>
                <th>% เปลี่ยนแปลง</th>
                <th>RSI (14)</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    """
    
  table_placeholder.markdown(table_html, unsafe_allow_html=True)
    info_placeholder.caption(f"อัปเดตล่าสุด: {datetime.now().strftime('%H:%M:%S')} | รีเฟรชทุก {refresh_rate} วินาที")
    
    time.sleep(refresh_rate)
    st.rerun()
