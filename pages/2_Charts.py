import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าหน้าจอและ CSS สไตล์พรีเมียม
st.set_page_config(page_title="SET100 Monitor", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    
    /* จัดหัวตารางให้หนาและอยู่ตรงกลาง */
    [data-testid="stDataFrame"] th {
        text-align: center !important;
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

# 3. Sidebar: รีเฟรชทุก 30 นาที
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
                    "Change": round(diff, 2) if abs(diff) > 0.0001 else 0.00,
                    "% Chg": round(pct, 2) if abs(pct) > 0.0001 else 0.00,
                    "RSI (14)": round(rsi, 2)
                })
        except: continue
    return pd.DataFrame(data_list)

# 5. การแสดงผล (Fragment ล็อกเวลา 30 นาที)
@st.fragment(run_every="30m")
def show_final_board():
    st.title("📊 SET100 Live Monitor")
    df = get_set100_data()
    
    if not df.empty:
        # สไตล์ตัวเลข (บวก=เขียว, ลบ=แดง, ศูนย์=ดำ) และจัดกลาง
        def style_logic(val):
            if val > 0: return 'color: #10b981; font-weight: 700; text-align: center;'
            if val < 0: return 'color: #ef4444; font-weight: 700; text-align: center;'
            return 'color: #000000; font-weight: 700; text-align: center;'

        # สไตล์ชื่อหุ้นและ RSI
        def style_row(row):
            color = '#10b981' if row['Change'] > 0 else '#ef4444' if row['Change'] < 0 else '#000000'
            rsi_color = '#ef4444' if row['RSI (14)'] < 30 else 'white'
            return [
                f'color: {color}; font-weight: 600; text-align: center;', # Ticker
                'text-align: center; font-weight: 600;', # Price
                '', # Change (Managed by map)
                '', # % Chg (Managed by map)
                f'color: {rsi_color}; font-weight: 700; text-align: center;' # RSI
            ]

        # เพิ่มเครื่องหมายเตือน RSI
        df['Ticker'] = df.apply(lambda x: f"⚠️ {x['Ticker']}" if x['RSI (14)'] < 30 else x['Ticker'], axis=1)

        # แสดงผลตารางพร้อมตั้งค่าความกว้างคอลัมน์
        st.dataframe(
            df.style.apply(style_row, axis=1)
                    .map(style_logic, subset=['Change', '% Chg'])
                    .format({
                        "% Chg": "{:+.2f}%", 
                        "Change": "{:+.2f}",
                        "Price": "{:,.2f}",
                        "RSI (14)": "{:.2f}"
                    }),
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width="medium"),
                "Price": st.column_config.NumberColumn("Price", width="small"),
                "Change": st.column_config.NumberColumn("Change", width="small"),
                "% Chg": st.column_config.NumberColumn("% Chg", width="small"),
                "RSI (14)": st.column_config.NumberColumn("RSI (14)", width="small"),
            },
            use_container_width=True,
            height=800,
            hide_index=True
        )
        
        st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')} | Auto-refresh every 30 mins")

show_final_board()
