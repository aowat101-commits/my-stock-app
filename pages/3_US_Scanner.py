import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ (เน้นความเรียบง่ายและตัวหนังสือปกติ)
st.set_page_config(page_title="US Broad Market Monitor", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .time-status {
        background-color: #1e293b; color: #fbbf24; padding: 10px; border-radius: 6px;
        text-align: center; font-size: 13px; margin-bottom: 15px; border: 1px solid #d97706;
    }
    [data-testid="stDataFrame"] th { 
        background-color: #0f172a !important; 
        color: #fbbf24 !important; 
        text-align: center !important; 
        font-size: 11px !important;
        font-weight: normal !important;
    }
    [data-testid="stDataFrame"] td { 
        font-size: 11px !important; 
        text-align: center !important; 
        font-weight: normal !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้นสหรัฐฯ แบบครอบคลุม (Tech, AI, Energy, Crypto, Index ETF)
us_full_list = [
    # กลุ่มที่คุณวิเคราะห์ (Quantum & AI)
    'IONQ', 'IREN', 'EOSE', 'SMX', 'ONDS', 'PLTR', 'SOUN', 'BBAI', 'RGTI',
    # กลุ่ม Semiconductor (ชิปเซ็ต)
    'NVDA', 'AMD', 'TSM', 'INTC', 'ARM', 'MU', 'AVGO', 'ASML',
    # กลุ่ม Big Tech (Magnificent 7)
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA',
    # กลุ่ม Crypto Mining & Blockchain
    'MARA', 'RIOT', 'CLSK', 'HIVE', 'COIN', 'MSTR',
    # กลุ่มพลังงานและอุตสาหกรรม
    'XOM', 'CVX', 'CAT', 'GE', 'BA',
    # ดัชนีและ ETF สำคัญ
    'SPY', 'QQQ', 'SOXX', 'BITO', 'BTC-USD', 'ETH-USD'
]

# 3. ฟังก์ชันคำนวณ HMA 30
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

# 4. ฟังก์ชันค้นหาสัญญาณล่าสุดพร้อม % Change
def get_us_signal_broad(df, ticker):
    if len(df) < 35: return None
    tz_th = pytz.timezone('Asia/Bangkok')
    
    df['hma'] = get_hma(df['Close'], 30)
    df['trend'] = np.where(df['hma'] > df['hma'].shift(1), "UP", "DOWN")
    df['is_switch'] = df['trend'] != df['trend'].shift(1)
    
    switches = df[df['is_switch'] == True].copy()
    if not switches.empty:
        last_sig = switches.iloc[-1]
        
        # คำนวณ % Change เทียบแท่งก่อนหน้า
        prev_close = df.shift(1).loc[last_sig.name, 'Close']
        pct_change = ((last_sig['Close'] - prev_close) / prev_close) * 100 if prev_close != 0 else 0
        
        actual_time_th = last_sig.name.astimezone(tz_th)
        
        return {
            "Ticker": ticker,
            "Price": last_sig['Close'],
            "% Chg": pct_change,
            "Signal": "🚀 BUY" if last_sig['trend'] == "UP" else "🔻 SELL",
            "เวลาไทย": actual_time_th.strftime("%H:%M:%S"),
            "วันที่": actual_time_th.strftime("%d/%m"),
            "raw_time": last_sig.name 
        }
    return None

# 5. ส่วนหัวและปุ่มรีเฟรช
st.subheader("🇺🇸 US Broad Market Scanner (Thai Time)")

if st.button("🔄 Refresh All US Market", use_container_width=True):
    st.rerun()

# 6. Dashboard Runtime
@st.fragment(run_every="5m")
def us_broad_dashboard():
    now_th = datetime.now(pytz.timezone('Asia/Bangkok')).strftime("%H:%M:%S")
    st.markdown(f'<div class="time-status">🇹🇭 Thai Time: {now_th} | สแกนหุ้น US แบบครอบคลุม 40+ ตัว</div>', unsafe_allow_html=True)
    
    results = []
    bar = st.progress(0)
    
    total = len(us_full_list)
    for i, t in enumerate(us_full_list):
        try:
            stock = yf.Ticker(t)
            # ดึงข้อมูลย้อนหลัง 20 วัน เพื่อให้คำนวณ HMA ได้แม่นยำ
            hist = stock.history(period="20d", interval="1h")
            if not hist.empty:
                res = get_us_signal_broad(hist, t)
                if res: results.append(res)
        except: continue
        bar.progress((i + 1) / total)
    
    bar.empty()

    if results:
        # เรียงตามความสดใหม่ของสัญญาณ
        df = pd.DataFrame(results).sort_values(by="raw_time", ascending=False)
        
        def style_row(row):
            color = '#10b981' if "BUY" in row['Signal'] else '#ef4444'
            return [f'color: {color}; font-weight: normal;'] * len(row)

        st.dataframe(
            df.drop(columns=['raw_time']).style.apply(style_row, axis=1)
            .format({"Price": "{:,.2f}", "% Chg": "{:+.2f}%"}),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=70),
                "Price": st.column_config.NumberColumn("Price", width=65),
                "% Chg": st.column_config.NumberColumn("% Chg", width=65),
                "Signal": st.column_config.TextColumn("Signal", width=75),
                "เวลาไทย": st.column_config.TextColumn("เวลาไทย", width=80),
                "วันที่": st.column_config.TextColumn("วันที่", width=55),
            },
            use_container_width=True, height=750, hide_index=True
        )

us_broad_dashboard()
