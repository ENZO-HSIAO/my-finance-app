import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. 密碼保護 (請設定你的密碼) ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("### 🔐 私人資產管理系統")
    pwd = st.text_input("輸入密碼", type="password")
    if st.button("登入"):
        if pwd == "0":
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

# --- 3. CSS 樣式 (回復原本的 Apple 風格) ---
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
def clean_num(val):
    """強力提取數字，移除所有符號"""
    if pd.isna(val) or val == "": return 0.0
    try:
        # 只抓數字和小數點
        num_str = "".join(re.findall(r"[-+]?\d*\.\d+|\d+", str(val)))
        return float(num_str)
    except:
        return 0.0

# --- 5. 讀取資料 ---
url = "https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0) # 強制不快取

    # 過濾掉「合計」那一列，避免重複計算數字
    display_df = df[df['項目'].str.contains('合計') == False].copy()
    
    # 計算總額 (只加 display_df 的數字)
    total_val = display_df['總價值公式'].apply(clean_num).sum()

    # 顯示標題
    st.markdown('<p style="color: #8E8E93; font-size: 14px; margin-bottom: 8px;">我的淨資產 (台幣)</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="amount-header">NT$ {total_val:,.0f}</p>', unsafe_allow_html=True)

    color_map = {
        "流動資產": "#A28BF3", "投資-股票": "#FF8A65", 
        "投資-加密貨幣": "#4DB6AC", "固定資產": "#81C784", "負債": "#FFB74D",
    }

    # 6. 渲染卡片
    for _, row in display_df.iterrows():
        if pd.isna(row['項目']): continue
        
        tag_color = color_map.get(row['類別'], "#D1D1D6")
        
        # 處理數量顯示
        try:
            q = float(row['持有數量'])
            qty_text = f"{q:.6f}" if 0 < q < 1 else f"{q:,.0f}"
        except:
            qty_text = str(row['持有數量'])

        # 處理金額顯示 (台幣整數)
        amt = clean_num(row['總價值公式'])
        
        # 特別修復：如果是銀行存款且總價為 0，改抓持有數量 (假設 1 點 = 1 元)
        if "銀行存款" in str(row['項目']) and amt == 0:
            amt = clean_num(row['持有數量'])

        st.markdown(f'''
        <div class="asset-card">
            <div class="color-tag" style="background-color: {tag
