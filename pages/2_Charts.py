import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. ตั้งค่าหน้าจอและสไตล์ Dark Premium (ซ่อนขีดวิ่งสีฟ้า)
st.set_page_config(page_title="SET100 Premium Board", layout="wide")

st.markdown("""
    <style>
    [data-testid="stStatusWidget"] {display: none !important;}
    .stSpinner {display: none !important;}
    .main { background-color: #050a14; }
    
    .custom-table {
        width: 100%; border-collapse: collapse; color: white;
        background-color: #0b111e; border-radius: 10px; overflow: hidden;
    }
    .custom-table th {
        background-color: #161e2e; color: #94a3b8; text-align: left;
        padding: 15px; font-size: 14px; border-bottom: 2px solid #1e293b;
        cursor: pointer; /* ทำให้รู้ว่ากดเรียงได้ */
    }
    .custom-table th:hover { background-color: #1e293b; }
    .custom-table td { padding: 15px; border-bottom: 1px solid #1e293b; font-size: 16px; }
    .pos { color: #10b981; font-weight: bold; }
    .neg { color: #ef4444; font-weight: bold; }
    .rsi-alert { color: #ff4b4b; font-weight: bold; } /* สีแดงสำหรับ RSI ต่ำ */
    </style>
    
    <script>
    function sortTable(n) {
      var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
      table = document.querySelector(".custom-table");
      switching = true;
      dir = "asc"; 
      while (switching) {
        switching = false;
        rows = table.rows;
        for (i = 1; i < (rows.length - 1); i++) {
          shouldSwitch = false;
          x = rows[i].getElementsByTagName("TD")[n];
          y = rows[i + 1].getElementsByTagName("TD")[n];
          var xContent = x.innerText.replace(/[^0-9.-]+/g,"");
          var yContent = y.innerText.replace(/[^0-9.-]+/g,"");
          if (isNaN(parseFloat(xContent))) {
              xContent = x.innerText.toLowerCase();
              yContent = y.innerText.toLowerCase();
          } else {
              xContent = parseFloat(xContent);
              yContent = parseFloat(yContent);
          }
          if (dir == "asc") {
            if (xContent > yContent) { shouldSwitch = true; break; }
          } else if (dir == "desc") {
            if (xContent < yContent) { shouldSwitch = true; break; }
          }
        }
        if (shouldSwitch) {
          rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
          switching = true;
          switchcount ++;      
        } else {
          if (switchcount == 0 && dir == "asc") {
            dir = "desc";
            switching = true;
          }
        }
      }
    }
    </script>
    """, unsafe_allow_html=True)

# 2. รายชื่อหุ้น SET100 ครบทั้งหมด
tickers = [
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

# 3. Sidebar: ล็อกรีเฟรช 30 นาที และปุ่มกด
st.sidebar.header("⚙️ ระบบอัปเดต")
st.sidebar.write("⏱️ รีเฟรชอัตโนมัติ: **ทุก 30 นาที**")
if st.sidebar.button("🔄 อัปเดตข้อมูลตอนนี้"):
    st.rerun()

def get_stock_html():
    rows_html = ""
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="30d")
            if not hist.empty:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                diff = curr - prev
                pct = (diff / prev) * 100
                delta = hist['Close'].diff()
                up = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
                down = -delta.clip(upper=0).rolling(window=14).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (up / down))) if down != 0 else 100

                # เงื่อนไขสี RSI < 30
                rsi_class = "rsi-alert" if rsi < 30 else ""
                alert_icon = "⚠️ " if rsi < 30 else ""
                
                style = "pos" if diff > 0 else "neg" if diff < 0 else ""
                sign = "+" if diff > 0 else ""

                rows_html += f"""
                <tr>
                    <td><b>{alert_icon}{t.replace('.BK','')}</b></td>
                    <td>฿{prev:,.2f}</td>
                    <td>฿{curr:,.2f}</td>
                    <td class="{style}">{sign}{diff:.2f}</td>
                    <td class="{style}">{sign}{pct:.2f}%</td>
                    <td class="{rsi_class}">{rsi:.2f}</td>
                </tr>
                """
        except: continue
    return rows_html

# 4. การแสดงผล (ล็อกเวลา 30 นาที)
@st.fragment(run_every="30m")
def show_board():
    st.title("📊 SET100 Full Live Board (Premium Sortable)")
    rows = get_stock_html()
    table_html = f"""
    <table class="custom-table">
        <thead>
            <tr>
                <th onclick="sortTable(0)">Ticker ↕</th>
                <th onclick="sortTable(1)">ราคาปิดก่อนหน้า ↕</th>
                <th onclick="sortTable(2)">ราคาล่าสุด ↕</th>
                <th onclick="sortTable(3)">เปลี่ยนแปลง ↕</th>
                <th onclick="sortTable(4)">% ↕</th>
                <th onclick="sortTable(5)">RSI ↕</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    <p style='color: gray; font-size: 12px; margin-top: 10px;'>
        อัปเดตเมื่อ: {datetime.now().strftime('%H:%M:%S')} | รีเฟรชทุก 30 นาที
    </p>
    """
    st.markdown(table_html, unsafe_allow_html=True)
