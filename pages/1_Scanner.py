import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าหน้าจอแบบกว้างและสไตล์ Dark Loft
st.set_page_config(page_title="Market Intelligence", layout="wide")

st.markdown("""
    <style>
    /* ปรับแต่งหัวตารางตามรูปภาพ */
    [data-testid="stDataFrame"] th {
        background-color: #1e293b !important;
        color: #94a3b8 !important;
        text-align: center !important;
        font-weight: bold !important;
        border-bottom: 2px solid #334155 !important;
    }
    /* ปรับแต่งขนาดตัวอักษรและระยะห่างให้ดูพรีเมียม */
    [data-testid="stDataFrame"] td {
        font-size: 13px !important;
        padding: 10px !important;
        text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น 20 ตัวล่าสุด (เน้นหุ้นที่คุณสนใจและหุ้นใหญ่)
watch_20 = [
    'IONQ', 'IREN', 'ONDS', 'SMX', 'DELTA.BK', 'GULF.BK', 'ADVANC.BK', 'PTT.BK', 
    'KBANK.BK', 'SCB.BK', 'CPALL.BK', 'AOT.BK', 'BDMS.BK', 'CPN.BK', 'PTTEP.BK', 
    'SCC.BK', 'INTUCH.BK', 'TRUE.BK', 'EA.BK', 'HANA.BK'
]

# 3. ฟังก์ชันวิเคราะห์สัญญาณ (Logic จำลองตามรูปแบบภาพ)
def get_signal(rsi, change_pct):
    if rsi < 30:
        return "🚀 Golden Cross", "เข้าเงื่อนไข"
    elif change_pct > 3:
        return "🔥 Breakout", "เข้าเงื่อนไข"
    elif rsi > 70:
        return "⚠️ RSI Divergence", "ระวัง"
    else:
        return "Wait", "ติดตามต่อ"

# 4. ฟังก์ชันดึงข้อมูล
@st.cache_data(ttl=1800)
def fetch_dashboard_data():
    results = []
    for t in watch_20:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="30d")
            if not hist.empty:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                diff_pct = ((curr - prev) / prev) * 100
                
                # คำนวณ RSI
                delta = hist['Close'].diff()
                up = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
                down = -delta.clip(upper=0).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (up / down))) if down != 0 else 100
                
                sig, status = get_signal(rsi, diff_pct)
                
                results.append({
                    "หุ้น (Ticker)": t.replace('.BK', ''),
                    "ราคาปัจจุบัน": f"${curr:,.2f}" if ".BK" not in t else f"{curr:,.2f}",
                    "การเปลี่ยนแปลง": diff_pct,
                    "สัญญาณ (Signal)": sig,
                    "สถานะ": status
                })
        except: continue
    return pd.DataFrame(results)

# 5. ส่วนแสดงผล
st.subheader("🌐 Market Intelligence Dashboard")
st.write(f"🕒 อัปเดตล่าสุด: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

df_final = fetch_dashboard_data()

if not df_final.empty:
    # ฟังก์ชันกำหนดสีตัวหนังสือ
    def style_dashboard(row):
        # สีสำหรับการเปลี่ยนแปลง
        change_color = '#10b981' if row['การเปลี่ยนแปลง'] > 0 else '#ef4444' if row['การเปลี่ยนแปลง'] < 0 else '#888888'
        
        # สีสำหรับสัญญาณ
        sig_color = '#10b981' if "Golden" in row['สัญญาณ (Signal)'] or "Breakout" in row['สัญญาณ (Signal)'] else '#ef4444' if "Divergence" in row['สัญญาณ (Signal)'] else '#888888'
        
        return [
            '', # Ticker
            'font-weight: bold;', # Price
            f'color: {change_color}; font-weight: bold;', # Change
            f'color: {sig_color}; font-weight: bold;', # Signal
            ''  # Status
        ]

    # แสดงตาราง
    st.dataframe(
        df_final.style.apply(style_dashboard, axis=1)
                .format({"การเปลี่ยนแปลง": "{:+.2f}%"}),
        use_container_width=True,
        height=750,
        hide_index=True
    )
else:
    st.warning("ไม่สามารถดึงข้อมูลได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง")

# ปุ่ม Refresh
if st.button("🔄 Refresh Data"):
    st.rerun()
