import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. 密碼保護功能 ---
# 你可以在這裡修改你的專屬密碼
correct_password = "900612" 

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("### 🔐 私人資產管理系統")
    user_input = st.text_input("請輸入訪問密碼", type="password")
    if st.button("登入"):
        if user_input == correct_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("密碼錯誤，請重新輸入。")
    st.stop() # 沒登入前，後面的代碼完全不會執行

# --- 3. 登入成功後執行的程式碼 ---

# 定義你的 Google Sheets 網址
url = r"https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing"

# CSS 美化 (Apple 風格)
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    .asset-card {
        background: white; border-radius: 18px; padding: 20px;
        margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        display: flex; justify-content: space-between; align-items: center;
    }
    .title { font-size: 14px; color: #8E8E93; }
    .amount { font-size: 32px; font-weight: 700; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

# 連結 Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def load_data(sheets_url):
    return conn.read(spreadsheet=sheets_url)

try:
    df = load_data(url)
    
    st.markdown('<p class="title">我的總資產 (元)</p>', unsafe_allow_html=True)
    
    # 計算總金額
    df['金額數字'] = pd.to_numeric(df['總價值公式'], errors='coerce').fillna(0)
    total = df['金額數字'].sum()
    st.markdown(f'<p class="amount">¥ {total:,.2f}</p>', unsafe_allow_html=True)

    # 顯示資產卡片
    for index, row in df.iterrows():
        if pd.isna(row['項目']) or row['項目'] == '合計': 
            continue
        
        st.markdown(f'''
        <div class="asset-card">
            <div>
                <div style="font-weight:600;">{row['項目']}</div>
                <div style="font-size:12px; color:#8E8E93;">{row['備註']}</div>
            </div>
            <div style="font-weight:700;">¥ {row['總價值公式']}</div>
        </div>
        ''', unsafe_allow_html=True)

except Exception as e:
    st.error(f"資料讀取失敗，請檢查網路或 Secrets 設定。")
