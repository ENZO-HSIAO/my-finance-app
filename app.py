import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 頁面基本美化
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# CSS 強制美化成 Apple 質感
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
@st.cache_data(ttl=600)
def load_data(sheets_url):
    return conn.read(spreadsheet=sheets_url)

# 執行讀取
try:
    df = load_data(url)
except Exception as e:
st.error("讀取資料失敗，請確認 Sheets 網址是否正確。")
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url)

# 介面顯示
st.markdown('<p class="title">我的總資產 (元)</p>', unsafe_allow_html=True)
total = df['總價值公式'].replace('[¥,]', '', regex=True).astype(float).sum()
st.markdown(f'<p class="amount">¥ {total:,.2f}</p>', unsafe_allow_html=True)

for index, row in df.iterrows():
    if pd.isna(row['項目']): continue
    st.markdown(f'''
    <div class="asset-card">
        <div>
            <div style="font-weight:600;">{row['項目']}</div>
            <div style="font-size:12px; color:#8E8E93;">{row['備註']}</div>
        </div>
        <div style="font-weight:700;">{row['總價值公式']}</div>
    </div>
    ''', unsafe_allow_html=True)
