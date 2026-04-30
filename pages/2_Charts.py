import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าหน้าจอและ CSS สำหรับ Mobile Optimized
st.set_page_config(page_title="SET100 Mobile", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    
    /* ปรับขนาดตัวอักษรตารางให้เล็กลงเพื่อมือถือ */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        font-size: 12px !important;
        text-align: center !important;
    }
    
    /* จัดหัวตารางให้หนาและอยู่ตรงกลาง */
    [data-testid="stDataFrame"] th {
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น SET100 ทั้งหมด
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
st.sidebar.header("⚙️ Market Settings")
st.sidebar.markdown("⏱️ รีเฟรชอัตโนมัติ: **ทุก 30 นาที**")
if st.sidebar.button("🔄 Force Refresh Now"):
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
                    "Chg": round(diff, 2) if abs(diff) > 0.0001 else 0.00,
                    "%": round(pct, 2) if abs(pct) > 0.0001 else 0.00,
                    "RSI": round(rsi, 2)
                })
        except: continue
    return pd.DataFrame(data_list)

# 5. การแสดงผล (Fragment ล็อกเวลา 30 นาที)
@st.fragment(run_every="30m")
def show_mobile_board():
    st.title("📊 SET100 Live")
    df = get_set100_data()
    
    if not df.empty:
        # สไตล์ตัวเลข (บวก=เขียว, ลบ=แดง, ศูนย์=เทาอ่อน)
        def style_logic(val):
            if val > 0: return 'color: #10b981; font-weight: normal; text-align: center;'
            if val < 0: return 'color: #ef4444; font-weight: normal; text-align: center;'
            return 'color: #888888; font-weight: normal; text-align: center;'

        # สไตล์ RSI และ Ticker
        def style_rsi_only(val):
            if val < 30: return 'color: #ef4444; font-weight: normal; text-align: center;'
            return 'color: #888888; font-weight: normal; text-align: center;'

        def apply_row_styles(row):
            color = '#10b981' if row['Chg'] > 0 else '#ef4444' if row['Chg'] < 0 else '#888888'
            style = f'color: {color}; font-weight: normal; text-align: center;'
            return [style, style, '', '', '']

        # จัดการเครื่องหมายเตือน RSI
        df_display = df.copy()
        df_display['Ticker'] = df_display.apply(lambda x: f"⚠️{x['Ticker']}" if x['RSI'] < 30 else x['Ticker'], axis=1)

        # แสดงผลตารางแบบบีบคอลัมน์ให้เล็กที่สุด
        st.dataframe(
            df_display.style.apply(apply_row_styles, axis=1) \
                    .map(style_logic, subset=['Chg', '%']) \
                    .map(style_rsi_only, subset=['RSI']) \
                    .format({
                        "%": "{:+.1f}%", 
                        "Chg": "{:+.1f}",
                        "Price": "{:,.1f}",
                        "RSI": "{:.0f}"
                    }),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width=60),
                "Price": st.column_config.NumberColumn("Px", width=40),
                "Chg": st.column_config.NumberColumn("Chg", width=40),
                "%": st.column_config.NumberColumn("%", width=40),
                "RSI": st.column_config.NumberColumn("RSI", width=35),
            },
            use_container_width=True,
            height=800,
            hide_index=True
        )
        
        st.caption(f"Update: {datetime.now().strftime('%H:%M')} | Auto 30m")

show_mobile_board()
