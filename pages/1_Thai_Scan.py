import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
import pytz

# --- 1. ฟังก์ชันส่งการแจ้งเตือนเข้า Telegram ---
def send_telegram_msg(message):
    token = "ใส่_BOT_TOKEN_ของคุณที่นี่"
    chat_id = "ใส่_CHAT_ID_ของคุณที่นี่"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        st.error(f"Error sending Telegram: {e}")

# --- 2. ฟังก์ชันคำนวณ WaveTrend (WT_LB: 9, 12) ---
def calculate_wavetrend(df, ch_len=10, avg_len=21):
    ap = (df['high'] + df['low'] + df['close']) / 3
    esa = ta.ema(ap, length=ch_len)
    d = ta.ema(abs(ap - esa), length=ch_len)
    ci = (ap - esa) / (0.015 * d)
    tci = ta.ema(ci, length=avg_len)
    wt1 = tci
    wt2 = ta.sma(wt1, length=4)
    return wt1, wt2

# --- 3. ฟังก์ชันหลักในการสแกนและตรวจสอบเงื่อนไข ---
def scan_guardian_swing(df, ticker):
    # คำนวณอินดิเคเตอร์พื้นฐาน
    df['ema8'] = ta.ema(df['close'], length=8)
    df['ema20'] = ta.ema(df['close'], length=20)
    df['hull'] = ta.hma(df['close'], length=55)
    df['vma5'] = df['volume'].rolling(window=5).mean()
    df['wt1'], df['wt2'] = calculate_wavetrend(df, 9, 12)
    
    # ดึงค่าล่าสุดมาเช็ค
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # --- เงื่อนไขการซื้อ (Buy Alert) ---
    # 1. WT ตัดขึ้นต่ำกว่า -53
    wt_cross_up = (prev['wt1'] < prev['wt2']) and (curr['wt1'] > curr['wt2'])
    wt_low_zone = curr['wt1'] < -53
    # 2. ราคาอยู่เหนือ EMA 8 และ 20
    above_ema = (curr['close'] > curr['ema8']) and (curr['close'] > curr['ema20'])
    # 3. Hull Suite สีเขียว (ราคาปัจจุบัน > Hull)
    hull_green = curr['close'] > curr['hull']
    # 4. Volume มากกว่า VMA5 อย่างน้อย 1.5 เท่า
    vol_ratio = curr['volume'] / curr['vma5'] if curr['vma5'] > 0 else 0
    vol_confirm = vol_ratio >= 1.5

    if wt_cross_up and wt_low_zone and above_ema and hull_green and vol_confirm:
        msg = (f"🚀 *[The Guardian Swing] - สัญญาณซื้อ*\n"
               f"📈 *หุ้น:* {ticker}\n"
               f"💰 *ราคา:* {curr['close']:.2f}\n"
               f"🔥 *Volume:* {vol_ratio:.2f}x (แรงกว่าค่าเฉลี่ย)\n"
               f"✅ เงื่อนไขครบ: WT/EMA/Hull/Vol")
        send_telegram_msg(msg)
        return "BUY"

    # --- เงื่อนไขการขาย (Sell Alert) ---
    # 1. Profit Take: WT ตัดลงในโซนสูง (> 53)
    wt_cross_down = (prev['wt1'] > prev['wt2']) and (curr['wt1'] < curr['wt2'])
    wt_high_zone = curr['wt1'] > 53
    # 2. Stop Loss: หลุด EMA 20 หรือ Hull เปลี่ยนสีแดง
    below_ema20 = curr['close'] < curr['ema20']
    hull_red = curr['close'] < curr['hull']

    if (wt_cross_down and wt_high_zone) or below_ema20 or hull_red:
        reason = ""
        if wt_cross_down: reason = "WT ตัดลงในโซนสูง (Take Profit)"
        elif below_ema20: reason = "ราคาหลุดเส้น EMA 20"
        elif hull_red: reason = "Hull Suite เปลี่ยนเป็นสีแดง"
        
        msg = (f"⚠️ *[The Guardian Swing] - สัญญาณขาย*\n"
               f"📉 *หุ้น:* {ticker}\n"
               f"💰 *ราคา:* {curr['close']:.2f}\n"
               f"📢 *เหตุผล:* {reason}\n"
               f"👉 *พิจารณาขายเพื่อลดความเสี่ยง*")
        send_telegram_msg(msg)
        return "SELL"
    
    return "HOLD"

# --- 4. ส่วนการแสดงผลบน Streamlit ---
st.title("🛡️ The Guardian Swing Monitor")
# (ใส่โค้ดดึงข้อมูลหุ้นของคุณมิลค์ตรงนี้ เช่น yfinance หรือ API อื่นๆ)
# จากนั้นเรียกใช้งาน:
# result = scan_guardian_swing(df_data, ticker_name)
