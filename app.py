import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. 密碼保護功能 ---
CORRECT_PASSWORD = "0612" 

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

# --- 3. CSS 樣式 (Percento 收折卡片風格，純字串不含變數) ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    
    /* 收折卡片主體 */
    .percento-card {
        background: white; border-radius: 18px; padding: 0;
        margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        overflow: hidden;
    }
    
    /* 點擊區域 (隱藏預設三角形) */
    .summary-box {
        display: flex; align-items: stretch; cursor: pointer;
        list-style: none; 
    }
    .summary-box::-webkit-details-marker { display: none; }
    
    /* 左側顏色條 */
    .color-bar { width: 16px; }
    
    /* 主類別內容區 */
    .summary-content {
        padding: 24px 20px; flex-grow: 1;
        display: flex; justify-content: space-between; align-items: center;
    }
    .main-title { font-size: 18px; font-weight: 700; color: #1C1C1E; }
    .main-sub { font-size: 13px; color: #8E8E93; margin-top: 4px; }
    .main-price { font-size: 22px; font-weight: 700; color: #1C1C1E; text-align: right; }
    .decimal-text { font-size: 14px; color: #8E8E93; font-weight: 600; }
    
    /* 展開後的子項目列表區 */
    .sub-list {
        background: #FAFAFB; padding: 10px 20px 20px 20px;
        border-top: 1px solid #F2F2F7;
    }
    .sub-item {
        display: flex; justify-content: space-between; align-items: center;
        padding: 12px 0; border-bottom: 1px solid #E5E5EA;
    }
    .sub-item:last-child { border-bottom: none; padding-bottom: 0; }
    .sub-title { font-size: 15px; font-weight: 600; color: #333; }
    .sub-desc { font-size: 12px; color: #8E8E93; margin-top: 4px; }
    .sub-price { font-size: 16px; font-weight: 600; color: #1C1C1E; }
    
    .amount-header { font-size: 36px; font-weight: 700; margin-bottom: 30px; color: #1C1C1E; }
</style>
""", unsafe_allow_html=True)

# --- 4. 數字解析工具 ---
def parse_val(val):
    if pd.isna(val) or val == "": return 0.0
    try:
        res = "".join(re.findall(r"[-+]?\d*\.\d+|\d+", str(val)))
        return float(res)
    except:
        return 0.0

# --- 5. 主類別映射邏輯 ---
def get_main_category(cat):
    cat_str = str(cat)
    if "流動" in cat_str: return "流動資金"
    if "投資" in cat_str: return "投資"
    if "固定" in cat_str: return "固定資產"
    if "負債" in cat_str: return "負債"
    return "其他"

# --- 6. 數據讀取與核心邏輯 ---
url = "https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)

    # A. 核心過濾
    items_df = df[df['類別'].notna() & ~df['項目'].str.contains('合計', na=False)].copy()
    
    # B. 新增主類別欄位
    items_df['主類別'] = items_df['類別'].apply(get_main_category)
    
    # C. 計算總淨資產
    total_net = items_df['總價值公式'].apply(parse_val).sum()

    st.markdown('<p style="color: #8E8E93; font-size: 14px; font-weight: 600;">我的資產 (TWD)</p>', unsafe_allow_html=True)
    st.markdown('<p class="amount-header">{:,.2f}</p>'.format(total_net), unsafe_allow_html=True)

    # 定義主類別順序與 Percento 風格顏色
    main_cat_order = ["流動資金", "投資", "固定資產", "負債"]
    main_colors = {
        "流動資金": "#D1BBEB",  # 淡紫
        "投資": "#FF9E79",      # 橘粉
        "固定資產": "#43CCC9",  # 藍綠
        "負債": "#FBD588"       # 鵝黃
    }

    # --- 7. 渲染收折卡片 (完全使用字串拼接) ---
    for m_cat in main_cat_order:
        sub_df = items_df[items_df['主類別'] == m_cat]
        if sub_df.empty: continue
        
        # 該大類別的總額
        cat_total = sub_df['總價值公式'].apply(parse_val).sum()
        
        # 組合次項目的 HTML 列表
        sub_items_html = ""
        for _, row in sub_df.iterrows():
            if pd.isna(row['項目']): continue
            
            amt = parse_val(row['總價值公式'])
            qty = parse_val(row['持有數量'])
            qty_txt = "{:,.6f}".format(qty) if 0 < qty < 1 else "{:,.0f}".format(qty)
            sub_name = str(row['項目'])
            sub_cat = str(row['類別']) # 顯示原本的次類別 (例如：投資-加密貨幣)
            
            sub_items_html += (
                '<div class="sub-item">'
                '<div>'
                '<div class="sub-title">' + sub_name + '</div>'
                '<div class="sub-desc">持有：' + qty_txt + '<br>' + sub_cat + '</div>'
                '</div>'
                '<div class="sub-price">' + "{:,.2f}".format(amt) + '</div>'
                '</div>'
            )

        # 外層大卡片的 HTML 設定
        color = main_colors.get(m_cat, "#D1D1D6")
        
        # 針對負債做特別處理（像 Percento 顯示負號）
        is_debt = (m_cat == "負債")
        sign_html = '<span style="color:#1C1C1E; margin-right:4px;">➖</span>' if is_debt else ""
        
        # 將整數與小數點分開，讓字體大小有層次感 (Percento 的細節)
        total_str = "{:,.2f}".format(abs(cat_total))
        int_part, dec_part = total_str.split('.')

        card_html = (
            '<details class="percento-card">'
            '<summary class="summary-box">'
            '<div class="color-bar" style="background-color: ' + color + ';"></div>'
            '<div class="summary-content">'
            '<div>'
            '<div class="main-title">' + m_cat + '</div>'
            '<div class="main-sub">••• 點擊展開明細</div>'
            '</div>'
            '<div class="main-price">' + sign_html + int_part + '<span class="decimal-text">.' + dec_part + '</span></div>'
            '</div>'
            '</summary>'
            '<div class="sub-list">'
            + sub_items_html +
            '</div>'
            '</details>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

except Exception as e:
    # 開發時建議把 e 印出來，上線後再改成 "連線中..."
    st.error("連線或讀取資料發生錯誤: " + str(e))
