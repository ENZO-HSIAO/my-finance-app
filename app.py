import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. 密碼保護功能 ---
# 請在此修改你的專屬密碼
correct_password = "你的自訂密碼" 

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
            st.error("密碼錯誤，請重新輸入。")
    st.stop()

# --- 3. CSS 強制美化 (Apple 彩色標籤版) ---
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

# --- 4. 讀取資料 ---
url = r"https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url)
    
    # 介面頂部：總資產
    st.markdown('<p style="color: #8E8E93; font-size: 14px; margin-bottom: 8px;">我的淨資產 (元)</p>', unsafe_allow_html=True)
    
    # 計算總金額
    df['金額數字'] = pd.to_numeric(df['總價值公式'], errors='coerce').fillna(0)
    total = df['金額數字'].sum()
    st.markdown(f'<p class="amount-header">¥ {total:,.2f}</p>', unsafe_allow_html=True)

    # 顏色對應表
    color_map = {
        "流動資產": "#A28BF3", # 紫色
        "投資-股票": "#FF8A65", # 橘色
        "投資-加密貨幣": "#4DB6AC", # 青色
        "固定資產": "#81C784", # 綠色
        "負債": "#FFB74D",    # 淺橘色
    }

    # 顯示列表
    for index, row in df.iterrows():
        # 跳過「合計」行或空行
        if pd.isna(row['項目']) or row['項目'] == '合計': 
            continue
        
        tag_color = color_map.get(row['類別'], "#D1D1D6")
        
        # 格式化持有數量 (處理幾股/幾顆)
        qty = row['持有數量']
        qty_display = f"{float(qty):,.4f}" if pd.to_numeric(qty, errors='coerce') > 0 else "-"

        st.markdown(f'''
        <div class="asset-card">
            <div class="color-tag" style="background-color: {tag_color};"></div>
            <div class="card-content">
                <div style="flex: 1;">
                    <div class="title-text">{row['項目']}</div>
                    <div class="sub-text">
                        持有：<span style="color: #1C1C1E; font-weight: 500;">{qty_display}</span> 
                        <br>{row['類別']} · {row['備註']}
                    </div>
                </div>
                <div class="price-text">¥ {row['總價值公式']}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

except Exception as e:
    st.error(f"發生錯誤，請確認 Google Sheets 權限與 Secret 設定。")
    st.info(f"錯誤代碼：{e}")
