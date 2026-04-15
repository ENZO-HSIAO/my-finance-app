import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. 密碼保護功能 ---
CORRECT_PASSWORD = "900612" 

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("### 🔐 私人資產管理系統")
    pwd_input = st.text_input("請輸入訪問密碼", type="password")
    if st.button("登入"):
        if pwd_input == CORRECT_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("密碼錯誤")
    st.stop()

# --- 3. CSS 樣式 (獨立字串，避免語法衝突) ---
style_css = """
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
"""
st.markdown(style_css, unsafe_allow_html=True)

# --- 4. 數字解析 ---
def parse_val(val):
    if pd.isna(val) or val == "": return 0.0
    try:
        return float("".join(re.findall(r"[-+]?\d*\.\d+|\d+", str(val))))
    except:
        return 0.0

# --- 5. 數據讀取與計算 ---
url = "https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)

    # A. 排除「合計」列，避免重複計算 (修正 72 萬錯誤)
    items_df = df[~df['項目'].str.contains('合計', na=False)].copy()
    
    # B. 計算台幣總額
    total_net = items_df['總價值公式'].apply(parse_val).sum()

    st.markdown('<p style="color: #8E8E93; font-size: 14px;">我的淨資產 (台幣)</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="amount-header">NT$ {total_net:,.0f}</p>', unsafe_allow_html=True)

    color_map = {
        "流動資產": "#A28BF3", "投資-股票": "#FF8A65", 
        "投資-加密貨幣": "#4DB6AC", "固定資產": "#81C784", "負債": "#FFB74D"
    }

    # 6. 渲染資產卡片 (使用 % 格式化徹底避開 f-string 衝突)
    for _, row in items_df.iterrows():
        if pd.isna(row['項目']): continue
        
        tag_color = color_map.get(row['類別'], "#D1D1D6")
        amt = parse_val(row['總價值公式'])
        qty = parse_val(row['持有數量'])
        qty_txt = "{:,.6f}".format(qty) if 0 < qty < 1 else "{:,.0f}".format(qty)
        note_txt = str(row['備註']) if not pd.isna(row['備註']) else ""

        card_html = """
        <div class="asset-card">
            <div class="color-tag" style="background-color: %s;"></div>
            <div class="card-content">
                <div>
                    <div class="title-text">%s</div>
                    <div class="sub-text">持有：%s<br>%s · %s</div>
                </div>
                <div class="price-text">NT$ %s</div>
            </div>
        </div>
        """ % (tag_color, row['項目'], qty_txt, row['類別'], note_txt, "{:,.0f}".format(amt))
        
        st.markdown(card_html, unsafe_allow_html=True)

except Exception as e:
    st.error("系統更新中，請點擊右上角 Rerun")
