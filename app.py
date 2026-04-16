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

# --- 3. 全局 CSS 樣式 (極簡奢華風) ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F8F9FB; }
    
    /* Tab 導覽列 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px; background-color: #EEF0F3; padding: 5px; border-radius: 14px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px; background-color: transparent; border-radius: 10px;
        color: #8E8E93; border: none; font-weight: 600; font-size: 15px;
    }
    .stTabs [aria-selected="true"] {
        background-color: white !important; color: #1C1C1E !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }

    /* 資訊卡片 */
    .info-card {
        background: white; padding: 24px; border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.03); margin-bottom: 20px;
        border: 1px solid #F2F2F7;
    }

    /* 按鈕樣式 */
    .stButton>button {
        border-radius: 15px; padding: 15px 20px; font-weight: 700;
        transition: transform 0.1s ease; height: 60px;
    }
    .plus-btn button { background-color: #1C1C1E !important; color: white !important; border: none; }
    .minus-btn button { background-color: white !important; color: #1C1C1E !important; border: 1.5px solid #1C1C1E !important; }
    
    /* 資產摺疊卡片 */
    .percento-card { background: white; border-radius: 20px; margin-bottom: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); overflow: hidden; border: 1px solid #F2F2F7; }
    .summary-box { display: flex; align-items: stretch; cursor: pointer; list-style: none; }
    .color-bar { width: 10px; }
    .summary-content { padding: 22px 20px; flex-grow: 1; display: flex; justify-content: space-between; align-items: center; }
    .main-title { font-size: 17px; font-weight: 700; color: #1C1C1E; }
    .main-price { font-size: 20px; font-weight: 700; color: #1C1C1E; }
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

# --- 5. 數據讀取 ---
url = "https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    raw_df = conn.read(spreadsheet=url, ttl=10)
    # 過濾無效行
    items_df = raw_df[raw_df['類別'].notna() & ~raw_df['項目'].str.contains('合計', na=False)].copy()
    items_df['主類別'] = items_df['類別'].apply(get_main_category)

    tab1, tab2 = st.tabs(["📈 資產總覽", "⚙️ 資產更新"])

    with tab1:
        # 總淨資產計算
        total_net = items_df['總價值公式'].apply(parse_val).sum()
        st.markdown(f'<p style="color:#8E8E93; margin-top:25px; font-weight:600;">我的資產 (TWD)</p>', unsafe_allow_html=True)
        st.markdown(f'<h1 style="font-size:42px; margin-bottom:30px; letter-spacing:-1px;">NT$ {total_net:,.0f}</h1>', unsafe_allow_html=True)

        main_cat_order = ["流動資金", "投資", "固定資產", "負債"]
        main_colors = {"流動資金": "#D1BBEB", "投資": "#FF9E79", "固定資產": "#43CCC9", "負債": "#FBD588"}

        for m_cat in main_cat_order:
            sub_df = items_df[items_df['主類別'] == m_cat]
            if sub_df.empty: continue
            cat_total = sub_df['總價值公式'].apply(parse_val).sum()
            
            # 生成子項目 HTML
            sub_items_html = ""
            for _, row in sub_df.iterrows():
                amt = parse_val(row['總價值公式'])
                qty = parse_val(row['持有數量'])
                qty_txt = f"{qty:,.6f}" if 0 < qty < 1 else f"{qty:,.0f}"
                sub_items_html += (
                    f'<div style="display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid #F2F2F7;">'
                    f'<div><div style="font-weight:600;">{row["項目"]}</div>'
                    f'<div style="font-size:12px; color:#8E8E93;">持有: {qty_txt}</div></div>'
                    f'<div style="font-weight:600;">NT$ {amt:,.0f}</div></div>'
                )

            st.markdown(f"""
                <details class="percento-card"><summary class="summary-box">
                <div class="color-bar" style="background-color: {main_colors[m_cat]};"></div>
                <div class="summary-content">
                <div><div class="main-title">{m_cat}</div><div style="font-size:12px; color:#8E8E93;">點擊查看細項</div></div>
                <div class="main-price">{cat_total:,.2f}</div>
                </div></summary>
                <div style="background:#FAFAFB; padding: 10px 20px 20px 20px; border-top:1px solid #F2F2F7;">{sub_items_html}</div>
                </details>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("### ⚙️ 調整庫存")
        
        target_item = st.selectbox("請選擇資產項目", items_df['項目'].unique(), label_visibility="collapsed")
        
        # 獲取當前數據
        item_data = items_df[items_df['項目'] == target_item].iloc[0]
        current_qty = parse_val(item_data['持有數量'])
        current_total_val = parse_val(item_data['總價值公式'])
        
        # 計算當前單價 (用於連動更新)
        unit_price = current_total_val / current_qty if current_qty > 0 else 1.0

        st.markdown(f"""
        <div class="info-card">
            <div style="color: #8E8E93; font-size: 13px; font-weight: 600;">目前持倉數量</div>
            <div style="font-size: 34px; font-weight: 800; color: #1C1C1E; margin: 5px 0;">{current_qty:,.6f}</div>
            <div style="display: inline-block; background: #E8F5F2; color: #2D9C8B; padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 700;">{target_item}</div>
        </div>
        """, unsafe_allow_html=True)

        change_amt = st.number_input("輸入異動數量", min_value=0.0, step=0.000001, format="%.6f")

        col1, col2 = st.columns(2)
        new_qty = current_qty
        clicked = False

        with col1:
            st.markdown('<div class="plus-btn">', unsafe_allow_html=True)
            if st.button("➕ 增加持倉", use_container_width=True):
                new_qty = current_qty + change_amt
                clicked = True
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="minus-btn">', unsafe_allow_html=True)
            if st.button("➖ 減少持倉", use_container_width=True):
                new_qty = current_qty - change_amt
                clicked = True
            st.markdown('</div>', unsafe_allow_html=True)

        if clicked and change_amt > 0:
            with st.spinner("同步數據中..."):
                # 重要：連動計算新的總價值
                new_total_val = new_qty * unit_price
                
                # 同時更新數量與總價值
                raw_df.loc[raw_df['項目'] == target_item, '持有數量'] = new_qty
                raw_df.loc[raw_df['項目'] == target_item, '總價值公式'] = new_total_val
                
                conn.update(spreadsheet=url, data=raw_df.dropna(how="all"))
                st.cache_data.clear()
                st.toast(f"✅ {target_item} 更新成功")
                st.rerun()

        with st.expander("精確修正總量 (取代現有數值)"):
            fix_qty = st.number_input("修正數量為", value=current_qty, format="%.6f")
            fix_val = st.number_input("修正總金額為", value=current_total_val)
            if st.button("確認修正"):
                raw_df.loc[raw_df['項目'] == target_item, '持有數量'] = fix_qty
                raw_df.loc[raw_df['項目'] == target_item, '總價值公式'] = fix_val
                conn.update(spreadsheet=url, data=raw_df.dropna(how="all"))
                st.cache_data.clear()
                st.rerun()

except Exception as e:
    st.error(f"系統連線中或發生錯誤：{e}")
