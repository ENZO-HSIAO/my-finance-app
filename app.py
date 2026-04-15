import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re
import json

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

# --- 核心邏輯：JavaScript 與 Streamlit 溝通 ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# 設定密碼
CORRECT_PASSCODE = "1234"

def unlock_app():
    st.session_state["authenticated"] = True

# 密碼檢查元件
if not st.session_state["authenticated"]:
    check_code = st.text_input("code", type="password", key="hidden_core", label_visibility="collapsed")
    if check_code == str(CORRECT_PASSCODE):
        unlock_app()
        st.rerun()

# --- 2. 極致 iPhone 解鎖 UI ---
if not st.session_state["authenticated"]:
    # 注意：這裡我把原本的 %s 換成了 {{PASSCODE_PLACEHOLDER}}
    iphone_ui_template = """
    <style>
        .stApp { background: none; }
        [data-testid="stHeader"] { display: none; }
        [data-testid="stToolbar"] { display: none; }
        [data-testid="stVerticalBlock"] > div:first-child { display: none; }
        
        #iphone-lock-screen {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: linear-gradient(135deg, #1d1d1f 0%, #434343 100%);
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: white; z-index: 99999;
        }

        .lock-icon { font-size: 40px; margin-bottom: 20px; }
        .prompt-text { font-size: 17px; font-weight: 400; margin-bottom: 30px; letter-spacing: 0.5px; }

        .indicator-container { display: flex; gap: 15px; margin-bottom: 60px; }
        .dot {
            width: 13px; height: 13px;
            border: 1.5px solid #8e8e93; border-radius: 50%;
            background: transparent; transition: background 0.1s;
        }
        .dot.filled { background-color: #f2f2f7; border-color: #f2f2f7; }

        .keypad { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px 25px; }
        .key {
            width: 75px; height: 75px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            cursor: pointer; -webkit-tap-highlight-color: transparent;
            transition: background 0.1s;
        }
        .key:active { background-color: rgba(255, 255, 255, 0.3); }
        .key-number { font-size: 30px; font-weight: 400; }
        .key-letters { font-size: 9px; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,0.7); }

        .bottom-buttons {
            position: absolute; bottom: 50px; width: 80%;
            display: flex; justify-content: space-between; font-size: 16px;
        }

        @keyframes shake { 
            0%, 100% { transform: translateX(0); } 
            20%, 60% { transform: translateX(-10px); } 
            40%, 80% { transform: translateX(10px); } 
        }
    </style>

    <div id="iphone-lock-screen">
        <div class="lock-icon">🔒</div>
        <div class="prompt-text">輸入密碼</div>
        <div class="indicator-container">
            <div class="dot" id="dot-1"></div>
            <div class="dot" id="dot-2"></div>
            <div class="dot" id="dot-3"></div>
            <div class="dot" id="dot-4"></div>
        </div>
        <div class="keypad">
            <div class="key" onclick="press('1')"><span class="key-number">1</span><span class="key-letters">&nbsp;</span></div>
            <div class="key" onclick="press('2')"><span class="key-number">2</span><span class="key-letters">ABC</span></div>
            <div class="key" onclick="press('3')"><span class="key-number">3</span><span class="key-letters">DEF</span></div>
            <div class="key" onclick="press('4')"><span class="key-number">4</span><span class="key-letters">GHI</span></div>
            <div class="key" onclick="press('5')"><span class="key-number">5</span><span class="key-letters">JKL</span></div>
            <div class="key" onclick="press('6')"><span class="key-number">6</span><span class="key-letters">MNO</span></div>
            <div class="key" onclick="press('7')"><span class="key-number">7</span><span class="key-letters">PQRS</span></div>
            <div class="key" onclick="press('8')"><span class="key-number">8</span><span class="key-letters">TUV</span></div>
            <div class="key" onclick="press('9')"><span class="key-number">9</span><span class="key-letters">WXYZ</span></div>
            <div style="visibility: hidden;"></div>
            <div class="key" onclick="press('0')"><span class="key-number">0</span><span class="key-letters">&nbsp;</span></div>
        </div>
        <div class="bottom-buttons">
            <span>緊急服務</span>
            <span onclick="resetPasscode()">取消</span>
        </div>
    </div>

    <script>
        let currentCode = "";
        const correctHash = "{{PASSCODE_PLACEHOLDER}}"; 

        function press(num) {
            if (currentCode.length < 4) {
                currentCode += num;
                updateIndicators();
                if (currentCode.length === 4) {
                    checkPasscode();
                }
            }
        }

        function updateIndicators() {
            for (let i = 1; i <= 4; i++) {
                const dot = document.getElementById(`dot-${i}`);
                if (i <= currentCode.length) {
                    dot.classList.add('filled');
                } else {
                    dot.classList.remove('filled');
                }
            }
        }

        function resetPasscode() {
            currentCode = "";
            updateIndicators();
        }

        function checkPasscode() {
            if (currentCode === correctHash) {
                const stInput = window.parent.document.querySelector('input[aria-label="code"]');
                if (stInput) {
                    stInput.value = currentCode;
                    stInput.dispatchEvent(new Event('input', { bubbles: true }));
                    document.getElementById('iphone-lock-screen').style.display = 'none';
                }
            } else {
                const container = document.querySelector('.indicator-container');
                container.style.animation = 'shake 0.3s';
                setTimeout(() => {
                    container.style.animation = '';
                    resetPasscode();
                }, 300);
            }
        }
    </script>
    """
    # 使用 replace 避免 % 或 f-string 的轉義問題
    iphone_ui_html = iphone_ui_template.replace("{{PASSCODE_PLACEHOLDER}}", str(CORRECT_PASSCODE))
    st.components.v1.html(iphone_ui_html, height=1000, scrolling=False)
    st.stop()

# --- 3. 資產頁面 ---
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
        res = "".join(re.findall(r"[-+]?\d*\.\d+|\d+", str(val)))
        return float(res)
    except:
        return 0.0

url = "https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)

    items_df = df[df['類別'].notna() & ~df['項目'].str.contains('合計', na=False)].copy()
    total_net = items_df['總價值公式'].apply(parse_val).sum()

    st.markdown('<p style="color: #8E8E93; font-size: 14px;">我的淨資產 (台幣)</p>', unsafe_allow_html=True)
    st.markdown('<p class="amount-header">NT$ {:,.0f}</p>'.format(total_net), unsafe_allow_html=True)

    color_map = {
        "流動資產": "#A28BF3", "投資-股票": "#FF8A65", 
        "投資-加密貨幣": "#4DB6AC", "固定資產": "#81C784", "負債": "#FFB74D"
    }

    for _, row in items_df.iterrows():
        if pd.isna(row['項目']): continue
        c = color_map.get(row['類別'], "#D1D1D6")
        amt = parse_val(row['總價值公式'])
        qty = parse_val(row['持有數量'])
        q_txt = "{:,.6f}".format(qty) if 0 < qty < 1 else "{:,.0f}".format(qty)
        note = str(row['備註']) if not pd.isna(row['備註']) else ""

        card_html = (
            f'<div class="asset-card">'
            f'<div class="color-tag" style="background-color: {c};"></div>'
            f'<div class="card-content">'
            f'<div>'
            f'<div class="title-text">{row["項目"]}</div>'
            f'<div class="sub-text">持有：{q_txt}<br>{row["類別"]} · {note}</div>'
            f'</div>'
            f'<div class="price-text">NT$ {amt:,.0f}</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

except Exception as e:
    st.error(f"數據讀取失敗，請檢查權限或網址。錯誤細節：{e}")
