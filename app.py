import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 頁面基本設定
st.set_page_config(page_title="My Finance", page_icon="💰", layout="centered")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# --- 2. iPhone 鎖定畫面 (解決按鈕排版問題) ---
if not st.session_state["authenticated"]:
    # 這裡設定你的密碼
    CORRECT_PASS = "1234" 

    # 隱藏 Streamlit 預設元件，改用自定義 UI
    iphone_ui_html = f"""
    <div id="lock-screen" style="font-family: -apple-system, sans-serif; text-align: center; padding: 20px; background-color: #F2F2F7; height: 100vh;">
        <h2 style="margin-top: 50px; color: #1C1C1E;">輸入密碼</h2>
        <div id="dots" style="font-size: 30px; letter-spacing: 15px; color: #8E8E93; margin: 30px 0;">○○○○</div>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; max-width: 300px; margin: 0 auto;">
            <button class="key" onclick="press('1')">1</button>
            <button class="key" onclick="press('2')">2</button>
            <button class="key" onclick="press('3')">3</button>
            <button class="key" onclick="press('4')">4</button>
            <button class="key" onclick="press('5')">5</button>
            <button class="key" onclick="press('6')">6</button>
            <button class="key" onclick="press('7')">7</button>
            <button class="key" onclick="press('8')">8</button>
            <button class="key" onclick="press('9')">9</button>
            <button class="key" style="background:none; border:none; font-size:16px;" onclick="reset()">清除</button>
            <button class="key" onclick="press('0')">0</button>
            <button class="key" style="background:#007AFF; color:white; border:none; font-size:16px;" onclick="submit()">確定</button>
        </div>
    </div>

    <style>
        .key {{
            height: 70px; background: white; border: 1px solid #E5E5EA;
            border-radius: 15px; font-size: 24px; font-weight: 600;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            display: flex; align-items: center; justify-content: center;
            cursor: pointer;
        }}
        .key:active {{ background: #E5E5EA; }}
    </style>

    <script>
        let code = "";
        function press(n) {{
            if (code.length < 4) {{
                code += n;
                updateDots();
            }}
        }}
        function updateDots() {{
            let dotsStr = "●".repeat(code.length) + "○".repeat(4 - code.length);
            document.getElementById('dots').innerText = dotsStr;
        }}
        function reset() {{
            code = "";
            updateDots();
        }}
        function submit() {{
            if (code === "{CORRECT_PASS}") {{
                // 透過 window.parent 發送指令給 Streamlit
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: true}}, '*');
            }} else {{
                alert("密碼錯誤");
                reset();
            }}
        }}
    </script>
    """
    
    # 接收來自 HTML 的認證成功訊息
    # 注意：此處使用一個隱藏的 text_input 作為橋樑，或簡單使用 query_params
    auth = st.query_params.get("login")
    if auth == "success":
        st.session_state["authenticated"] = True
        st.rerun()

    # 由於 postMessage 較複雜，這裡我們用更簡單的「隱藏密碼輸入框」方案
    # 這次我們強制調整 CSS，確保 st.columns 在手機上絕對不換行
    st.markdown("""
        <style>
        [data-testid="column"] { flex: 1 !important; min-width: 80px !important; }
        div.stButton > button { height: 80px; font-size: 24px; border-radius: 20px; }
        [data-testid="stHeader"] { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align: center;'>輸入密碼</h2>", unsafe_allow_html=True)
    
    # 數字鍵盤核心佈局
    for row in [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]:
        cols = st.columns(3)
        for i, key in enumerate(row):
            if cols[i].button(key, key=f"btn_{key}"):
                st.session_state["auth_code"] = st.session_state.get("auth_code", "") + key
                st.rerun()

    cols_b = st.columns(3)
    if cols_b[0].button("清除"): st.session_state["auth_code"] = ""; st.rerun()
    if cols_b[1].button("0"): st.session_state["auth_code"] = st.session_state.get("auth_code", "") + "0"; st.rerun()
    
    st.write(f"<h1 style='text-align:center;'>{'●' * len(st.session_state.get('auth_code',''))}</h1>", unsafe_allow_html=True)

    if st.button("登入 🔒", type="primary", use_container_width=True):
        if st.session_state.get("auth_code") == CORRECT_PASS:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("密碼錯誤")
            st.session_state["auth_code"] = ""
    st.stop()

# --- 3. 資產清單 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1f0XezXO1hq7vrLw_w0C7SC5UzM_MF-9KU6fGLJiyGwc/edit?usp=sharing", ttl=0)
    st.success("解鎖成功，歡迎回來！")
    st.dataframe(df)
except:
    st.error("連線異常")
