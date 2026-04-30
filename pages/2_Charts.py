import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าหน้าจอและ CSS (เน้นบีบระยะห่างให้เหลือน้อยที่สุด)
st.set_page_config(page_title="SET100 Monitor", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    
    /* บีบขนาดตัวอักษรและระยะห่างเซลล์ให้เล็กที่สุดสำหรับมือถือ */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        font-size: 11px !important;
        padding: 2px 4px !important;
        text-align: center !important;
    }
    
    /* จัดหัวตารางให้หนาและอยู่ตรงกลาง */
    [data-testid="stDataFrame"] th {
        font-weight: bold !important;
        white-space: nowrap !important; /* ห้ามตัดบรรทัดที่หัวข้อ */
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น SET100 ครบทั้งหมด
tickers = [
    'AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK',
    'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK',
    'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK',
    'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK',
    'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK',
    'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK',
    'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK',
    'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK',
    'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK',
    'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK',
    'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK'
]

# 3. Sidebar
st.sidebar.header("⚙️ Settings")
if st.sidebar.button("🔄 Force Refresh"):
    st.rerun()

# 4. ฟังก์ชันดึงข้อมูล (Cache 30 นาที)
@st.cache_data(ttl=1800)
def get_set100_data():
    data_list = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="30d")
            if not hist.empty and len(hist) >= 15:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff = curr - prev
                pct = ((curr - prev) / prev) * 100 if prev != 0 else 0.0
                
                delta = hist['Close'].diff()
                up = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
                down = -delta.clip(upper=0).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (up / down))) if down != 0 else 100

                data_list.append({
                    "Ticker": t.replace('.BK', ''),
                    "Price": round(curr, 2),
                    "Change": round(diff, 2) if abs(diff) > 0.0001 else 0.0,
                    "% Change": round(pct, 2) if abs(pct) > 0.0001 else 0.0,
                    "RSI (14)": round(rsi, 2)
                })
        except: continue
    return pd.DataFrame(data_list)

# 5. การแสดงผล (ล็อกเวลา 30 นาที)
@st.fragment(run_every="30m")
def show_mobile_optimized_board():
    st.title("📊 SET100 Live")
    df = get_set100_data()
    
    if not df.empty:
        # สไตล์สี (เขียว/แดง/เทา)
        def style_color(val):
            if val > 0: return 'color: #10b981; font-weight: normal;'
            if val < 0: return 'color: #ef4444; font-weight: normal;'
            return 'color: #888888; font-weight: normal;'

        def style_rsi(val):
            if val < 30: return 'color: #ef4444; font-weight: normal;'
            return 'color: #888888; font-weight: normal;'

        def style_ticker_price(row):
            color = '#10b981' if row['Change'] > 0 else '#ef4444' if row['Change'] < 0 else '#888888'
            return [f'color: {color};', f'color: {color};', '', '', '']

        # ใส่ ⚠️ หน้า Ticker
        df_display = df.copy()
        df_display['Ticker'] = df_display.apply(lambda x: f"⚠️{x['Ticker']}" if x['RSI (14)'] < 30 else x['Ticker'], axis=1)

        # แสดงผลตาราง (ชื่อหัวข้อเต็ม)
        st.dataframe(
            df_display.style.apply(style_ticker_price, axis=1, subset=['Ticker', 'Price']) \
                    .map(style_color, subset=['Change', '% Change']) \
                    .map(style_rsi, subset=['RSI (14)']) \
                    .format({
                        "% Change": "{:+.1f}%", 
                        "Change": "{:+.1f}",
                        "Price": "{:,.1f}",
                        "RSI (14)": "{:.0f}"
                    }),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=70),
                "Price": st.column_config.NumberColumn("Price", width=45),
                "Change": st.column_config.NumberColumn("Change", width=45),
                "% Change": st.column_config.NumberColumn("% Change", width=55),
                "RSI (14)": st.column_config.NumberColumn("RSI (14)", width=45),
            },
            use_container_width=True,
            height=800,
            hide_index=True
        )
        
        st.caption(f"Refreshed: {datetime.now().strftime('%H:%M')} | Auto 30m")

show_mobile_optimized_board()
