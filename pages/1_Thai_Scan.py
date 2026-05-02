import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime
import pytz

# 1. ตั้งค่าหน้าจอและสไตล์ Loft
st.set_page_config(page_title="The Guardian Swing Dashboard", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stHeader"], header, .stAppHeader { display: none !important; }
    .main { background-color: #0f172a; }
    .time-status {
        background-color: #1e293b; color: #10b981; padding: 12px; border-radius: 8px;
        text-align: center; font-size: 14px; margin-bottom: 15px; border: 1px solid #334155;
        font-weight: bold;
    }
    [data-testid="stDataFrame"] th { background-color: #1e293b !important; color: #94a3b8 !important; text-align: center !important; font-size: 12px !important; }
    [data-testid="stDataFrame"] td { font-size: 12px !important; text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น (SET100 + Extra Growth)
set100 = ['AAV.BK', 'ADVANC.BK', 'AMATA.BK', 'AOT.BK', 'AP.BK', 'AWC.BK', 'BA.BK', 'BAM.BK', 'BANPU.BK', 'BBL.BK', 'BCH.BK', 'BCP.BK', 'BCPG.BK', 'BDMS.BK', 'BEM.BK', 'BGRIM.BK', 'BH.BK', 'BJC.BK', 'BLA.BK', 'BPP.BK', 'BTG.BK', 'BTS.BK', 'CBG.BK', 'CENTEL.BK', 'CHG.BK', 'CK.BK', 'CKP.BK', 'COM7.BK', 'CPALL.BK', 'CPF.BK', 'CPN.BK', 'CRC.BK', 'DELTA.BK', 'DOHOME.BK', 'EA.BK', 'EGCO.BK', 'ERW.BK', 'FORTH.BK', 'GLOBAL.BK', 'GPSC.BK', 'GULF.BK', 'GUNKUL.BK', 'HANA.BK', 'HMPRO.BK', 'ICHI.BK', 'INTUCH.BK', 'IRPC.BK', 'ITC.BK', 'IVL.BK', 'JMART.BK', 'JMT.BK', 'KBANK.BK', 'KCE.BK', 'KKP.BK', 'KTB.BK', 'KTC.BK', 'LH.BK', 'M.BK', 'MASTER.BK', 'MBK.BK', 'MC.BK', 'MEGA.BK', 'MINT.BK', 'MTC.BK', 'OR.BK', 'ORI.BK', 'OSP.BK', 'PLANB.BK', 'PRM.BK', 'PSL.BK', 'PTG.BK', 'PTT.BK', 'PTTEP.BK', 'PTTGC.BK', 'QH.BK', 'RATCH.BK', 'RCL.BK', 'SAWAD.BK', 'SCB.BK', 'SCC.BK', 'SCGP.BK', 'SINGER.BK', 'SIRI.BK', 'SJWD.BK', 'SKY.BK', 'SPALI.BK', 'SPRC.BK', 'STA.BK', 'STEC.BK', 'STGT.BK', 'TCAP.BK', 'THANI.BK', 'THG.BK', 'TIDLOR.BK', 'TIPH.BK', 'TISCO.BK', 'TOP.BK', 'TQM.BK', 'TRUE.BK', 'TTB.BK', 'TTW.BK', 'TU.BK', 'VGI.BK', 'WHA.BK', 'WHAUP.BK']
extra_growth = ['TFG.BK', 'JTS.BK', 'SAPPE.BK', 'SISB.BK', 'BE8.BK', 'BBIK.BK', 'SNNP.BK', 'AU.BK', 'DITTO.BK', 'NSL.BK', 'KAMART.BK', 'COCOCO.BK', 'KLINIQ.BK', 'WARRIX.BK', 'SABINA.BK', 'SCCC.BK', 'TASCO.BK', 'MALEE.BK', 'PLUS.BK', 'TKN.BK', 'XO.BK']
full_scan_list = list(set(set100 + extra_growth))

# 3. ฟังก์ชันคำนวณ HMA และ WaveTrend
def get_hma(series, length):
    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    half_length, sqrt_length = int(length / 2), int(np.sqrt(length))
    raw_hma = 2 * wma(series, half_length) - wma(series, length)
    return wma(raw_hma, sqrt_length)

def get_wavetrend(df, n1=10, n2=21):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ta.ema(ap, length=n1)
    d = ta.ema(abs(ap - esa), length=n1)
    ci = (ap - esa) / (0.015 * d)
    tci = ta.ema(ci, length=n2)
    wt1 = tci
    wt2 = ta.sma(wt1, length=4)
    return wt1, wt2

# 4. ฟังก์ชันวิเคราะห์ Guardian Swing Logic
def analyze_guardian(ticker):
    try:
        df = yf.download(ticker, period="20d", interval="1h", progress=False)
        if len(df) < 40: return None

        # คำนวณ Indicators
        df['ema8'] = ta.ema(df['Close'], length=8)
        df['ema20'] = ta.ema(df['Close'], length=20)
        df['hma30'] = get_hma(df['Close'], 30)
        df['vma5'] = ta.sma(df['Volume'], length=5)
        wt1, wt2 = get_wavetrend(df)
        df['wt1'], df['wt2'] = wt1, wt2

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # เงื่อนไข Trend & Momentum
        is_above_ema = last['Close'] > last['ema8'] and last['Close'] > last['ema20']
        is_hull_green = last['hma30'] > prev['hma30']
        
        # เงื่อนไข WaveTrend (Cross Up Below -53)
        wt_cross_up = prev['wt1'] < prev['wt2'] and last['wt1'] > last['wt2']
        wt_oversold = last['wt1'] < -53
        
        # เงื่อนไข Volume (มากกว่า VMA5 1.5 เท่า)
        vol_confirmation = last['Volume'] > (last['vma5'] * 1.5)

        # ตัดสินใจ Signal
        signal = "WAIT"
        action_note = "-"
        
        if is_above_ema and is_hull_green and wt_cross_up and wt_oversold and vol_confirmation:
            signal = "🚀 BUY"
            action_note = "Strong Volume Confirmation"
        elif last['wt1'] > 53 and prev['wt1'] > prev['wt2'] and last['wt1'] < last['wt2']:
            signal = "💰 TAKE PROFIT"
            action_note = "WT Red Cross Over 53"
        elif last['Close'] < last['ema20'] or last['hma30'] < prev['hma30']:
            signal = "🔻 EXIT"
            action_note = "Protect Profit/Capital"

        return {
            "Ticker": ticker.replace('.BK', ''),
            "Price": last['Close'],
            "Signal": signal,
            "Note": action_note,
            "WT": round(last['wt1'], 2),
            "Vol/VMA5": round(last['Volume'] / last['vma5'], 2)
        }
    except: return None

# 5. UI และ Dashboard
st.subheader("🛡️ The Guardian Swing: High Confirmation Scan")

@st.fragment(run_every="10m")
def guardian_runtime():
    tz = pytz.timezone('Asia/Bangkok')
    st.markdown(f'<div class="time-status">🕒 Last Sync: {datetime.now(tz).strftime("%H:%M:%S")} | Logic: EMA + Hull + WT + Vol</div>', unsafe_allow_html=True)
    
    results = []
    bar = st.progress(0, text="กำลังวิเคราะห์หุ้นตามสูตร The Guardian Swing...")
    
    total = len(full_scan_list)
    for i, t in enumerate(full_scan_list):
        res = analyze_guardian(t)
        if res: results.append(res)
        bar.progress((i + 1) / total)
    bar.empty()

    if results:
        df = pd.DataFrame(results)
        # แสดงเฉพาะหุ้นที่มีสัญญาณ BUY, EXIT หรือ TAKE PROFIT
        active_df = df[df['Signal'] != "WAIT"].sort_values(by="Signal")
        
        if active_df.empty:
            st.info("🔎 ขณะนี้ยังไม่มีหุ้นที่ครบเงื่อนไข Strong Buy")
        else:
            def style_signal(row):
                if "BUY" in row['Signal']: color = '#10b981'
                elif "EXIT" in row['Signal']: color = '#ef4444'
                else: color = '#fbbf24'
                return [f'color: {color}; font-weight: bold;'] * len(row)

            st.dataframe(
                active_df.style.apply(style_signal, axis=1).format({"Price": "{:,.2f}"}),
                column_config={
                    "Ticker": st.column_config.TextColumn("Ticker", width=80),
                    "Price": st.column_config.NumberColumn("Price", width=70),
                    "Signal": st.column_config.TextColumn("Action Signal", width=120),
                    "Note": st.column_config.TextColumn("Reason", width=180),
                    "WT": st.column_config.NumberColumn("WT Value", width=70),
                    "Vol/VMA5": st.column_config.NumberColumn("Vol Force", width=80),
                },
                use_container_width=True, height=500, hide_index=True
            )

guardian_runtime()
