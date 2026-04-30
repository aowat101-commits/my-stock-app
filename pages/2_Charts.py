import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

# 1. ตั้งค่าหน้าจอและใส่ CSS เพื่อความสวยงาม (Dark Mode Premium)
st.set_page_config(page_title="SET100 Premium Board", layout="wide")

st.markdown("""
    <style>
    /* ซ่อนแถบสถานะและขีดวิ่งสีฟ้าด้านบน */
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    
    /* พื้นหลังหลักโทนเข้ม */
    .main { background-color: #050a14; }
    
    /* สไตล์ตาราง Custom (อ้างอิงรูป 1777543125050.jpg) */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        color: white;
        background-color: #0b111e;
        border-radius: 10px;
        overflow: hidden;
        font-family: 'Inter', sans-serif;
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
    .pos { color: #10b981; font-weight: bold; } /* เขียวนีออนสำหรับหุ้นบวก */
    .neg { color: #ef4444; font-weight: bold; } /* แดงนีออนสำหรับหุ้นลบ */
    .rsi-val { color: #60a5fa; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น SET100 ครบถ้วนจากข้อมูลของคุณ
SET100_FULL = [
    'ADVANC.BK', 'AOT.BK', 'AWC.BK', 'BANPU.BK', 'BBL.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK',
    'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'EA.BK',
    'EGCO.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'INTUCH.BK', 'IRPC.BK', 'IVL.BK',
    'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'OSP.BK',
    'PLANB.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'RATCH.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK',
    'SIRI.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STGT.BK', 'TASCO.BK', 'TCAP.BK', 'TIDLOR.BK', 'TISCO.BK', 'TOP.BK',
    'TRUE.BK', 'TTB.BK', 'TU.BK', 'WHA.BK'
]

# --- Sidebar สำหรับตั้งค่าการรีเฟรช ---
st.sidebar.header("⏱️ Live Settings")
refresh_rate = st.sidebar.slider("ความถี่รีเฟรช (วินาที)", 10, 300, 30)

# --- ฟังก์ชันดึงข้อมูลและสร้าง HTML Row ---
def fetch_stock_data():
    html_rows = ""
    for ticker in SET100_FULL:
        try:
            stock = yf.Ticker(ticker)
            # ดึงข้อมูลย้อนหลัง 20 วันเพื่อใช้คำนวณ RSI (14 วัน)
            hist = stock.history(period="20d")
            if len(hist) > 1:
                current = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change = current - prev_close
                p_change = (change / prev_close) * 100
                
                # การคำนวณ RSI เบื้องต้น
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 100
                
                # กำหนด Class สี
                c_class = "pos" if change > 0 else "neg" if change < 0 else ""
                sign = "+" if change > 0 else ""
                
                # สร้างแถวตาราง (เรียงลำดับ: Ticker, ปิดก่อนหน้า, ล่าสุด, เปลี่ยนแปลง, %, RSI)
                html_rows += f"""
                <tr>
                    <td><b>{ticker.replace('.BK', '')}</b></td>
                    <td>฿{prev_close:,.2f}</td>
                    <td>฿{current:,.2f}</td>
                    <td class="{c_class}">{sign}{change:.2f}</td>
                    <td class="{c_class}">{sign}{p_change:.2f}%</td>
                    <td class="rsi-val">{rsi:.2f}</td>
                </tr>
                """
        except:
            continue
    return html_rows

# --- ส่วนแสดงผลหลัก ---
st.title("📊 TH SET100 Live Market Board")

# สร้างพื้นที่ว่างสำหรับอัปเดตข้อมูลเฉพาะจุด (ทำให้หน้านิ่ง ไม่กระตุก)
table_placeholder = st.empty()
info_placeholder = st.empty()

# ลูปทำงานอัตโนมัติตามเวลาที่ตั้งไว้
while True:
    rows_content = fetch_stock_data()
    
    # โครงสร้างตาราง HTML ทั้งหมด
    full_table_html = f"""
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
            {rows_content}
        </tbody>
    </table>
    """
    
    # แสดงผลตารางโดยใช้ unsafe_allow_html=True เพื่อให้ HTML ทำงาน
    table_placeholder.markdown(full_table_html, unsafe_allow_html=True)
    
    # แสดงเวลาอัปเดตล่าสุด
    info_placeholder.caption(f"อัปเดตล่าสุด: {datetime.now().strftime('%H:%M:%S')} | รอบการรีเฟรช: {refresh_rate} วินาที")
    
    # หยุดรอตามเวลาที่ตั้งไว้ใน Sidebar
    time.sleep(refresh_rate)
    st.rerun()
