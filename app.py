import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. 密碼保護功能 ---
correct_password = "０" 
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    st.markdown("### 🔐 私人資產管理系統")
    user_input = st.text_input("請輸入訪問密碼", type="password")
    if st.button("登入"):
        if user_input == correct_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("密碼錯誤。")
    st.stop()

# --- 3. CSS 樣式美化 ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    .asset-card {
        background: white; border-radius: 18px; padding: 0;
        margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        display: flex; align-items: stretch; overflow: hidden;
    }
    .color-tag { width: 12px; }
    .card-content {
        padding: 20px; flex-grow: 1;
        display: flex; justify-content: space-between; align-items: center;
    }
    .title-text { font-size: 16px; font-weight: 600; color: #1C1C1E; }
    .sub-text { font-size: 12px; color: #8E8E93; margin-top: 4px; line-height: 1.5; }
    .price-text { font-size: 18px; font-weight: 700; color: #1C1C1E; text-align: right; }
    .amount-header { font-size: 32px; font-weight: 700; margin-bottom: 30px; color: #1C1C1E; }
    </style>
""", unsafe_allow_html=True)

# --- 4. 核心解析函數 ---
def force_twd_display(val):
    """將任何輸入值強制轉為台幣整數顯示"""
    try:
        if pd.isna(val) or val == "": return 0, "NT$ 0"
        # 移除 NT$, 逗號等，只留數字與小數點
        s = str(val).replace('NT$', '').replace(',', '').replace('$', '').strip()
        num = float(re.findall(r"[-+]?\d*\.\d+|\d+", s)[0])
        return num, f"NT$ {num:,.0f}"
    except:
        return 0, f"NT$ 0"

# --- 5. 讀取與渲染 ---
url = r"https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 強制不使用快取
    df = conn.read(spreadsheet=url, ttl=0)
    
    # 計算總資產
    total_net = 0
    for v in df['總價值公式']:
        val, _ = force_twd_display(v)
        total_net += val

    st.markdown('<p style="color: #8E8E93; font-size: 14px; margin-bottom: 8px;">我的淨資產 (台幣)</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="amount-header">NT$ {total_net:,.0f}</p>', unsafe_allow_html=True)

    color_map = {
        "流動資產": "#A28BF3", "投資-股票": "#FF8A65", 
        "投資-加密貨幣": "#4DB6AC", "固定資產": "#81C784", "負債": "#FFB74D",
    }

    for _, row in df.iterrows():
        if pd.isna(row['項目']) or str(row['項目']).strip() == '合計': continue
        
        tag_color = color_map.get(row['類別'], "#D1D1D6")
        
        # 持有數量
        try:
            q = float(str(row['持有數量']).replace(',', ''))
            qty_text = f"{q:.6f}" if 0 < q < 1 else f"{q:,.0f}"
        except:
            qty_text = str(row['持有數量'])

        # 單項金額
        _, price_text = force_twd_display(row['總價值公式'])

        st.markdown(f'''
        <div class="asset-card">
            <div class="color-tag" style="background-color: {tag_color};"></div>
            <div class="card-content">
                <div style="flex: 1;">
                    <div class="title-text">{row['項目']}</div>
                    <div class="sub-text">持有：{qty_text}<br>{row['類別']} · {row['備註']}</div>
                </div>
                <div class="price-text">{price_text}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

except Exception as e:
    st.error("讀取失敗")
