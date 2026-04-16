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

# --- 3. CSS 樣式 ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #E5E5EA; padding: 4px; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { height: 35px; background-color: transparent; border-radius: 8px; color: #8E8E93; border: none; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: white !important; color: #1C1C1E !important; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .percento-card { background: white; border-radius: 18px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); overflow: hidden; }
    .summary-box { display: flex; align-items: stretch; cursor: pointer; list-style: none; }
    .summary-box::-webkit-details-marker { display: none; }
    .color-bar { width: 16px; }
    .summary-content { padding: 24px 20px; flex-grow: 1; display: flex; justify-content: space-between; align-items: center; }
    .main-title { font-size: 18px; font-weight: 700; color: #1C1C1E; }
    .main-price { font-size: 22px; font-weight: 700; color: #1C1C1E; }
    .decimal-text { font-size: 14px; color: #8E8E93; font-weight: 600; }
    .sub-list { background: #FAFAFB; padding: 10px 20px 20px 20px; border-top: 1px solid #F2F2F7; }
    .sub-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #E5E5EA; }
    .sub-price { font-size: 16px; font-weight: 600; color: #1C1C1E; }
</style>
""", unsafe_allow_html=True)

# --- 4. 工具函數 ---
def parse_val(val):
    if pd.isna(val) or val == "": return 0.0
    try:
        res = "".join(re.findall(r"[-+]?\d*\.\d+|\d+", str(val)))
        return float(res)
    except: return 0.0

def get_main_category(cat):
    cat_str = str(cat)
    if "流動" in cat_str: return "流動資金"
    if "投資" in cat_str: return "投資"
    if "固定" in cat_str: return "固定資產"
    if "負債" in cat_str: return "負債"
    return "其他"

# --- 5. 數據連接與讀取 ---
url = "https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 這裡讀取整張表，包含隱藏的列，以便寫回
    raw_df = conn.read(spreadsheet=url, ttl=10)
    
    # 建立用於顯示的過濾表
    items_df = raw_df[raw_df['類別'].notna() & ~raw_df['項目'].str.contains('合計', na=False)].copy()
    items_df['主類別'] = items_df['類別'].apply(get_main_category)

    tab1, tab2 = st.tabs(["📈 資產總覽", "⚙️ 調整庫存"])

    with tab1:
        total_net = items_df['總價值公式'].apply(parse_val).sum()
        st.markdown('<p style="color: #8E8E93; margin-top:20px; font-weight:600;">我的資產 (TWD)</p>', unsafe_allow_html=True)
        st.markdown('<h1 style="font-size:42px; margin-bottom:30px;">NT$ {:,.2f}</h1>'.format(total_net), unsafe_allow_html=True)

        main_cat_order = ["流動資金", "投資", "固定資產", "負債"]
        main_colors = {"流動資金": "#D1BBEB", "投資": "#FF9E79", "固定資產": "#43CCC9", "負債": "#FBD588"}

        for m_cat in main_cat_order:
            sub_df = items_df[items_df['主類別'] == m_cat]
            if sub_df.empty: continue
            cat_total = sub_df['總價值公式'].apply(parse_val).sum()
            
            sub_items_html = ""
            for _, row in sub_df.iterrows():
                amt = parse_val(row['總價值公式'])
                qty = parse_val(row['持有數量'])
                qty_txt = "{:,.6f}".format(qty) if 0 < qty < 1 else "{:,.0f}".format(qty)
                sub_items_html += (
                    '<div class="sub-item"><div><div class="sub-title">' + str(row['項目']) + '</div>'
                    '<div style="font-size:12px; color:#8E8E93;">持有：' + qty_txt + '</div></div>'
                    '<div class="sub-price">NT$ ' + "{:,.0f}".format(amt) + '</div></div>'
                )

            total_str = "{:,.2f}".format(abs(cat_total))
            int_part, dec_part = total_str.split('.')
            color = main_colors.get(m_cat, "#D1D1D6")
            
            st.markdown((
                '<details class="percento-card"><summary class="summary-box">'
                '<div class="color-bar" style="background-color: ' + color + ';"></div>'
                '<div class="summary-content"><div><div class="main-title">' + m_cat + '</div>'
                '<div style="font-size:12px; color:#8E8E93;">點擊查看明細</div></div>'
                '<div class="main-price">' + int_part + '<span class="decimal-text">.' + dec_part + '</span></div></div>'
                '</summary><div class="sub-list">' + sub_items_html + '</div></details>'
            ), unsafe_allow_html=True)

with tab2:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("### ⚙️ 資產異動")
        
        # --- 漂亮的操作卡片 ---
        st.markdown("""
        <style>
            /* 讓輸入框變高級 */
            div[data-baseweb="input"] {
                border-radius: 12px !important;
                border: 1px solid #E5E5EA !important;
                background-color: white !important;
                padding: 4px;
            }
            /* 調整按鈕樣式：Apple 風格 */
            .stButton>button {
                border-radius: 12px;
                padding: 12px 20px;
                font-weight: 600;
                transition: all 0.2s;
                border: none;
            }
            .plus-btn button { background-color: #1C1C1E !important; color: white !important; }
            .minus-btn button { background-color: white !important; color: #1C1C1E !important; border: 1px solid #E5E5EA !important; }
            
            /* 資產資訊卡 */
            .info-card {
                background: white;
                padding: 20px;
                border-radius: 18px;
                border: 1px solid #F2F2F7;
                box-shadow: 0 4px 12px rgba(0,0,0,0.03);
                margin-bottom: 24px;
            }
        </style>
        """, unsafe_allow_html=True)

        # 1. 選擇資產 (簡約下拉選單)
        target_item = st.selectbox("選擇要調整的項目", items_df['項目'].unique(), label_visibility="collapsed")
        
        # 2. 顯示目前狀態卡片
        item_data = items_df[items_df['項目'] == target_item].iloc[0]
        current_qty = parse_val(item_data['持有數量'])
        
        st.markdown(f"""
        <div class="info-card">
            <div style="color: #8E8E93; font-size: 14px; font-weight: 500;">目前持倉</div>
            <div style="font-size: 28px; font-weight: 700; color: #1C1C1E; margin: 4px 0;">{current_qty:,.6f}</div>
            <div style="font-size: 14px; color: #43CCC9; font-weight: 600;">{target_item}</div>
        </div>
        """, unsafe_allow_html=True)

        # 3. 輸入異動數量 (大文字輸入框)
        st.markdown("<p style='font-size: 14px; color: #8E8E93; margin-bottom: 8px;'>請輸入異動數量</p>", unsafe_allow_html=True)
        change_amt = st.number_input("異動數量", min_value=0.0, step=0.000001, format="%.6f", label_visibility="collapsed")

        # 4. 雙按鈕操作介面
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="plus-btn">', unsafe_allow_html=True)
            plus_clicked = st.button(f"➕ 增加 {change_amt if change_amt > 0 else ''}", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="minus-btn">', unsafe_allow_html=True)
            minus_clicked = st.button(f"➖ 減少 {change_amt if change_amt > 0 else ''}", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # 5. 處理寫入邏輯
        if plus_clicked or minus_clicked:
            if change_amt <= 0:
                st.error("請輸入大於 0 的數字")
            else:
                with st.spinner("正在同步數據..."):
                    new_qty = current_qty + change_amt if plus_clicked else current_qty - change_amt
                    
                    # 執行寫入 Google Sheets
                    raw_df.loc[raw_df['項目'] == target_item, '持有數量'] = new_qty
                    updated_df = raw_df.dropna(how="all")
                    conn.update(spreadsheet=url, data=updated_df)
                    
                    st.cache_data.clear()
                    st.toast(f"✅ {target_item} 已更新", icon='💰')
                    st.rerun()

        # --- 額外：直接覆蓋功能 (隱藏在摺疊選單中，避免誤觸) ---
        with st.expander("需要精確修正總數？"):
            fixed_qty = st.number_input("輸入修正後的正確總量", value=current_qty)
            if st.button("確認修正"):
                raw_df.loc[raw_df['項目'] == target_item, '持有數量'] = fixed_qty
                conn.update(spreadsheet=url, data=raw_df.dropna(how="all"))
                st.cache_data.clear()
                st.rerun()

except Exception as e:
    st.error("系統連線中或發生錯誤：" + str(e))
