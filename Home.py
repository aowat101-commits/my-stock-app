import streamlit as st

# 1. ตั้งค่าหน้าจอ: ล้างค่า page_icon ให้เป็นค่าว่างที่สุด
st.set_page_config(
    layout="wide", 
    page_title=" ", 
    page_icon=" "  # ใส่ช่องว่างเพื่อทับค่าเดิมของระบบ
) 

st.markdown("""
    <style>
    /* 1. มาตรการขั้นเด็ดขาด: ซ่อน Header และรูปภาพทุกชนิดที่อยู่ใน Header */
    [data-testid="stHeader"], 
    header, 
    .stAppHeader {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    
    /* 2. บล็อกรูปภาพหรือไอคอนแปลกปลอมที่อาจจะหลุดมาที่มุมซ้ายบน */
    header img, 
    [data-testid="stHeader"] img,
    .st-emotion-cache-1avcm0n img {
        display: none !important;
    }

    /* 3. ดันเนื้อหา (Banner) ขึ้นไปทับพื้นที่ที่เคยมีไอคอนจนมิด */
    .main .block-container {
        padding-top: 0rem !important;
        margin-top: -100px !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# ส่วนเนื้อหาอื่นๆ ของคุณ...
st.image("https://images.unsplash.com/photo-1611974714851-eb605161882c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", use_container_width=True)
st.markdown("<h1 style='text-align: center; color: #fbbf24;'>📊 HOME</h1>", unsafe_allow_html=True)
