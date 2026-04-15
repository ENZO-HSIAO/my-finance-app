import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. 密碼解鎖 UI (強制 3 欄格式) ---
CORRECT_PASSWORD = "1234" 

if "auth_code" not in st.session_state:
    st.session_state["auth_code"] = ""
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# 強制 CSS 佈局：解決手機端按鈕變一條的問題
st.markdown("""
<style>
    /* 強制欄位不換行 */
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }
    /* 按鈕樣式：確保寬度填滿欄位 */
    div.stButton > button {
        height: 65px;
        width: 100%;
        border-radius: 12px;
        background-color: white;
        color: #1C1C1E;
        font-size: 22px;
        font-weight: 600;
        border: 1px solid #E5E5EA;
        padding: 0px;
    }
    /* 登入按鈕 */
    div.stButton > button[kind="primary"] {
        background-color: #007AFF;
        color: white;
        height: 55px;
        font-size: 18px;
        margin-top: 15px;
    }
    [data-testid="stHeader"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center; color: #1C1C1E; margin-top: 30px;'>輸入密碼</h2>", unsafe_allow_html=True)
    
    # 密碼圓點
    dots = "●" * len(st.session_state["auth_code"]) + "○" * (len(CORRECT_PASSWORD) - len(st.session_state["auth_code"]))
    st.markdown(f"<h1 style='text-align: center; letter-spacing: 15px; color: #8E8E93;'>{dots}</h1>", unsafe_allow_html=True)

    # 1-9 佈局
    for row in [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]:
        cols = st.columns(3)
        for i, key in enumerate(row):
            if cols[i].button(key):
                if len(st.session_state["auth_code"]) < len(CORRECT_PASSWORD):
                    st.session_state["auth_code"] += key
                    st.rerun()

    # 0 佈局：讓 0 在中間
    cols_bottom = st.columns(3)
    if cols_bottom[0].button("❌"): # 左邊清除
        st.session_state["auth_code"] = ""
        st.rerun()
    if cols_bottom[1].button("0"): # 中間 0
        if len(st.session_state["auth_code"]) < len(CORRECT_PASSWORD):
            st.session_state["auth_code"] += "0"
            st.rerun()
    # 右邊留白或放別的

    # 登入按鈕
    if st.button("登入 🔒", use_container_width=True, type="primary"):
        if st.session_state["auth_code"] == CORRECT_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("密碼錯誤")
            st.session_state["auth_code"] = ""
            st.rerun()
    st.stop()

# --- 3. 資產頁面 (解鎖後) ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    .asset-card {
        background: white; border-radius: 16px; margin-bottom: 10px;
        display: flex; align-items: stretch; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .color-tag { width: 8px; }
    .card-content { padding: 15px; flex-grow: 1; display: flex; justify-content: space-between; align-items: center; }
</style>
""", unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing", ttl=0)
    items_df = df[df['類別'].notna() & ~df['項目'].str.contains('合計', na=False)].copy()
    
    st.markdown(f'<h1 style="font-size: 28px; margin-top:20px;">NT$ {items_df["總價值公式"].apply(lambda x: float("".join(re.findall(r"[-+]?\d*\.\d+|\d+", str(x)))) if pd.notna(x) else 0).sum():,.0f}</h1>', unsafe_allow_html=True)

    color_map = {"流動資產": "#A28BF3", "投資-股票": "#FF8A65", "投資-加密貨幣": "#4DB6AC", "固定資產": "#81C784", "負債": "#FFB74D"}

    for _, row in items_df.iterrows():
        c = color_map.get(row['類別'], "#D1D1D6")
        st.markdown(f'<div class="asset-card"><div class="color-tag" style="background-color: {c};"></div><div class="card-content"><div><div style="font-weight:600;">{row["項目"]}</div><div style="font-size:12px;color:grey;">{row["類別"]}</div></div><div style="font-weight:700;">NT$ {row["總價值公式"]}</div></div></div>', unsafe_allow_html=True)
except:
    st.info("更新中...")
