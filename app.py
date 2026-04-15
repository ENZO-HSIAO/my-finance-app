import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# --- 1. 頁面設定 ---
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. 密碼保護 ---
CORRECT_PASSWORD = "你的自訂密碼"

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

# --- 3. CSS ---
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
.asset-card {
    background: white; border-radius: 18px;
    margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    display: flex; overflow: hidden;
}
.color-tag { width: 10px; }
.card-content {
    padding: 18px; flex-grow: 1;
    display: flex; justify-content: space-between; align-items: center;
}
.title-text { font-size: 16px; font-weight: 600; }
.sub-text { font-size: 12px; color: #8E8E93; margin-top: 4px; }
.price-text { font-size: 18px; font-weight: 700; }
.amount-header { font-size: 32px; font-weight: 700; margin-bottom: 30px; }
</style>
""", unsafe_allow_html=True)

# --- 4. 數字解析 ---
def parse_val(val):
    if pd.isna(val) or val == "":
        return 0.0
    try:
        return float(re.sub(r"[^\d.-]", "", str(val)))
    except:
        return 0.0

# --- 5. 讀取 Google Sheets ---
url = "你的 Google Sheet URL"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)

    # --- 🔥 核心清理（關鍵修正） ---
    items_df = df.copy()

    # 1️⃣ 移除空列
    items_df = items_df[items_df['項目'].notna()]

    # 2️⃣ 移除「合計」
    items_df = items_df[~items_df['項目'].str.contains('合計', na=False)]

    # 3️⃣ 🔥 移除重複（解決翻倍問題）
    items_df = items_df.drop_duplicates(subset=['項目'])

    # 4️⃣ 移除沒數值的列
    items_df = items_df[items_df['總價值公式'].notna()]

    # --- 計算總資產 ---
    total_net = items_df['總價值公式'].apply(parse_val).sum()

    st.markdown('<p style="color: #8E8E93;">我的淨資產 (台幣)</p>', unsafe_allow_html=True)
    st.markdown('<p class="amount-header">NT$ {:,.0f}</p>'.format(total_net), unsafe_allow_html=True)

    # --- 顏色分類 ---
    color_map = {
        "流動資產": "#A28BF3",
        "投資-股票": "#FF8A65",
        "投資-加密貨幣": "#4DB6AC",
        "固定資產": "#81C784",
        "負債": "#FFB74D"
    }

    # --- 渲染卡片 ---
    for _, row in items_df.iterrows():
        c = color_map.get(row['類別'], "#D1D1D6")

        amt = parse_val(row['總價值公式'])
        qty = parse_val(row['持有數量'])

        if 0 < qty < 1:
            qty_text = "{:,.6f}".format(qty)
        else:
            qty_text = "{:,.0f}".format(qty)

        note = "" if pd.isna(row['備註']) else str(row['備註'])

        card_html = (
            '<div class="asset-card">'
            '<div class="color-tag" style="background:' + c + ';"></div>'
            '<div class="card-content">'
            '<div>'
            '<div class="title-text">' + str(row['項目']) + '</div>'
            '<div class="sub-text">持有：' + qty_text + '<br>' + str(row['類別']) + ' · ' + note + '</div>'
            '</div>'
            '<div class="price-text">NT$ ' + "{:,.0f}".format(amt) + '</div>'
            '</div>'
            '</div>'
        )

        st.markdown(card_html, unsafe_allow_html=True)

except Exception as e:
    st.error("資料載入失敗，請重新整理")
