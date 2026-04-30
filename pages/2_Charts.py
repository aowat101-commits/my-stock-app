import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าหน้าจอ (ซ่อน UI ส่วนเกินเพื่อให้หน้านิ่งที่สุด)
st.set_page_config(page_title="SET100 Premium Monitor", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
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

# 3. Sidebar: ล็อกเวลา 30 นาที และปุ่มกด
st.sidebar.header("⚙️ ระบบอัปเดต")
st.sidebar.info("⏱️ รีเฟรชอัตโนมัติ: **ทุก 30 นาที**")
if st.sidebar.button("🔄 อัปเดตข้อมูลตอนนี้"):
    st.rerun()

# 4. ฟังก์ชันดึงข้อมูล (ดึงข้อมูลจริงจาก Yahoo Finance)
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
                    "ปิดก่อนหน้า": round(prev, 2),
                    "ล่าสุด": round(curr, 2),
                    "เปลี่ยนแปลง": round(diff, 2),
                    "%": round(pct, 2),
                    "RSI (14)": round(rsi, 2)
                })
        except: continue
    return pd.DataFrame(data_list)

# 5. การแสดงผล (ล็อกเวลา 30 นาที)
@st.fragment(run_every="30m")
def show_premium_board():
    st.title("📊 SET100 Full Live Board")
    df = get_set100_data()
    
    if not df.empty:
        # ใส่สัญลักษณ์ ⚠️ หน้า Ticker ที่ RSI < 30
        df['Ticker'] = df.apply(lambda x: f"⚠️ {x['Ticker']}" if x['RSI (14)'] < 30 else x['Ticker'], axis=1)
        
        # ตั้งค่าสี RSI < 30 เป็นสีแดง
        def color_rsi(val):
            color = '#ff4b4b' if val < 30 else 'white'
            return f'color: {color}; font-weight: bold' if val < 30 else f'color: {color}'

        # ใช้ st.dataframe เพื่อให้หัวแถว "กดเรียงลำดับได้"
        st.dataframe(
            df.style.map(color_rsi, subset=['RSI (14)'])
                    .format({"%": "{:+.2f}%", "เปลี่ยนแปลง": "{:+.2f}"}),
            use_container_width=True,
            height=800,
            hide_index=True
        )
        
        st.caption(f"อัปเดตล่าสุด: {datetime.now().strftime('%H:%M:%S')} | รีเฟรชทุก 30 นาที")

show_premium_board()
