import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# --- 【這裡修改你的密碼】 ---
CORRECT_PASSCODE = "0612" 

# 接收 JS 訊號的隱藏輸入框
check_code = st.text_input("code", type="password", key="hidden_core", label_visibility="collapsed")
if check_code == CORRECT_PASSCODE:
    st.session_state["authenticated"] = True
    st.rerun()

# --- 2. iPhone 解鎖 UI (加入確定按鈕) ---
if not st.session_state["authenticated"]:
    iphone_ui_html = """
    <style>
        .stApp { background: none; }
        [data-testid="stHeader"], [data-testid="stToolbar"] { display: none; }
        [data-testid="stVerticalBlock"] > div:first-child { display: none; }
        
        #iphone-lock-screen {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: linear-gradient(135deg, #1d1d1f 0%, #434343 100%);
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: white; z-index: 99999;
        }
        .lock-icon { font-size: 40px; margin-bottom: 20px; }
        .indicator-container { display: flex; gap: 15px; margin-bottom: 60px; }
        .dot { width: 13px; height: 13px; border: 1.5px solid #8e8e93; border-radius: 50%; }
        .dot.filled { background-color: #f2f2f7; border-color: #f2f2f7; }
        .keypad { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px 25px; }
        .key {
            width: 75px; height: 75px; background-color: rgba(255, 255, 255, 0.1);
            border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center;
            cursor: pointer; -webkit-tap-highlight-color: transparent;
        }
        .key:active { background-color: rgba(255, 255, 255, 0.3); }
        .key-number { font-size: 30px; }
        .key-text { font-size: 14px; font-weight: 500; } /* 確定/取消按鈕文字 */
        .bottom-buttons { position: absolute; bottom: 50px; width: 80%; display: flex; justify-content: space-between; color: rgba(255,255,255,0.8); }
    </style>

    <div id="iphone-lock-screen">
        <div class="lock-icon">🔒</div>
        <div style="margin-bottom: 30px;">輸入密碼</div>
        <div class="indicator-container">
            <div class="dot" id="dot-1"></div><div class="dot" id="dot-2"></div>
            <div class="dot" id="dot-3"></div><div class="dot" id="dot-4"></div>
        </div>
        <div class="keypad">
            <div class="key" onclick="press('1')"><span class="key-number">1</span></div>
            <div class="key" onclick="press('2')"><span class="key-number">2</span></div>
            <div class="key" onclick="press('3')"><span class="key-number">3</span></div>
            <div class="key" onclick="press('4')"><span class="key-number">4</span></div>
            <div class="key" onclick="press('5')"><span class="key-number">5</span></div>
            <div class="key" onclick="press('6')"><span class="key-number">6</span></div>
            <div class="key" onclick="press('7')"><span class="key-number">7</span></div>
            <div class="key" onclick="press('8')"><span class="key-number">8</span></div>
            <div class="key" onclick="press('9')"><span class="key-number">9</span></div>
            <div class="key" style="background:none;" onclick="reset()"><span class="key-text">清除</span></div>
            <div class="key" onclick="press('0')"><span class="key-number">0</span></div>
            <div class="key" style="background:rgba(255,255,255,0.2);" onclick="submit()"><span class="key-text">確定</span></div>
        </div>
        <div class="bottom-buttons"><span>緊急服務</span><span onclick="reset()">取消</span></div>
    </div>

    <script>
        let code = "";
        function press(n) {
            if (code.length < 4) {
                code += n;
                update();
                if (code.length === 4) { setTimeout(submit, 100); }
            }
        }
        function update() {
            for(let i=1; i<=4; i++) {
                document.getElementById('dot-'+i).classList.toggle('filled', i<=code.length);
            }
        }
        function submit() {
            const input = window.parent.document.querySelector('input[aria-label="code"]');
            if(input) {
                input.value = code;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
        function reset() { code = ""; update(); }
    </script>
    """
    st.components.v1.html(iphone_ui_html, height=1000)
    st.stop()

# --- 3. 資產頁面 (解鎖後) ---
# 維持你滿意的樣式與正確的加總邏輯
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    .asset-card {
        background: white; border-radius: 18px; padding: 20px;
        margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        display: flex; justify-content: space-between; align-items: center;
        border-left: 12px solid #D1D1D6;
    }
    .title-text { font-size: 16px; font-weight: 600; color: #1C1C1E; }
    .price-text { font-size: 18px; font-weight: 700; color: #1C1C1E; }
    .amount-header { font-size: 32px; font-weight: 700; margin-bottom: 30px; color: #1C1C1E; }
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
    total_net = items_df['總價值公式'].apply(parse_val).sum()

    st.markdown('<p style="color: #8E8E93; font-size: 14px; margin-top:30px;">我的淨資產 (台幣)</p>', unsafe_allow_html=True)
    st.markdown('<p class="amount-header">NT$ {:,.0f}</p>'.format(total_net), unsafe_allow_html=True)

    color_map = {"流動資產": "#A28BF3", "投資-股票": "#FF8A65", "投資-加密貨幣": "#4DB6AC", "固定資產": "#81C784", "負債": "#FFB74D"}

    for _, row in items_df.iterrows():
        c = color_map.get(row['類別'], "#D1D1D6")
        amt = parse_val(row['總價值公式'])
        st.markdown(f'<div class="asset-card" style="border-left-color: {c};"><div><div class="title-text">{row["項目"]}</div><div style="font-size:12px;color:#8E8E93;">{row["類別"]}</div></div><div class="price-text">NT$ {amt:,.0f}</div></div>', unsafe_allow_html=True)
except:
    st.error("同步數據中...")
