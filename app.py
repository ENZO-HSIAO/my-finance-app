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

# --- 3. 全局 CSS 樣式 ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F8F9FB; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background-color: #EEF0F3; padding: 5px; border-radius: 14px; }
    .stTabs [data-baseweb="tab"] { height: 40px; background-color: transparent; border-radius: 10px; color: #8E8E93; border: none; font-weight: 600; font-size: 14px; flex-grow: 1; }
    .stTabs [aria-selected="true"] { background-color: white !important; color: #1C1C1E !important; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }

    .form-card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.03); border: 1px solid #F2F2F7; margin-bottom: 15px; }
    
    .percento-card { background: white; border-radius: 20px; margin-bottom: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); overflow: hidden; border: 1px solid #F2F2F7; }
    .summary-box { display: flex; align-items: stretch; cursor: pointer; list-style: none; }
    .color-bar { width: 10px; }
    .summary-content { padding: 22px 20px; flex-grow: 1; display: flex; justify-content: space-between; align-items: center; }
    
    .stButton>button { border-radius: 12px !important; font-weight: 700 !important; }
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
    raw_df = conn.read(spreadsheet=url, ttl=5)
    items_df = raw_df[raw_df['類別'].notna() & ~raw_df['項目'].str.contains('合計', na=False)].copy()
    items_df['主類別'] = items_df['類別'].apply(get_main_category)

    # 分成三個頁籤
    tab1, tab2, tab3 = st.tabs(["📈 資產總覽", "⚙️ 庫存更新", "✨ 新增資產"])

    # --- TAB 1: 資產總覽 ---
    with tab1:
        total_net = items_df['總價值公式'].apply(parse_val).sum()
        st.markdown(f'<p style="color:#8E8E93; margin-top:25px; font-weight:600;">我的資產 (TWD)</p><h1 style="font-size:42px; margin-bottom:30px; letter-spacing:-1px;">NT$ {total_net:,.0f}</h1>', unsafe_allow_html=True)
        
        main_colors = {"流動資金": "#D1BBEB", "投資": "#FF9E79", "固定資產": "#43CCC9", "負債": "#FBD588"}
        for m_cat in ["流動資金", "投資", "固定資產", "負債"]:
            sub_df = items_df[items_df['主類別'] == m_cat]
            if sub_df.empty: continue
            cat_total = sub_df['總價值公式'].apply(parse_val).sum()
            
            detail_html = ""
            for _, r in sub_df.iterrows():
                qty = parse_val(r["持有數量"])
                detail_html += (
                    f'<div style="display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid #F2F2F7;">'
                    f'<div><div style="font-weight:600;">{r["項目"]}</div>'
                    f'<div style="font-size:12px; color:#8E8E93;">持有: {qty:,.2f}</div></div>'
                    f'<div style="font-weight:600;">NT$ {parse_val(r["總價值公式"]):,.0f}</div></div>'
                )

            st.markdown(f"""
                <details class="percento-card"><summary class="summary-box">
                <div class="color-bar" style="background-color:{main_colors[m_cat]};"></div>
                <div class="summary-content">
                <div><div style="font-weight:700;">{m_cat}</div><div style="font-size:12px; color:#8E8E93;">點擊查看細項</div></div>
                <div style="font-size:20px; font-weight:700;">{cat_total:,.0f}</div>
                </div></summary>
                <div style="background:#FAFAFB; padding:20px; border-top:1px solid #F2F2F7;">{detail_html}</div>
                </details>
            """, unsafe_allow_html=True)

    # --- TAB 2: 快速更新 (保留顏色連動) ---
    with tab2:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("### ⚙️ 庫存調整")
        target_item = st.selectbox("選擇要更新的資產", items_df['項目'].unique())
        
        item_data = items_df[items_df['項目'] == target_item].iloc[0]
        m_cat = item_data['主類別']
        main_colors = {"流動資金": "#D1BBEB", "投資": "#FF9E79", "固定資產": "#43CCC9", "負債": "#FBD588"}
        active_color = main_colors.get(m_cat, "#1C1C1E")
        
        curr_q = parse_val(item_data['持有數量'])
        curr_v = parse_val(item_data['總價值公式'])
        u_price = curr_v / curr_q if curr_q > 0 else 1.0

        st.markdown(f"""
        <div class="form-card" style="border-left: 8px solid {active_color};">
            <div style="color: #8E8E93; font-size: 13px; font-weight: 600;">目前持倉</div>
            <div style="font-size: 34px; font-weight: 800; color: {active_color}; margin: 5px 0;">{curr_q:,.6f}</div>
            <div style="display: inline-block; background: {active_color}22; color: {active_color}; padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 700;">{target_item} ({m_cat})</div>
        </div>
        """, unsafe_allow_html=True)

        change = st.number_input("輸入異動數量", min_value=0.0, step=0.000001, format="%.6f")
        b1, b2 = st.columns(2)
        if b1.button("➕ 增加持倉", use_container_width=True):
            raw_df.loc[raw_df['項目'] == target_item, ['持有數量', '總價值公式']] = [curr_q + change, (curr_q + change) * u_price]
            conn.update(spreadsheet=url, data=raw_df.dropna(how="all"))
            st.cache_data.clear()
            st.rerun()
        if b2.button("➖ 減少持倉", use_container_width=True):
            raw_df.loc[raw_df['項目'] == target_item, ['持有數量', '總價值公式']] = [curr_q - change, (curr_q - change) * u_price]
            conn.update(spreadsheet=url, data=raw_df.dropna(how="all"))
            st.cache_data.clear()
            st.rerun()

    # --- TAB 3: 新增項目 ---
    with tab3:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("### ✨ 建立新資產項目")
        with st.form("new_asset_form", clear_on_submit=True):
            n_cat = st.selectbox("歸類類別", ["流動資金", "投資-股票", "投資-加密貨幣", "固定資產", "負債"])
            n_name = st.text_input("項目名稱 (例如: 0050)")
            c1, c2 = st.columns(2)
            i_qty = c1.number_input("初始數量", format="%.6f")
            i_val = c2.number_input("初始總價值 (TWD)")
            if st.form_submit_button("🚀 確認新增資產", use_container_width=True):
                if n_name:
                    new_row = pd.DataFrame([{"類別": n_cat, "項目": n_name, "持有數量": i_qty, "總價值公式": i_val}])
                    conn.update(spreadsheet=url, data=pd.concat([raw_df, new_row], ignore_index=True).dropna(how="all"))
                    st.cache_data.clear()
                    st.rerun()

except Exception as e:
    st.error(f"系統連線異常：{e}")
