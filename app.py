import streamlit as st

st.set_page_config(page_title="Stock Scanner Home", layout="wide")

st.title("🚀 Stock Analysis Dashboard")
st.write("ยินดีต้อนรับสู่ระบบสแกนหุ้นอัตโนมัติด้วยสัญญาณ HMA 30")

# แสดง Metric สรุปภาพรวม
c1, c2, c3 = st.columns(3)
c1.metric("Market Status", "OPEN 🟢")
c2.metric("Signals Found Today", "12 🔥")
c3.metric("Last Update", "15:00")

st.info("💡 เลือกเมนูด้านซ้ายเพื่อเริ่มสแกนหุ้นหรือดูรายละเอียดกราฟ")