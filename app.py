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
    raw_df = conn.read(spreadsheet=url, ttl=0)
    
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
        st.markdown("### 🛠️ 快速調整庫存")
        
        with st.container(border=True):
            target_item = st.selectbox("選擇資產項目", items_df['項目'].unique())
            
            # 找到當前項目的現有數量
            current_qty = parse_val(items_df.loc[items_df['項目'] == target_item, '持有數量'].values[0])
            st.write(f"當前庫存：`{current_qty}`")

            col1, col2 = st.columns(2)
            with col1:
                mode = st.radio("調整方式", ["增加數量", "減少數量", "直接修正總數"])
            with col2:
                change_amt = st.number_input("異動數量", min_value=0.0, step=0.000001, format="%.6f")
            
            if st.button("🚀 執行數據更新", use_container_width=True):
                with st.spinner("正在同步至 Google Sheets..."):
                    # 計算新數量
                    new_qty = current_qty
                    if mode == "增加數量": new_qty += change_amt
                    elif mode == "減少數量": new_qty -= change_amt
                    else: new_qty = change_amt
                    
                    # 更新 raw_df (確保格式正確)
                    raw_df.loc[raw_df['項目'] == target_item, '持有數量'] = new_qty
                    
                    # 清除因讀取產生的空白列，避免寫入失敗
                    updated_df = raw_df.dropna(how="all")
                    
                    # 寫回 Google Sheets
                    conn.update(spreadsheet=url, data=updated_df)
                    st.cache_data.clear() # 清除快取以顯示最新數據
                    st.success(f"更新成功！{target_item} 新數量為 {new_qty}")
                    st.balloons()
                    st.rerun()

except Exception as e:
    st.error("系統連線中或發生錯誤：" + str(e))
