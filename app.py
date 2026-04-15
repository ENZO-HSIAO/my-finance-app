import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

st.set_page_config(page_title="My Finance", page_icon="💰")

# 密碼
CORRECT_PASSWORD = "你的自訂密碼"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("密碼", type="password")
    if st.button("登入"):
        if pwd == CORRECT_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("錯誤")
    st.stop()

# 數字解析
def parse_val(val):
    if pd.isna(val): return 0
    return float(re.sub(r"[^\d.-]", "", str(val)) or 0)

# 讀資料
url = "你的 Google Sheet URL"

conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url, ttl=0)

# 🔥 關鍵：清理欄位名稱
df.columns = df.columns.str.strip()

# 🔍 debug（第一次可以打開）
# st.write(df.columns)

# --- 清理資料 ---
df = df[df['項目'].notna()]
df = df[~df['項目'].str.contains('合計', na=False)]
df = df.drop_duplicates(subset=['項目'])

# --- 計算 ---
total = df['總價值公式'].apply(parse_val).sum()

st.title("💰 我的淨資產")
st.subheader(f"NT$ {total:,.0f}")

# --- 顯示 ---
for _, row in df.iterrows():
    st.write(f"{row['項目']}：NT$ {parse_val(row['總價值公式']):,.0f}")
