import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="Market Intelligence Dashboard", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    .main { background-color: #0f172a; }
    .time-status {
        background-color: #1e293b; color: #fbbf24; padding: 10px; border-radius: 6px;
        text-align: center; font-size: 14px; margin-bottom: 15px; border: 1px solid #334155;
        font-weight: bold;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 12px !important; }
    [data-testid="stDataFrame"] td { font-size: 13px !important; text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. ฟังก์ชันคำนวณ HMA (Hull Moving Average) สำหรับ Hull Suite
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 3. ดึงรายชื่อหุ้น (ลำดับความสำคัญ: Session State > Full Scan List)
if 'thai_watchlist' in st.session_state and st.session_state.thai_watchlist:
    # เพิ่ม .BK ให้อัตโนมัติถ้ายังไม่มี
    full_scan_list = [t if t.endswith('.BK') else f"{t}.BK" for t in st.session_state.thai_watchlist]
else:
    # ค่าเริ่มต้นถ้าหน้า Chart ยังไม่ได้ตั้งค่า
    full_scan_list = ['PTT.BK', 'CPALL.BK', 'AOT.BK', 'ADVANC.BK', 'KBANK.BK', 'DELTA.BK', 'GULF.BK']

# 4. ฟังก์ชันวิเคราะห์ข้อมูลเชิงลึก (HMA + RSI)
def get_stock_analysis(ticker):
    try:
        # ดึงข้อมูล 1 ชั่วโมง ย้อนหลัง 10 วัน (เพื่อให้ได้แท่งเทียนเพียงพอต่อ HMA 30)
        df = yf.download(ticker, period="10d", interval="1h", progress=False)
        if len(df) < 35: return None
        
        tz = pytz.timezone('Asia/Bangkok')
        
        # คำนวณ HMA 30 (Hull Suite)
        df['hma'] = get_hma(df['Close'], 30)
        df['trend'] = np.where(df['hma'] > df['hma'].shift(1), "UP", "DOWN")
        
        # คำนวณ RSI 14 (High Precision)
        df['rsi'] = ta.rsi(df['Close'], length=14)
        
        last_sig = df.iloc[-1]
        prev_sig = df.iloc[-2]
        
        # ตรวจสอบจุดเปลี่ยนสี (Signal Switch)
        is_switch = df['trend'].iloc[-1] != df['trend'].iloc[-2]
        actual_time = last_sig.name.astimezone(tz)
        
        return {
            "Ticker": ticker.replace('.BK', ''),
            "Price": last_sig['Close'],
            "Signal": "🚀 Buy (Green)" if last_sig['trend'] == "UP" else "🔻 Sell (Red)",
            "Status": "✨ New Entry" if is_switch else "Holding",
            "RSI (14)": last_sig['rsi'],
            "เวลาล่าสุด": actual_time.strftime("%H:%M"),
            "raw_time": actual_time
        }
    except: return None

# 5. UI ส่วนหัว
st.subheader("🛰️ Market Intelligence Dashboard")

# แบ่งคอลัมน์ปุ่ม
c1, c2 = st.columns([1, 4])
with c1:
    if st.button("🔄 Manual Refresh", use_container_width=True):
        st.rerun()

# 6. ส่วนประมวลผลหลัก (Fragment เพื่อประหยัดทรัพยากร)
@st.fragment(run_every="5m") # อัปเดตทุก 5 นาที
def scan_runtime():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Last Sync: {datetime.now(tz).strftime("%H:%M:%S")} | Watching {len(full_scan_list)} Tickers</div>', unsafe_allow_html=True)
    
    results = []
    bar = st.progress(0, text="กำลังวิเคราะห์เทรนด์ Hull Suite และ RSI...")
    
    total = len(full_scan_list)
    for i, t in enumerate(full_scan_list):
        res = get_stock_analysis(t)
        if res: results.append(res)
        bar.progress((i + 1) / total)
    
    bar.empty()

    if results:
        df_result = pd.DataFrame(results).sort_values(by="raw_time", ascending=False)
        
        # ฟังก์ชันจัดสีตามสัญญาณ
        def style_signal(row):
            color = '#10b981' if "Buy" in row['Signal'] else '#ef4444'
            return [f'color: {color}; font-weight: bold;'] * len(row)

        st.dataframe(
            df_result.drop(columns=['raw_time']).style.apply(style_signal, axis=1)
            .format({"Price": "{:,.2f}", "RSI (14)": "{:,.2f}"}),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=80),
                "Price": st.column_config.NumberColumn("Price", width=70),
                "Signal": st.column_config.TextColumn("Hull Trend", width=100),
                "Status": st.column_config.TextColumn("Status", width=90),
                "RSI (14)": st.column_config.ProgressColumn("RSI", width=100, min_value=0, max_value=100, format="%.2f"),
                "เวลาล่าสุด": st.column_config.TextColumn("Last Update", width=80),
            },
            use_container_width=True, height=600, hide_index=True
        )
    else:
        st.warning("⚠️ ไม่พบข้อมูลหุ้นในลิสต์ของคุณมิลค์ กรุณาเพิ่มหุ้นในหน้า Charts ก่อนครับ")

# เรียกใช้งาน Runtime
scan_runtime()

st.write("---")
st.caption("Por Piang Electric Plus Co., Ltd. | ระบบสแกนเนอร์อ้างอิงเงื่อนไข Hull Suite 30 + RSI 14")
