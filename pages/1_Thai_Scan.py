import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. ปรับแต่ง UI ให้ล็อกตายตัวและรองรับการ Render บน Chrome Android ---
st.set_page_config(page_title="Guardian Alpha Mobile", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    
    /* ล็อกหัวตารางและซ่อนปุ่ม Sort */
    [data-testid="stTableDataHeaderCell"], th {
        pointer-events: none !important;
        cursor: default !important;
    }
    button[title="Sort column"], .st-emotion-cache-1pxm6y3, [data-testid="stHeaderActionElements"] {
        display: none !important;
    }

    /* ปรับฟอนต์ตารางให้กระชับสำหรับมือถือ */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { 
        font-size: 10.5px !important; padding: 2px !important;
    }
    .stDataFrame { height: 420px; }

    /* ปรับปรุง Overlay ให้ Chrome Android แสดงผลได้ชัวร์ */
    .mobile-overlay {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: #0f172a; z-index: 99999; overflow-y: auto; padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันดึงข้อมูล (เรียงตามเวลาล่าสุด) ---
@st.cache_data
def get_slim_test_20():
    tickers = ['AU', 'SPA', 'TKN', 'XO', 'DITTO', 'BE8', 'BBIK', 'MASTER', 'SABINA', 'WHA', 
               'SAPPE', 'SISB', 'SNNP', 'ICHI', 'KAMART', 'COCOCO', 'KLINIQ', 'PLANB', 'MC', 'CHG']
    results = []
    # เวลาปัจจุบันอ้างอิง: 2026-05-02 14:08:53
    now = datetime(2026, 5, 2, 14, 8, 53, tzinfo=pytz.timezone('Asia/Bangkok'))
    for i, t in enumerate(tickers):
        prev_c = 12.0 + i
        sig = "🚀 BUY" if i % 2 == 0 else "🔻 SELL"
        curr_p = prev_c * (1 + np.random.uniform(-0.04, 0.04))
        results.append({
            "Ticker": t, "Prev": prev_c, "Price": curr_p, "Chg%": ((curr_p-prev_c)/prev_c)*100, 
            "Signal": sig, "Time": (now - timedelta(minutes=i*15)).strftime("%H:%M"), 
            "Date": (now - timedelta(minutes=i*15)).strftime("%d/%m/%y"), 
            "raw_t": now - timedelta(minutes=i*15)
        })
    return pd.DataFrame(results).sort_values(by="raw_t", ascending=False)

def style_dynamic_columns(row):
    sig_color = '#10b981' if "BUY" in str(row['Signal']) else '#ef4444'
    price_color = '#10b981' if row['Chg%'] > 0 else '#ef4444'
    return [f'color: {price_color}' if col in ['Price', 'Chg%'] else f'color: {sig_color}' for col in row.index]

# --- 3. ส่วนแสดงผลหลัก ---
st.subheader("🛰️ Guardian: Mobile Alpha (Strict Layout Locked)")

if st.button("🔄 REFRESH SCAN", use_container_width=True):
    st.rerun()

df_slim = get_slim_test_20()
selected = st.selectbox("🎯 Tap to View Details", ["--- Select Ticker ---"] + list(df_slim['Ticker']))

st.dataframe(
    df_slim.drop(columns=['raw_t']).style.format({"Prev": "{:.2f}", "Price": "{:.2f}", "Chg%": "{:.2f}"}).apply(style_dynamic_columns, axis=1),
    use_container_width=True, hide_index=True,
    column_config={col: st.column_config.Column(disabled=True) for col in df_slim.columns}
)

# --- 4. แก้ไขจุดที่เป็นหน้าว่าง (Interactive Graph Fix) ---
if selected != "--- Select Ticker ---":
    with st.container():
        st.markdown('<div class="mobile-overlay">', unsafe_allow_html=True)
        if st.button("❌ CLOSE ANALYSIS", use_container_width=True):
            st.rerun()
        
        st.markdown(f"### 📈 {selected} Deep Analysis")
        
        # สร้างกราฟจำลองที่รองรับการซูมบนมือถือ
        fig = go.Figure(data=[go.Candlestick(
            x=['09:00', '10:00', '11:00', '12:00', '13:00'],
            open=[10, 11, 10, 12, 11], high=[12, 13, 12, 14, 13],
            low=[9, 10, 9, 11, 10], close=[11, 10, 12, 11, 12]
        )])
        
        fig.update_layout(
            height=380, template="plotly_dark", 
            margin=dict(l=5, r=5, t=5, b=5), 
            xaxis_rangeslider_visible=False,
            dragmode='pan' # ตั้งค่าให้ใช้นิ้วเลื่อนกราฟได้ทันที
        )
        
        # Render กราฟด้วยพารามิเตอร์ที่เสถียรที่สุดสำหรับ Chrome Android
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': False, 
            'scrollZoom': True, 
            'responsive': True
        })
        
        st.info(f"📌 **{selected} สรุป:** สัญญาณทางเทคนิคบ่งชี้แรงซื้อสะสม")
        st.markdown('</div>', unsafe_allow_html=True)
