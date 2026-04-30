import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. การตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="Intelligence Dashboard", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    
    /* แถบเวลาอัปเดตปัจจุบัน */
    .time-status {
        background-color: #1e293b;
        color: #10b981;
        padding: 8px;
        border-radius: 6px;
        text-align: center;
        font-size: 12px;
        margin-bottom: 15px;
        border: 1px solid #334155;
    }

    /* สไตล์ตาราง Loft (ตามรูป 1777556027968.jpg) */
    [data-testid="stDataFrame"] th {
        background-color: #1e293b !important;
        color: #94a3b8 !important;
        text-align: center !important;
        font-size: 11px !important;
    }
    [data-testid="stDataFrame"] td {
        font-size: 11px !important;
        text-align: center !important;
        border-bottom: 1px solid #1e293b !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นที่ติดตาม
watch_list = [
    'IONQ', 'IREN', 'ONDS', 'SMX', 'DELTA.BK', 'GULF.BK', 'ADVANC.BK', 
    'PTT.BK', 'KBANK.BK', 'SCB.BK', 'CPALL.BK', 'AOT.BK', 'BDMS.BK', 
    'CPN.BK', 'PTTEP.BK', 'SCC.BK', 'INTUCH.BK', 'TRUE.BK', 'EA.BK', 'HANA.BK'
]

# 3. ฟังก์ชันวิเคราะห์สัญญาณ (Signal Logic)
def identify_signal(rsi, change_pct):
    # ปรับเป็นคำว่า "ซื้อ" และพ่วง Emoji ตามสไตล์รูปภาพ
    if rsi < 35: 
        return "🚀 ซื้อ (Golden)", datetime.now().strftime("%H:%M:%S")
    elif change_pct > 2.0:
        return "🔥 ซื้อ (Breakout)", datetime.now().strftime("%H:%M:%S")
    elif rsi > 70:
        return "⚠️ ระวัง (Diverge)", datetime.now().strftime("%H:%M:%S")
    return None, None

# 4. ฟังก์ชันดึงข้อมูลและกรอง
@st.cache_data(ttl=1800)
def get_actionable_data():
    action_list = []
    for t in watch_list:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="30d")
            if not hist.empty:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-1] if len(hist) < 2 else hist['Close'].iloc[-2]
                diff_pct = ((curr - prev) / prev) * 100
                
                delta = hist['Close'].diff()
                up = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
                down = -delta.clip(upper=0).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (up / down))) if down != 0 else 100
                
                sig, sig_time = identify_signal(rsi, diff_pct)
                
                if sig:
                    action_list.append({
                        "หุ้น (Ticker)": t.replace('.BK', ''),
                        "ราคาปัจจุบัน": f"{curr:,.2f}",
                        "การเปลี่ยนแปลง": diff_pct,
                        "สัญญาณ (Signal)": sig,
                        "เวลาแจ้งเตือน": sig_time
                    })
        except: continue
    return pd.DataFrame(action_list)

# 5. การแสดงผล
st.markdown(f'<div class="time-status">🕒 Current Market Time: {datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

st.subheader("🌐 Market Intelligence Dashboard")

df_filtered = get_actionable_data()

if not df_filtered.empty:
    def style_rows(row):
        c_color = '#10b981' if row['การเปลี่ยนแปลง'] > 0 else '#ef4444'
        s_color = '#10b981' if "ซื้อ" in row['สัญญาณ (Signal)'] else '#ef4444'
        return ['', '', f'color: {c_color};', f'color: {s_color};', 'color: #888888;']

    st.dataframe(
        df_filtered.style.apply(style_rows, axis=1)
                   .format({"การเปลี่ยนแปลง": "{:+.2f}%"}),
        column_config={
            "หุ้น (Ticker)": st.column_config.TextColumn("หุ้น (Ticker)", width=70),
            "ราคาปัจจุบัน": st.column_config.TextColumn("ราคา", width=55),
            "การเปลี่ยนแปลง": st.column_config.NumberColumn("Chg", width=50),
            "สัญญาณ (Signal)": st.column_config.TextColumn("Signal", width=95),
            "เวลาแจ้งเตือน": st.column_config.TextColumn("เวลา", width=65),
        },
        use_container_width=True,
        height=500,
        hide_index=True
    )
else:
    st.info("🔎 ยังไม่พบหุ้นที่เข้าเงื่อนไขสัญญาณซื้อในขณะนี้")

if st.button("🔄 Force Refresh Now", use_container_width=True):
    st.rerun()
