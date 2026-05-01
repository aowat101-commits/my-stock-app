import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและ CSS สำหรับ Mobile Optimized (สไตล์เดียวกับหุ้นไทย)
st.set_page_config(page_title="US Market Monitor", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    
    /* บีบขนาดตัวอักษรและระยะห่างเซลล์ให้เล็กที่สุดสำหรับมือถือ และเป็นตัวธรรมดา */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        font-size: 11px !important;
        padding: 2px 4px !important;
        text-align: center !important;
        font-weight: normal !important;
    }
    
    /* จัดหัวตารางให้สัดส่วนพอดี */
    [data-testid="stDataFrame"] th {
        white-space: nowrap !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นสหรัฐฯ แบบครอบคลุม
us_full_list = [
    'IONQ', 'IREN', 'EOSE', 'SMX', 'ONDS', 'PLTR', 'SOUN', 'BBAI', 'RGTI',
    'NVDA', 'AMD', 'TSM', 'INTC', 'ARM', 'MU', 'AVGO', 'ASML',
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA',
    'MARA', 'RIOT', 'CLSK', 'HIVE', 'COIN', 'MSTR',
    'SPY', 'QQQ', 'SOXX', 'BITO', 'BTC-USD', 'ETH-USD'
]

# 3. Sidebar
st.sidebar.header("⚙️ Settings")
if st.sidebar.button("🔄 Force Refresh"):
    st.rerun()

# 4. ฟังก์ชันดึงข้อมูล (ทศนิยม 2 ตำแหน่ง และคำนวณ RSI)
@st.cache_data(ttl=1800)
def get_us_market_data():
    data_list = []
    # ใช้ลิสต์หุ้น US ทั้งหมด
    for t in us_full_list:
        try:
            stock = yf.Ticker(t)
            # ดึงข้อมูล 30 วันเพื่อคำนวณ RSI ให้แม่นยำ
            hist = stock.history(period="30d")
            if not hist.empty and len(hist) >= 15:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff = curr - prev
                pct = ((curr - prev) / prev) * 100 if prev != 0 else 0.0
                
                # คำนวณ RSI (14)
                delta = hist['Close'].diff()
                up = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
                down = -delta.clip(upper=0).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (up / down))) if down != 0 else 100

                data_list.append({
                    "Ticker": t,
                    "Price": curr,
                    "Change": diff,
                    "% Change": pct,
                    "RSI (14)": rsi
                })
        except: continue
    return pd.DataFrame(data_list)

# 5. การแสดงผลแบบเดียวกับหุ้นไทย
@st.fragment(run_every="5m")
def show_us_charts_board():
    st.title("📊 US Market Monitor Live")
    df = get_us_market_data()
    
    if not df.empty:
        # ฟังก์ชันกำหนดสี (ตัวหนังสือปกติ)
        def style_general(val):
            if val > 0: return 'color: #10b981; font-weight: normal;'
            if val < 0: return 'color: #ef4444; font-weight: normal;'
            return 'color: #888888; font-weight: normal;'

        def style_rsi(val):
            if val < 30: return 'color: #ef4444; font-weight: normal;'
            return 'color: #888888; font-weight: normal;'

        def style_row_base(row):
            color = '#10b981' if row['Change'] > 0 else '#ef4444' if row['Change'] < 0 else '#888888'
            style = f'color: {color}; font-weight: normal;'
            return [style, style, '', '', '']

        # ใส่ ⚠️ หน้า Ticker ถ้า RSI < 30 (เหมือนหุ้นไทย)
        df_display = df.copy()
        df_display['Ticker'] = df_display.apply(lambda x: f"⚠️{x['Ticker']}" if x['RSI (14)'] < 30 else x['Ticker'], axis=1)
        
        # เรียงลำดับตาม % Change
        df_display = df_display.sort_values(by="% Change", ascending=False)

        # แสดงผลตาราง (ทศนิยม 0.00)
        st.dataframe(
            df_display.style.apply(style_row_base, axis=1) \
                    .map(style_general, subset=['Change', '% Change']) \
                    .map(style_rsi, subset=['RSI (14)']) \
                    .format({
                        "% Change": "{:+.2f}%", 
                        "Change": "{:+.2f}",
                        "Price": "{:,.2f}",
                        "RSI (14)": "{:.0f}"
                    }),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=70),
                "Price": st.column_config.NumberColumn("Price", width=55),
                "Change": st.column_config.NumberColumn("Change", width=55),
                "% Change": st.column_config.NumberColumn("% Change", width=65),
                "RSI (14)": st.column_config.NumberColumn("RSI (14)", width=45),
            },
            use_container_width=True,
            height=800,
            hide_index=True
        )
        
        now_th = datetime.now(pytz.timezone('Asia/Bangkok')).strftime("%H:%M")
        st.caption(f"Refreshed: {now_th} | Auto 5m | Decimal 0.00")

show_us_charts_board()
