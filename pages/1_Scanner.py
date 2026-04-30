import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าหน้าจอและสไตล์ Loft (อ้างอิงดีไซน์จากรูป 1777556027968.jpg)
st.set_page_config(page_title="Intelligence Dashboard", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    
    /* แถบเวลาอัปเดตด้านบน */
    .time-bar {
        background-color: #1e293b;
        color: #10b981;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
        border: 1px solid #334155;
    }

    /* สไตล์หัวตารางตามรูปภาพ */
    [data-testid="stDataFrame"] th {
        background-color: #1e293b !important;
        color: #94a3b8 !important;
        text-align: center !important;
        font-size: 11px !important;
    }
    
    /* สไตล์เนื้อหาตาราง */
    [data-testid="stDataFrame"] td {
        font-size: 11px !important;
        text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นที่ต้องการเฝ้าระวัง (ลำดับตาม User Summary และหุ้น Tech/Energy ที่ติดตาม)
watch_list = [
    'IONQ', 'IREN', 'ONDS', 'SMX', 'DELTA.BK', 'GULF.BK', 'ADVANC.BK', 'PTT.BK', 
    'KBANK.BK', 'SCB.BK', 'CPALL.BK', 'AOT.BK', 'BDMS.BK', 'CPN.BK', 'PTTEP.BK', 
    'SCC.BK', 'INTUCH.BK', 'TRUE.BK', 'EA.BK', 'HANA.BK'
]

# 3. ฟังก์ชันวิเคราะห์สัญญาณ (Logic สำหรับคัดกรองตัวที่เข้าเงื่อนไข)
def get_market_signal(rsi, change_pct):
    if rsi < 30:
        return "🚀 Golden Cross", "เข้าเงื่อนไข"
    elif change_pct > 2.5:
        return "🔥 Breakout", "เข้าเงื่อนไข"
    elif rsi > 70:
        return "⚠️ RSI Divergence", "ระวัง"
    return None, None # ถ้าไม่เข้าเงื่อนไขจะส่งค่า None

# 4. ฟังก์ชันดึงข้อมูลและคัดกรอง
@st.cache_data(ttl=1800)
def fetch_filtered_data():
    results = []
    for t in watch_list:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="30d")
            if not hist.empty:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                diff_pct = ((curr - prev) / prev) * 100
                
                # คำนวณ RSI (14)
                delta = hist['Close'].diff()
                up = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
                down = -delta.clip(upper=0).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (up / down))) if down != 0 else 100
                
                sig, status = get_market_signal(rsi, diff_pct)
                
                # *** คัดกรองเฉพาะตัวที่มีสัญญาณเท่านั้น ***
                if sig is not None:
                    results.append({
                        "หุ้น (Ticker)": t.replace('.BK', ''),
                        "ราคาปัจจุบัน": f"{curr:,.2f}",
                        "การเปลี่ยนแปลง": diff_pct,
                        "สัญญาณ (Signal)": sig,
                        "สถานะ": status
                    })
        except: continue
    return pd.DataFrame(results)

# 5. การแสดงผลหน้าจอ
st.markdown(f"""
    <div class="time-bar">
        🕒 อัปเดตล่าสุด: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)

df_filtered = fetch_filtered_data()

if not df_filtered.empty:
    # ฟังก์ชันกำหนดสี (เน้นสีเขียวสำหรับสัญญาณบวก และแดงสำหรับระวัง)
    def style_row(row):
        change_color = '#10b981' if row['การเปลี่ยนแปลง'] > 0 else '#ef4444'
        sig_color = '#10b981' if "🚀" in row['สัญญาณ (Signal)'] or "🔥" in row['สัญญาณ (Signal)'] else '#ef4444'
        
        return [
            '', # Ticker
            '', # Price
            f'color: {change_color};', # Change
            f'color: {sig_color};', # Signal
            ''  # Status
        ]

    st.dataframe(
        df_filtered.style.apply(style_row, axis=1)
                   .format({"การเปลี่ยนแปลง": "{:+.2f}%"}),
        column_config={
            "หุ้น (Ticker)": st.column_config.TextColumn("หุ้น (Ticker)", width=70),
            "ราคาปัจจุบัน": st.column_config.TextColumn("ราคา", width=50),
            "การเปลี่ยนแปลง": st.column_config.NumberColumn("Chg", width=50),
            "สัญญาณ (Signal)": st.column_config.TextColumn("Signal", width=80),
            "สถานะ": st.column_config.TextColumn("สถานะ", width=65),
        },
        use_container_width=True,
        height=600,
        hide_index=True
    )
else:
    st.info("ขณะนี้ยังไม่มีหุ้นที่เข้าเงื่อนไขสัญญาณซื้อ/ขาย (กำลังติดตามตลาด...)")

# ปุ่มรีเฟรชข้อมูลแบบเต็มหน้าจอ
if st.button("🔄 Refresh Market Data", use_container_width=True):
    st.rerun()
