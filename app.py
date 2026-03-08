import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. 配置中心 (大叔请填入您的两个专属链接) ---
# 填入第一步“发布到网络”拿到的那个 CSV 链接
READ_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaLJQbQAIk0Vp5PRD7U1JDyturObEh7PCdVTUiFKikO6BaqVoZIRIwzxYxHnvPBPa_yCHy5ErNm2xE/pub?gid=0&single=true&output=csv" 
# 填入您之前在“App 脚本”部署拿到的那个 Web 应用 URL
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwwbgupWtmk2yNwVs1DIyfsQe84ZZnvfC-LMly8caYaYos-o5Tqz8-V7kDCtGbbqs1g/exec" 

st.set_page_config(page_title="指挥部完全体", page_icon="🤺", layout="centered")

# --- 2. 样式与状态初始化 ---
st.markdown("""<style>.main-score { font-size: 80px; font-weight: 900; text-align: center; color: #333; }</style>""", unsafe_allow_html=True)

if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []

def calculate_status(score):
    if score >= 100: return "🏆 完美状态", 200.0
    if score >= 90: return "🌟 出色状态", 88.88
    if score >= 60: return "✅ 合格状态", 10.0
    return "💪 加油呀", 0.0

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 管理面板")
    selected_date = st.date_input("记录日期", datetime.now())
    if st.button("🔄 刷新历史数据"):
        st.cache_data.clear()
        st.rerun()

# --- 4. 主看板 ---
status, money = calculate_status(st.session_state.score)
st.markdown(f'<p style="text-align:center;color:#FF4B4B;font-weight:bold;font-size:20px;">{status}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="main-score">{st.session_state.score}</p>', unsafe_allow_html=True)
st.markdown(f'<p style="text-align:center;background:#F0F2F6;padding:10px;border-radius:10px;">今日奖金：¥{money}</p>', unsafe_allow_html=True)

# --- 5. 任务打卡 (大按钮) ---
st.divider()
tasks = {"没有玩游戏": 20, "10:30前睡觉": 10, "实战复盘": 5, "作业/阅读": 5, "如厕不看手机": 2}
cols = st.columns(2)
for i, (name, p) in enumerate(tasks.items()):
    if cols[i%2].button(f"{name} +{p}", use_container_width=True):
        st.session_state.score += p
        st.session_state.details.append(name)
        st.rerun()

# 撤销按钮
if st.session_state.details:
    if st.button("🔙 撤销上一条", use_container_width=True):
        last = st.session_state.details.pop()
        st.session_state.score -= tasks.get(last, 0)
        st.rerun()

# --- 6. 身体数据 ---
st.divider()
cw, ch = st.columns(2)
weight = cw.text_input("体重 (kg)", placeholder="55.0")
heart = ch.text_input("心率 (bpm)", placeholder="65")

# --- 7. 同步逻辑 (通过脚本写入) ---
if st.button("🚀 确认并同步到表格", type="primary", use_container_width=True):
    payload = {
        "日期": selected_date.strftime("%Y-%m-%d"),
        "项目明细": " | ".join(st.session_state.details) if st.session_state.details else "无记录",
        "项目分值": st.session_state.score,
        "当日总分": st.session_state.score,
        "当日奖金": money,
        "体重": weight,
        "心率": heart
    }
    try:
        # 发送数据
        response = requests.post(SCRIPT_URL, json=payload, timeout=10)
        st.balloons()
        st.success("同步成功！数据已飞往云端表格。")
        st.session_state.score = 0
        st.session_state.details = []
    except Exception as e:
        st.error(f"同步失败，请检查脚本URL: {e}")

# --- 8. 历史记录 (直接读取 CSV，不再报错) ---
st.divider()
st.subheader("📊 历史记录明细")
try:
    # 强制加上缓存控制，防止读取旧数据
    history_df = pd.read_csv(READ_URL)
    if not history_df.empty:
        st.dataframe(history_df.sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)
except:
    st.info("暂时还没看到历史数据，快去同步第一条吧！")
