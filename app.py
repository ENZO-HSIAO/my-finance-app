import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. 密碼解鎖 UI 優化 (方格按鈕) ---
CORRECT_PASSWORD = "0612" 

if "auth_code" not in st.session_state:
    st.session_state["auth_code"] = ""
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# 注入 CSS：讓按鈕變成漂亮的圓角方塊
st.markdown("""
<style>
    div.stButton > button {
        height: 80px;
        width: 100%;
        border-radius: 20px;
        background-color: white;
        color: #1C1C1E;
        font-size: 26px;
        font-weight: 600;
        border: 1px solid #E5E5EA;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    div.stButton > button:active {
        background-color: #F2F2F7;
    }
    /* 隱藏預設的頂部工具欄讓它更像 App */
    [data-testid="stHeader"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center; color: #1C1C1E; margin-top: 50px;'>請輸入密碼</h2>", unsafe_allow_html=True)
    
    # 顯示密碼圓點
    dots = "●" * len(st.session_state["auth_code"]) + "○" * (len(CORRECT_PASSWORD) - len(st.session_state["auth_code"]))
    st.markdown("<h1 style='text-align: center; letter-spacing: 15px; color: #8E8E93;'>" + dots + "</h1>", unsafe_allow_html=True)

    # 3x4 方格佈局
    keys = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["清除", "0", "確定"]]
    
    for row in keys:
        cols = st.columns(3)
        for i, key in enumerate(row):
            if cols[i].button(key):
                if key == "清除":
                    st.session_state["auth_code"] = ""
                    st.rerun()
                elif key == "確定":
                    if st.session_state["auth_code"] == CORRECT_PASSWORD:
                        st.session_state["authenticated"] = True
                        st.rerun()
                    else:
                        st.error("密碼錯誤")
                        st.session_state["auth_code"] = ""
                else:
                    if len(st.session_state["auth_code"]) < len(CORRECT_PASSWORD):
                        st.session_state["auth_code"] += key
                        st.rerun()
    st.stop()

# --- 3. 資產頁面 (解鎖後) ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    .asset-card {
        background: white; border-radius: 18px; padding: 0;
        margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        display: flex; align-items: stretch; overflow: hidden;
    }
    .color-tag { width: 12px; }
    .card-content { padding: 20px; flex-grow: 1; display: flex; justify-content: space-between; align-items: center; }
    .title-text { font-size: 16px; font-weight: 600; color: #1C1C1E; }
    .sub-text { font-size: 12px; color: #8E8E93; margin-top: 4px; }
    .price-text { font-size: 18px; font-weight: 700; color: #1C1C1E; }
</style>
""", unsafe_allow_html=True)

def parse_val(val):
    if pd.isna(val) or val == "": return 0.0
    try: return float("".join(re.findall(r"[-+]?\d*\.\d+|\d+", str(val))))
    except: return 0.0

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing", ttl=0)
    items_df = df[df['類別'].notna() & ~df['項目'].str.contains('合計', na=False)].copy()
    items_df['總價值'] = items_df['總價值公式'].apply(parse_val)
    total_net = items_df['總價值'].sum()

    # --- 穩定版分頁 ---
    tab1, tab2 = st.tabs(["📊 資產清單", "📄 原始數據"])

    with tab1:
        st.markdown(f'<p style="color: #8E8E93; font-size: 14px; margin-top: 20px;">我的淨資產 (台幣)</p>', unsafe_allow_html=True)
        st.markdown(f'<h1 style="font-size: 32px; font-weight: 700;">NT$ {total_net:,.0f}</h1>', unsafe_allow_html=True)

        color_map = {"流動資產": "#A28BF3", "投資-股票": "#FF8A65", "投資-加密貨幣": "#4DB6AC", "固定資產": "#81C784", "負債": "#FFB74D"}

        for _, row in items_df.iterrows():
            c = color_map.get(row['類別'], "#D1D1D6")
            st.markdown(f"""
                <div class="asset-card">
                    <div class="color-tag" style="background-color: {c};"></div>
                    <div class="card-content">
                        <div><div class="title-text">{row['項目']}</div><div class="sub-text">{row['類別']}</div></div>
                        <div class="price-text">NT$ {row['總價值']:,.0f}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### Google Sheets 原始資料")
        st.dataframe(items_df[['類別', '項目', '持有數量', '總價值']], use_container_width=True)

except:
    st.info("數據讀取中...")
