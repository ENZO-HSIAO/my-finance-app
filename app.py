import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面基本設定與密碼 (密碼請自訂)
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. 密碼保護 ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    user_input = st.text_input("輸入密碼登入", type="password")
    if st.button("登入"):
        if user_input == "0":
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

# --- 3. 核心功能：把「文字」變回「台幣數字」 ---
def to_twd_float(val):
    if pd.isna(val) or val == "": return 0.0
    # 這裡會強行移除所有 NT$、逗號、空格，只留下數字跟小數點
    try:
        num_str = "".join(re.findall(r"[-+]?\d*\.\d+|\d+", str(val)))
        return float(num_str)
    except:
        return 0.0

# --- 4. 讀取 Google Sheets ---
url = "https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # ttl=0 非常重要：這會強制程式每次都去抓最新的台幣資料，不准它記舊的！
    df = conn.read(spreadsheet=url, ttl=0)

    # 清理資料：確保「總價值公式」這一欄全部變成乾淨的數字
    df['clean_amount'] = df['總價值公式'].apply(to_twd_float)
    total_sum = df['clean_amount'].sum()

    # --- 5. 顯示總額 ---
    st.markdown(f"### 我的淨資產 (台幣)")
    st.markdown(f"<h1 style='color:black;'>NT$ {total_sum:,.0f}</h1>", unsafe_allow_html=True)

    # --- 6. 顯示資產清單 ---
    for _, row in df.iterrows():
        if pd.isna(row['項目']) or str(row['項目']) == "合計": continue
        
        amt = to_twd_float(row['總價值公式'])
        qty = row['持有數量']
        
        # 顯示卡片 (這裡簡化排版，確保數據先跑對)
        st.info(f"**{row['項目']}** | 持有: {qty} | **NT$ {amt:,.0f}**")

except Exception as e:
    st.error(f"讀取失敗，請檢查權限或欄位名稱是否正確。")
