import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. 密碼保護功能 ---
correct_password = "0" 

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

# --- 3. CSS 樣式美化 (Apple 風格) ---
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
    # 使用 ttl=0 確保每次重整都能抓到最新資料，或視需求改為 600 (10分鐘)
    df = conn.read(spreadsheet=url, ttl="0")
    
    # --- 總額計算邏輯 ---
    def clean_to_float(val):
        if pd.isna(val): return 0.0
        # 只保留數字與小數點，過濾掉 NT$, $, 逗號或文字
        num_str = "".join(re.findall(r"[-+]?\d*\.\d+|\d+", str(val)))
        try:
            return float(num_str)
        except:
            return 0.0

    df['計算金額'] = df['總價值公式'].apply(clean_to_float)
    total_net = df['計算金額'].sum()

    # 顯示總資產標題
    st.markdown('<p style="color: #8E8E93; font-size: 14px; margin-bottom: 8px;">我的淨資產 (台幣)</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="amount-header">NT$ {total_net:,.0f}</p>', unsafe_allow_html=True)

    # 類別顏色對應
    color_map = {
        "流動資產": "#A28BF3", 
        "投資-股票": "#FF8A65", 
        "投資-加密貨幣": "#4DB6AC", 
        "固定資產": "#81C784", 
        "負債": "#FFB74D",
    }

    # --- 5. 渲染資產清單 ---
    for _, row in df.iterrows():
        if pd.isna(row['項目']) or str(row['項目']).strip() == '合計': 
            continue
        
        tag_color = color_map.get(row['類別'], "#D1D1D6")
        
        # 處理持有數量 (qty)
        try:
            q_val = float(row['持有數量'])
            # 小於 1 的加密貨幣顯示 6 位小數，大於 1 的資產顯示千分位整數
            qty_display = f"{q_val:.6f}" if 0 < q_val < 1 else f"{q_val:,.0f}"
        except:
            qty_display = str(row['持有數量'])

        # 處理單項金額 (price)
        p_val = clean_to_float(row['總價值公式'])
        price_display = f"NT$ {p_val:,.0f}"

        # 輸出 HTML 卡片
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
                <div class="price-text">{price_display}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

except Exception as e:
    st.error("讀取失敗，請確認 Sheets 權限或 Secrets 設定。")
    st.info(f"錯誤訊息：{e}")
