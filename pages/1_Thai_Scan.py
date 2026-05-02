import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. ปรับแต่ง UI ให้ล็อกตายตัวและเหมาะสมกับ Mobile ---
st.set_page_config(page_title="Guardian Alpha Mobile", layout="wide")

# CSS ขั้นสูงเพื่อล็อกหัวตารางและซ่อนปุ่ม Sort ทุกจุด
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    
    /* 1. ตัดการตอบสนองของเมาส์ที่หัวตารางทั้งหมด (ล็อกการ Sort และการย้ายคอลัมน์) */
    [data-testid="stTableDataHeaderCell"], th {
        pointer-events: none !important;
        cursor: default !important;
        user-select: none !important;
    }
    
    /* 2. ซ่อนปุ่ม Sort, ไอคอนตัวกรอง และเมนู Action ต่างๆ ของ DataFrame */
    button[title="Sort column"], 
    .st-emotion-cache-1pxm6y3, 
    [data-testid="stHeaderActionElements"],
    [data-testid="stDataFrameResizer"] {
        display: none !important;
    }

    /* 3. ปรับฟอนต์ให้เล็กและกระชับสำหรับหน้าจอมือถือ */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { 
        font-size: 10.5px !important; padding: 2px !important;
    }
    
    .stDataFrame { height: 420px; }

    /* 4. ระบบ Pop-up เต็มจอ (Mobile Overlay) */
    .mobile-overlay {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: #0f172a; z-index: 100000; overflow-y: auto; padding: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันจำลองข้อมูล (Summary & B/O) ---
def get_mock_summary_brief(ticker):
    return f"📌 **{ticker} สรุป:** ราคางัดตัวขึ้นพร้อมวอลุ่มหนาแน่น มีสัญญาณสะสมชัดเจนในกลุ่ม mai รับโปรเจกต์ใหม่ไตรมาส 2"

def get_mock_bo_slim():
    return pd.DataFrame({
        'Bid_V': ['1.2M', '500K'],
        'Px': ['10.20', '10.15'],
        'Off_V': ['400K', '1.1M']
    })

# --- 3. ฟังก์ชันดึงหุ้นย้อนหลัง 20 ตัว (บังคับเรียงตามเวลาล่าสุด) ---
@st.cache_data
def get_slim_test_20():
    tickers = ['AU', 'SPA', 'TKN', 'XO', 'DITTO', 'BE8', 'BBIK', 'MASTER', 'SABINA', 'WHA', 
               'SAPPE', 'SISB', 'SNNP', 'ICHI', 'KAMART', 'COCOCO', 'KLINIQ', 'PLANB', 'MC', 'CHG']
    results = []
    # อ้างอิงเวลาปัจจุบันตามระบบ
    now = datetime(2026, 5, 2, 13, 45, 59, tzinfo=pytz.timezone('Asia/Bangkok'))
    for i, t in enumerate(tickers):
        prev_c = 12.0 + i
        signal_type = "🚀 BUY" if i % 2 == 0 else "🔻 SELL"
        # สุ่มราคาให้มีทั้งบวกและลบเพื่อเทสสี
        curr_p = prev_c * (1 + np.random.uniform(-0.04, 0.04))
        chg = ((curr_p - prev_c) / prev_c) * 100
        
        results.append({
            "Ticker": t,
            "Prev": prev_c,
            "Price": curr_p,
            "Chg%": chg,
            "Signal": signal_type,
            "Time": (now - timedelta(minutes=i*15)).strftime("%H:%M"),
            "Date": (now - timedelta(minutes=i*15)).strftime("%d/%m/%y"),
            "raw_t": now - timedelta(minutes=i*15)
        })
    # เรียงลำดับตามเวลาและวันที่ล่าสุดจากบนลงล่างเท่านั้น
    return pd.DataFrame(results).sort_values(by="raw_t", ascending=False)

# --- 4. ฟังก์ชันกำหนดสีตามเงื่อนไข (Dynamic Color Logic) ---
def style_dynamic_columns(row):
    # สีตามสัญญาณสำหรับ Ticker, Prev และข้อมูลอื่นๆ
    sig_color = '#10b981' if "BUY" in str(row['Signal']) else '#ef4444' if "SELL" in str(row['Signal']) else '#ffffff'
    # สีตามสภาวะราคาจริงสำหรับ Price และ Chg%
    price_status_color = '#10b981' if row['Chg%'] > 0 else '#ef4444' if row['Chg%'] < 0 else '#ffffff'
    
    styles = []
    for col in row.index:
        if col in ['Price', 'Chg%']:
            styles.append(f'color: {price_status_color}')
        else:
            styles.append(f'color: {sig_color}')
    return styles

# --- 5. ส่วนแสดงผลหลัก ---
st.subheader("🛰️ Guardian: Mobile Alpha (Strict Layout Locked)")

if st.button("🔄 REFRESH SCAN", use_container_width=True):
    st.rerun()

df_slim = get_slim_test_20()
selected = st.selectbox("🎯 Tap to View Details", ["--- Select Ticker ---"] + list(df_slim['Ticker']))

# แสดงตารางแบบ Hard-Locked (ห้ามเลื่อน ห้าม Sort ห้ามแก้)
st.dataframe(
    df_slim.drop(columns=['raw_t']).style.format({
        "Prev": "{:.2f}",
        "Price": "{:.2f}",
        "Chg%": "{:.2f}"
    }).apply(style_dynamic_columns, axis=1),
    use_container_width=True, 
    hide_index=True,
    # ปิดความสามารถในการคลิกและแก้ไขคอลัมน์
    column_config={col: st.column_config.Column(disabled=True) for col in df_slim.columns}
)

# --- 6. Pop-up วิเคราะห์เต็มจอ ---
if selected != "--- Select Ticker ---":
    with st.container():
        st.markdown('<div class="mobile-overlay">', unsafe_allow_html=True)
        if st.button("❌ CLOSE ANALYSIS", use_container_width=True):
            st.rerun()
        
        st.markdown(f"### 📈 {selected} Deep Analysis")
        fig = go.Figure(data=[go.Candlestick(x=[1,2,3,4,5], open=[10,11,10,12,11], 
                                            high=[12,13,12,14,13], low=[9,10,9,11,10], close=[11,10,12,11,12])])
        fig.update_layout(height=350, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.info(get_mock_summary_brief(selected))
        if st.button("📊 View Bid / Offer Details", use_container_width=True):
            st.table(get_mock_bo_slim())
        st.markdown('</div>', unsafe_allow_html=True)
