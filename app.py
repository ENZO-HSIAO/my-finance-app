import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# --- 2. 密碼解鎖 UI (使用 HTML Table 強制排版) ---
if not st.session_state["authenticated"]:
    # 設定密碼
    CORRECT_PASS = "1234" 

    # 這裡放一個真正的 Streamlit 輸入框，但把它藏起來
    # 這是為了讓 JS 可以把值傳回給 Streamlit
    password_input = st.text_input("隱藏輸入", type="password", key="real_pass", label_visibility="collapsed")

    if password_input == CORRECT_PASS:
        st.session_state["authenticated"] = True
        st.rerun()
    elif len(password_input) >= 4:
        st.error("密碼錯誤")
        # 清除輸入框需要一點技巧，這裡簡單處理

    # 核心：使用 HTML Table 繪製 3x4 鍵盤
    keyboard_html = """
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh; font-family: -apple-system, sans-serif;">
        <h2 style="color: #1c1c1e; margin-bottom: 40px;">請輸入密碼</h2>
        
        <table style="border-spacing: 15px; border-collapse: separate;">
            <tr>
                <td><button class="key" onclick="press('1')">1</button></td>
                <td><button class="key" onclick="press('2')">2</button></td>
                <td><button class="key" onclick="press('3')">3</button></td>
            </tr>
            <tr>
                <td><button class="key" onclick="press('4')">4</button></td>
                <td><button class="key" onclick="press('5')">5</button></td>
                <td><button class="key" onclick="press('6')">6</button></td>
            </tr>
            <tr>
                <td><button class="key" onclick="press('7')">7</button></td>
                <td><button class="key" onclick="press('8')">8</button></td>
                <td><button class="key" onclick="press('9')">9</button></td>
            </tr>
            <tr>
                <td><button class="key-func" onclick="clearAll()">清除</button></td>
                <td><button class="key" onclick="press('0')">0</button></td>
                <td><button class="key-func" style="background: #007AFF; color: white;" onclick="login()">登入</button></td>
            </tr>
        </table>
    </div>

    <style>
        .key, .key-func {
            width: 80px; height: 80px; border-radius: 50%;
            border: 1px solid #e5e5ea; background: white;
            font-size: 28px; font-weight: 500; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            transition: background 0.1s; -webkit-tap-highlight-color: transparent;
        }
        .key-func { font-size: 16px; border-radius: 15px; }
        .key:active, .key-func:active { background: #d1d1d6; }
    </style>

    <script>
        let currentPass = "";
        function press(num) {
            if (currentPass.length < 4) {
                currentPass += num;
            }
        }
        function clearAll() {
            currentPass = "";
        }
        function login() {
            // 找到 Streamlit 的原生輸入框並填值
            const inputs = window.parent.document.querySelectorAll('input[type="password"]');
            if (inputs.length > 0) {
                const nativeInput = inputs[0];
                nativeInput.value = currentPass;
                // 觸發輸入事件讓 Streamlit 偵測到變化
                nativeInput.dispatchEvent(new Event('input', { bubbles: true }));
                nativeInput.dispatchEvent(new Event('change', { bubbles: true }));
                // 模擬按下 Enter
                nativeInput.dispatchEvent(new KeyboardEvent('keydown', { 'key': 'Enter', 'bubbles': true }));
            }
        }
    </script>
    """
    st.components.v1.html(keyboard_html, height=600)
    st.stop()

# --- 3. 資產清單 ---
st.markdown("<h2 style='margin-top:20px;'>💰 資產總覽</h2>", unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing", ttl=0)
    
    # 這裡顯示你的資產卡片邏輯
    st.dataframe(df, use_container_width=True)
except:
    st.info("連線中...")
