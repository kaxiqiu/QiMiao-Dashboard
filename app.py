import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 配置 ---
st.set_page_config(page_title="指挥部完全体", layout="centered")
# 这里填入您刚才在 Google 脚本里拿到的那个 Web 应用 URL
SCRIPT_URL = "这里填入您复制的URL" 

# --- 2. 样式与逻辑 (保持和 App 一致) ---
st.markdown("""<style>.main-score { font-size: 80px; font-weight: 900; text-align: center; }</style>""", unsafe_allow_html=True)

def calculate_status(score):
    if score >= 100: return "🏆 完美状态", 200.0
    if score >= 90: return "🌟 出色状态", 88.88
    if score >= 60: return "✅ 合格状态", 10.0
    return "💪 加油呀", 0.0

if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []

# --- 3. 侧边栏 ---
with st.sidebar:
    selected_date = st.date_input("补录日期", datetime.now())
    st.info("读取数据依然使用公开链接，写入数据使用脚本。")

# --- 4. 主看板 ---
status, money = calculate_status(st.session_state.score)
st.markdown(f'<p style="text-align:center;color:red;font-weight:bold;">{status}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="main-score">{st.session_state.score}</p>', unsafe_allow_html=True)

# --- 5. 任务打卡 (大按钮) ---
tasks = {"没有玩游戏": 20, "10:30前睡觉": 10, "实战复盘": 5, "如厕不看手机": 2}
cols = st.columns(2)
for i, (name, p) in enumerate(tasks.items()):
    if cols[i%2].button(f"{name} +{p}", use_container_width=True):
        st.session_state.score += p
        st.session_state.details.append(name)
        st.rerun()

# --- 6. 身体数据 ---
st.divider()
cw, ch = st.columns(2)
w_in = cw.text_input("体重 (kg)")
h_in = ch.text_input("心率 (bpm)")

# --- 7. 🚀 核心同步逻辑 (不再需要 Service Account) ---
if st.button("🚀 确认并同步到表格", type="primary", use_container_width=True):
    if st.session_state.score >= 0:
        # 构造要发送的数据
        payload = {
            "日期": selected_date.strftime("%Y-%m-%d"),
            "项目明细": " | ".join(st.session_state.details),
            "项目分值": st.session_state.score,
            "当日总分": st.session_state.score,
            "当日奖金": money,
            "体重": w_in,
            "心率": h_in
        }
        
        try:
            # 像发短信一样把数据发给 Google 脚本
            response = requests.post(SCRIPT_URL, json=payload)
            if response.text == "OK":
                st.balloons()
                st.success("同步成功！数据已存入表格。")
                st.session_state.score = 0
                st.session_state.details = []
            else:
                st.error("同步失败，请检查脚本 URL。")
        except Exception as e:
            st.error(f"连接错误: {e}")

# --- 8. 历史预览 (依然使用只读连接) ---
st.divider()
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)
if not df.empty:
    st.dataframe(df.sort_values("日期", ascending=False), use_container_width=True, hide_index=True)
