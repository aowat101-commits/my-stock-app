import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าหน้าจอ (ซ่อน UI ส่วนเกินเพื่อให้หน้าจอนิ่ง)
st.set_page_config(page_title="SET100 Full Board", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น SET100 ครบทั้งหมด
SET100_TICKERS = [
    'AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK',
    'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK',
    'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK',
    'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK',
    'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK',
    'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KEX.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK',
    'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK',
    'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SABUY.BK', 'SAWAD.BK',
    'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK',
    'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK',
    'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK'
]

st.title("📊 SET100 Full Live Board (RSI Monitor)")

# --- Sidebar ---
st.sidebar.header("⚙️ ระบบอัปเดต")
st.sidebar.info("⏱️ รีเฟรชอัตโนมัติ: ทุก 30 นาที")
if st.sidebar.button("🔄 อัปเดตข้อมูลทันที"):
    st.rerun()

# 3. ฟังก์ชันดึงข้อมูลและคำนวณ
@st.cache_data(ttl=1800) # เก็บ Cache 30 นาที
def get_set100_data():
    data_list = []
    for t in SET100_TICKERS:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="30d")
            if not hist.empty and len(hist) >= 15:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                diff = curr - prev
                pct = (diff / prev) * 100
                
                delta = hist['Close'].diff()
                up = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
                down = -delta.clip(upper=0).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (up / down))) if down != 0 else 100

                data_list.append({
                    "Ticker": t.replace('.BK', ''),
                    "ราคาปิดก่อนหน้า": round(prev, 2),
                    "ราคาล่าสุด": round(curr, 2),
                    "เปลี่ยนแปลง": round(diff, 2),
                    "% เปลี่ยนแปลง": round(pct, 2),
                    "RSI (14)": round(rsi, 2)
                })
        except: continue
    return pd.DataFrame(data_list)

# 4. ฟังก์ชันจัดการสี (RSI < 30 เป็นสีแดง)
def style_rsi(val):
    color = 'red' if val < 30 else 'white'
    return f'color: {color}; font-weight: bold;' if val < 30 else f'color: {color};'

# 5. การแสดงผล (ล็อคเวลา 30 นาทีด้วย Fragment)
@st.fragment(run_every="30m")
def show_full_board():
    df = get_set100_data()
    
    if not df.empty:
        # ใส่สัญลักษณ์ ⚠️ หน้า Ticker ที่ RSI < 30
        df['Ticker'] = df.apply(lambda x: f"⚠️ {x['Ticker']}" if x['RSI (14)'] < 30 else x['Ticker'], axis=1)
        
        # แสดงผลและจัดการ Style (เปลี่ยน applymap เป็น map เพื่อแก้ Error)
        st.dataframe(
            df.style.map(style_rsi, subset=['RSI (14)'])
                    .format({"% เปลี่ยนแปลง": "{:+.2f}%", "เปลี่ยนแปลง": "{:+.2f}"}),
            use_container_width=True,
            height=800,
            hide_index=True
        )
        
        st.caption(f"อัปเดตเมื่อ: {datetime.now().strftime('%H:%M:%S')} | รีเฟรชทุก 30 นาที")
    else:
        st.warning("กำลังดึงข้อมูลหุ้น... โปรดรอสักครู่")

show_full_board()
