import streamlit as st

# 1. ตั้งค่าหน้าจอ (ปิดไอคอนและชื่อเพื่อความคลีน)
st.set_page_config(layout="wide", page_title=" ", page_icon=" ") 

st.markdown("""
    <style>
    /* ซ่อน Header และไอคอนที่มุมซ้ายแบบเด็ดขาด */
    [data-testid="stHeader"], header {
        display: none !important;
    }
    
    /* ดันเนื้อหาขึ้นไปให้สุดหน้าจอ */
    .main .block-container {
        padding-top: 0rem !important;
        margin-top: -50px !important; 
    }

    .main { background-color: #ffffff; } /* หรือใช้สี #0f172a ตามแบบเดิม */
    
    /* แก้ไขตำแหน่ง Header HOME */
    .custom-header {
        text-align: center;
        padding: 40px;
        background-color: #f8fafc;
        border-bottom: 2px solid #fbbf24;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. ส่วน Banner (ใช้รูปใหม่ที่เสถียร หรือถ้าไม่ต้องการรูปให้ลบบรรทัดนี้ออกครับ)
# ผมเปลี่ยนลิงก์รูปภาพให้ใหม่ที่โหลดติดชัวร์ครับ
st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80", use_container_width=True)

# 3. ชื่อหน้าแบบคลีนๆ
st.markdown("<h1 style='text-align: center; color: #fbbf24;'>📊 HOME</h1>", unsafe_allow_html=True)

# ส่วนโค้ดอื่นๆ (Market Status / Navigation) ของคุณใช้ของเดิมได้เลยครับ
