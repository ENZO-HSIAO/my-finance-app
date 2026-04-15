import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 2. iPhone 數字解鎖邏輯 ---
# 這裡設定你的 4 位數或多位數密碼
CORRECT_PASSWORD = "1234"

if "auth_code" not in st.session_state:
    st.session_state["auth_code"] = ""
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    # 鎖定畫面 UI
    st.markdown("<h2 style='text-align: center; color: #1C1C1E; margin-top: 50px;'>請輸入密碼</h2>", unsafe_allow_html=True)
    
    # 顯示密碼圓點
    dots = "●" * len(st.session_state["auth_code"]) + "○" * (len(CORRECT_PASSWORD) - len(st.session_state["auth_code"]))
    st.markdown("<h1 style='text-align: center; letter-spacing: 15px; color: #8E8E93;'>" + dots + "</h1>", unsafe_allow_html=True)

    # 模擬 iPhone 鍵盤 (3x4)
    keys = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["清除", "0", "確定"]]
    
    for row in keys:
        cols = st.columns([1, 1, 1])
        for i, key in enumerate(row):
            if cols[i].button(key, use_container_width=True):
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

# --- 3. 進入資產頁面 (維持你滿意的樣式) ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    .asset-card {
        background: white; border-radius: 18px; padding: 0;
        margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        display: flex; align-items: stretch; overflow: hidden;
    }
    .color-tag { width: 12px; }
    .card-content {
        padding: 20px; flex-grow: 1;
        display: flex; justify-content: space-between; align-items: center;
    }
    .title-text { font-size: 16px; font-weight: 600; color: #1C1C1E; }
    .sub-text { font-size: 12px; color: #8E8E93; margin-top: 4px; line-height: 1.5; }
    .price-text { font-size: 18px; font-weight: 700; color: #1C1C1E; text-align: right; }
    .amount-header { font-size: 32px; font-weight: 700; margin-bottom: 30px; color: #1C1C1E; }
</style>
""", unsafe_allow_html=True)

def parse_val(val):
    if pd.isna(val) or val == "": return 0.0
    try:
        return float("".join(re.findall(r"[-+]?\d*\.\d+|\d+", str(val))))
    except:
        return 0.0

url = "https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)

    # 核心邏輯：維持目前的過濾方式，排除「合計」列
    items_df = df[df['類別'].notna() & ~df['項目'].str.contains('合計', na=False)].copy()
    
    total_net = items_df['總價值公式'].apply(parse_val).sum()

    st.markdown('<p style="color: #8E8E93; font-size: 14px;">我的淨資產 (台幣)</p>', unsafe_allow_html=True)
    st.markdown('<p class="amount-header">NT$ {:,.0f}</p>'.format(total_net), unsafe_allow_html=True)

    color_map = {
        "流動資產": "#A28BF3", "投資-股票": "#FF8A65", 
        "投資-加密貨幣": "#4DB6AC", "固定資產": "#81C784", "負債": "#FFB74D"
    }

    # 渲染卡片 (純字串拼接，保證不報語法錯)
    for _, row in items_df.iterrows():
        if pd.isna(row['項目']): continue
        
        c = color_map.get(row['類別'], "#D1D1D6")
        v = parse_val(row['總價值公式'])
        q = parse_val(row['持有數量'])
        q_txt = "{:,.6f}".format(q) if 0 < q < 1 else "{:,.0f}".format(q)
        n = str(row['備註']) if not pd.isna(row['備註']) else ""

        card_html = (
            '<div class="asset-card">'
            '<div class="color-tag" style="background-color: ' + c + ';"></div>'
            '<div class="card-content">'
            '<div>'
                '<div class="title-text">' + str(row['項目']) + '</div>'
                '<div class="sub-text">持有：' + q_txt + '<br>' + str(row['類別']) + ' · ' + n + '</div>'
            '</div>'
            '<div class="price-text">NT$ ' + "{:,.0f}".format(v) + '</div>'
            '</div>'
            '</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

except Exception as e:
    st.error("同步數據中...")
