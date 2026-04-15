import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. 密碼鎖定邏輯 ---
# 密碼維持最初設定
CORRECT_PASSCODE = "1234" 

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "auth_code" not in st.session_state:
    st.session_state["auth_code"] = ""

# 強制 CSS：鎖死手機 3 欄佈局，防止變成一條直線
st.markdown("""
<style>
    /* 強制 columns 不換行 */
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }
    /* 數字按鈕樣式 */
    div.stButton > button {
        height: 70px;
        width: 100%;
        border-radius: 15px;
        background-color: white;
        color: #1C1C1E;
        font-size: 24px;
        font-weight: 600;
        border: 1px solid #E5E5EA;
        margin-bottom: 5px;
    }
    /* 登入按鈕樣式 */
    div.stButton > button[kind="primary"] {
        background-color: #007AFF;
        color: white;
        border: none;
        height: 60px;
        margin-top: 15px;
    }
    /* 隱藏上方多餘空白 */
    [data-testid="stHeader"] { visibility: hidden; }
    .stAppViewMain { padding-top: 0px; }
</style>
""", unsafe_allow_html=True)

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center; color: #1C1C1E; margin-top: 50px;'>請輸入密碼</h2>", unsafe_allow_html=True)
    
    # 顯示密碼進度
    dots = "●" * len(st.session_state["auth_code"]) + "○" * (len(CORRECT_PASSCODE) - len(st.session_state["auth_code"]))
    st.markdown(f"<h1 style='text-align: center; letter-spacing: 15px; color: #8E8E93;'>{dots}</h1>", unsafe_allow_html=True)

    # 1-9 數字鍵盤
    for row in [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]:
        cols = st.columns(3)
        for i, key in enumerate(row):
            if cols[i].button(key):
                if len(st.session_state["auth_code"]) < len(CORRECT_PASSCODE):
                    st.session_state["auth_code"] += key
                    st.rerun()

    # 0 與 清除
    col_l, col_m, col_r = st.columns(3)
    if col_l.button("❌"):
        st.session_state["auth_code"] = ""
        st.rerun()
    if col_m.button("0"):
        if len(st.session_state["auth_code"]) < len(CORRECT_PASSCODE):
            st.session_state["auth_code"] += "0"
            st.rerun()

    # 登入按鈕
    if st.button("登入", use_container_width=True, type="primary"):
        if st.session_state["auth_code"] == CORRECT_PASSCODE:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("密碼錯誤")
            st.session_state["auth_code"] = ""
            st.rerun()
            
    st.stop()

# --- 3. 資產頁面 (解鎖後顯示) ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    .asset-card {
        background: white; border-radius: 18px; 
        margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        display: flex; align-items: stretch; overflow: hidden;
    }
    .color-tag { width: 10px; }
    .card-content { padding: 18px; flex-grow: 1; display: flex; justify-content: space-between; align-items: center; }
</style>
""", unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing", ttl=0)
    
    # 過濾合計列
    items_df = df[df['類別'].notna() & ~df['項目'].str.contains('合計', na=False)].copy()
    
    # 解析數值函數
    def parse_val(val):
        if pd.isna(val) or val == "": return 0.0
        try: return float("".join(re.findall(r"[-+]?\d*\.\d+|\d+", str(val))))
        except: return 0.0

    total_val = items_df['總價值公式'].apply(parse_val).sum()
    
    st.markdown(f'<p style="color: #8E8E93; margin-top:20px;">我的淨資產 (台幣)</p>', unsafe_allow_html=True)
    st.markdown(f'<h1 style="font-size: 32px; margin-bottom: 25px;">NT$ {total_val:,.0f}</h1>', unsafe_allow_html=True)

    color_map = {"流動資產": "#A28BF3", "投資-股票": "#FF8A65", "投資-加密貨幣": "#4DB6AC", "固定資產": "#81C784", "負債": "#FFB74D"}

    for _, row in items_df.iterrows():
        c = color_map.get(row['類別'], "#D1D1D6")
        val = parse_val(row['總價值公式'])
        st.markdown(f"""
            <div class="asset-card">
                <div class="color-tag" style="background-color: {c};"></div>
                <div class="card-content">
                    <div>
                        <div style="font-weight: 600;">{row['項目']}</div>
                        <div style="font-size: 12px; color: #8E8E93;">{row['類別']}</div>
                    </div>
                    <div style="font-weight: 700;">NT$ {val:,.0f}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
except:
    st.info("資料讀取中...")
