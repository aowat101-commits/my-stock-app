import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าหน้าจอและ CSS สไตล์ Loft ตามรูปภาพ
st.set_page_config(page_title="Market Intelligence", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    
    /* ปรับแต่งหัวตาราง (Header) ให้เหมือนในรูป 1777556027968.jpg */
    [data-testid="stDataFrame"] th {
        background-color: #1e293b !important; /* สีน้ำเงินเข้ม Loft */
        color: #94a3b8 !important; /* สีเทาฟ้าสว่าง */
        text-align: center !important;
        font-weight: bold !important;
        font-size: 11px !important;
        padding: 8px 2px !important;
    }
    
    /* ปรับแต่งเนื้อหาตาราง (Body) ให้กระชับสำหรับมือถือ */
    [data-testid="stDataFrame"] td {
        font-size: 11px !important;
        padding: 6px 2px !important;
        text-align: center !important;
        border-bottom: 1px solid #1e293b !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น 20 ตัว (อ้างอิงจากความสนใจของคุณใน User Summary)
watch_20 = [
    'IONQ', 'IREN', 'ONDS', 'SMX', 'DELTA.BK', 'GULF.BK', 'ADVANC.BK', 'PTT.BK', 
    'KBANK.BK', 'SCB.BK', 'CPALL.BK', 'AOT.BK', 'BDMS.BK', 'CPN.BK', 'PTTEP.BK', 
    'SCC.BK', 'INTUCH.BK', 'TRUE.BK', 'EA.BK', 'HANA.BK'
]

# 3. ฟังก์ชันคำนวณสัญญาณ (Signal Logic)
def get_market_signal(rsi, change_pct):
    if rsi < 30:
        return "🚀 Golden", "เข้าเงื่อนไข"
    elif change_pct > 2.5:
        return "🔥 Breakout", "เข้าเงื่อนไข"
    elif rsi > 70:
        return "⚠️ Diverge", "ระวัง"
    else:
        return "Wait", "ติดตามต่อ"

# 4. ฟังก์ชันดึงข้อมูล (Cache 30 นาที)
@st.cache_data(ttl=1800)
def fetch_dashboard_20():
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
                
                sig, status = get_market_signal(rsi, diff_pct)
                
                results.append({
                    "หุ้น (Ticker)": t.replace('.BK', ''),
                    "ราคาปัจจุบัน": f"{curr:,.1f}",
                    "การเปลี่ยนแปลง": diff_pct,
                    "สัญญาณ (Signal)": sig,
                    "สถานะ": status
                })
        except: continue
    return pd.DataFrame(results)

# 5. ส่วนการแสดงผล
st.subheader("🌐 Market Intelligence")
st.caption(f"🕒 อัปเดต: {datetime.now().strftime('%H:%M:%S')} (ทุก 30 นาที)")

df_final = fetch_dashboard_20()

if not df_final.empty:
    # ฟังก์ชันจัดสไตล์ตัวหนังสือ (ไม่ใช้ตัวหนาตามคำขอครั้งก่อน)
    def style_row(row):
        # สี Change (เขียว/แดง/เทาอ่อนเพื่อ Dark Mode)
        change_color = '#10b981' if row['การเปลี่ยนแปลง'] > 0 else '#ef4444' if row['การเปลี่ยนแปลง'] < 0 else '#888888'
        
        # สี Signal
        sig_color = '#10b981' if "Golden" in row['สัญญาณ (Signal)'] or "Breakout" in row['สัญญาณ (Signal)'] else '#ef4444' if "Diverge" in row['สัญญาณ (Signal)'] else '#888888'
        
        return [
            '', # Ticker
            '', # Price
            f'color: {change_color};', # Change
            f'color: {sig_color};', # Signal
            ''  # Status
        ]

    # แสดงผลตารางแบบบีบความกว้างคอลัมน์ให้พอดีมือถือแนวตั้ง
    st.dataframe(
        df_final.style.apply(style_row, axis=1)
                .format({"การเปลี่ยนแปลง": "{:+.1f}%"}),
        column_config={
            "หุ้น (Ticker)": st.column_config.TextColumn("หุ้น (Ticker)", width=65),
            "ราคาปัจจุบัน": st.column_config.TextColumn("ราคา", width=45),
            "การเปลี่ยนแปลง": st.column_config.NumberColumn("Chg", width=45),
            "สัญญาณ (Signal)": st.column_config.TextColumn("Signal", width=65),
            "สถานะ": st.column_config.TextColumn("สถานะ", width=60),
        },
        use_container_width=True,
        height=800,
        hide_index=True
    )
else:
    st.warning("กำลังโหลดข้อมูล...")

# ปุ่ม Refresh สำหรับมือถือ
if st.button("🔄 Force Refresh Now", use_container_width=True):
    st.rerun()
