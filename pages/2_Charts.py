import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าหน้าจอและซ่อน UI ส่วนเกิน
st.set_page_config(page_title="SET100 Premium Monitor", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    .stDataFrame {border: 1px solid #1e293b; border-radius: 10px;}
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

# 4. ฟังก์ชันดึงข้อมูล
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
                pct = (diff / prev) * 100
                delta = hist['Close'].diff()
                up = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
                down = -delta.clip(upper=0).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (up / down))) if down != 0 else 100

                data_list.append({
                    "Ticker": t.replace('.BK', ''),
                    "Price": round(curr, 2),
                    "Change": round(diff, 2),
                    "% Chg": round(pct, 2),
                    "RSI (14)": round(rsi, 2)
                })
        except: continue
    return pd.DataFrame(data_list)

# 5. การแสดงผล (Fragment ล็อกเวลา 30 นาที)
@st.fragment(run_every="30m")
def show_enhanced_board():
    st.title("📊 SET100 Premium Monitor")
    df = get_set100_data()
    
    if not df.empty:
        # ตกแต่ง Ticker ที่ RSI ต่ำ
        df['Ticker'] = df.apply(lambda x: f"⚠️ {x['Ticker']}" if x['RSI (14)'] < 30 else x['Ticker'], axis=1)
        
        # ฟังก์ชันแต่งสี RSI
        def style_rsi(val):
            if val < 30:
                return 'background-color: #4c0519; color: #ff4b4b; font-weight: bold'
            return ''

        # ฟังก์ชันแต่งสี % Chg (บวกเขียว ลบแดง)
        def style_chg(val):
            color = '#10b981' if val > 0 else '#ef4444' if val < 0 else 'white'
            return f'color: {color}'

        # แสดงผลตารางแบบ High-End
        st.dataframe(
            df.style.map(style_rsi, subset=['RSI (14)']) \
                    .map(style_chg, subset=['Change', '% Chg']) \
                    .bar(subset=['% Chg'], color=['#440106', '#013220'], align='mid') \
                    .format({"% Chg": "{:+.2f}%", "Change": "{:+.2f}"}),
            use_container_width=True,
            height=750,
            hide_index=True
        )
        
        st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')} | Auto-refresh every 30 mins")

show_enhanced_board()
