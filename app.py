import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# 2. 定義你的 Google Sheets 網址 (請確保這行網址正確)
url = r"https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=drive_web"

# 3. CSS 美化 (Apple 風格)
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

# 4. 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 5. 定義讀取函數 (加入快取避免頻繁讀取)
@st.cache_data(ttl=600)
def load_data(sheets_url):
    return conn.read(spreadsheet=sheets_url)

# 6. 執行讀取並顯示介面
try:
    df = load_data(url)
    
    st.markdown('<p class="title">我的總資產 (元)</p>', unsafe_allow_html=True)
    
    # 計算總金額 (處理文字轉數字)
    total_df = df['總價值公式'].replace('[¥,]', '', regex=True).astype(float)
    total = total_df.sum()
    st.markdown(f'<p class="amount">¥ {total:,.2f}</p>', unsafe_allow_html=True)

    # 迴圈顯示每一張資產卡片
    for index, row in df.iterrows():
        if pd.isna(row['項目']): 
            continue
        
        st.markdown(f'''
        <div class="asset-card">
            <div>
                <div style="font-weight:600;">{row['項目']}</div>
                <div style="font-size:12px; color:#8E8E93;">{row['備註']}</div>
            </div>
            <div style="font-weight:700;">{row['總價值公式']}</div>
        </div>
        ''', unsafe_allow_html=True)

except Exception as e:
    st.error(f"讀取資料失敗，請確認 Google Sheets 網址或欄位名稱是否正確。")
    st.info("錯誤訊息: " + str(e))
