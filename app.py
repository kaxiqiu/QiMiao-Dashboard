import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. 配置中心 (请务必把您的链接填在引号里) ---
READ_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaLJQbQAIk0Vp5PRD7U1JDyturObEh7PCdVTUiFKikO6BaqVoZIRIwzxYxHnvPBPa_yCHy5ErNm2xE/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwwbgupWtmk2yNwVs1DIyfsQe84ZZnvfC-LMly8caYaYos-o5Tqz8-V7kDCtGbbqs1g/exec"

st.set_page_config(page_title="指挥部完全体", page_icon="🤺")

# --- 2. 报错自检逻辑 ---
def check_urls():
    if "这里填入" in READ_URL or "这里填入" in SCRIPT_URL:
        st.warning("⚠️ 大叔，您还没把代码顶部的两个 URL 换成您自己的链接哦！")
        return False
    return True

# --- 3. 样式与初始化 ---
st.markdown("<style>.main-score { font-size: 80px; font-weight: 900; text-align: center; }</style>", unsafe_allow_html=True)
if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []

# --- 4. 主界面渲染 ---
st.title("🤺 训练指挥部")

if check_urls():
    # 奖金逻辑
    def get_reward(s):
        if s >= 100: return "🏆 完美状态", 200.0
        if s >= 90: return "🌟 出色状态", 88.88
        if s >= 60: return "✅ 合格状态", 10.0
        return "💪 加油呀", 0.0

    status, money = get_reward(st.session_state.score)
    
    # 看板
    st.markdown(f'<p style="text-align:center;color:red;font-weight:bold;">{status}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="main-score">{st.session_state.score}</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;">今日奖金：¥{money}</p>', unsafe_allow_html=True)

    # 任务打卡
    st.divider()
    tasks = {"没有玩游戏": 20, "10:30前睡觉": 10, "实战复盘": 5, "作业/阅读": 5}
    cols = st.columns(2)
    for i, (name, p) in enumerate(tasks.items()):
        if cols[i%2].button(f"{name} +{p}", use_container_width=True):
            st.session_state.score += p
            st.session_state.details.append(name)
            st.rerun()

    # 身体数据与同步
    st.divider()
    w = st.text_input("体重 (kg)")
    h = st.text_input("心率 (bpm)")

    if st.button("🚀 同步到云端表格", type="primary", use_container_width=True):
        payload = {
            "日期": datetime.now().strftime("%Y-%m-%d"),
            "项目明细": " | ".join(st.session_state.details) if st.session_state.details else "无记录",
            "项目分值": st.session_state.score,
            "当日总分": st.session_state.score,
            "当日奖金": money,
            "体重": w,
            "心率": h
        }
        try:
            res = requests.post(SCRIPT_URL, json=payload, timeout=10)
            st.success("同步成功！数据已飞往表格。")
            st.session_state.score = 0
            st.session_state.details = []
        except Exception as e:
            st.error(f"同步失败: {e}")

    # 历史记录展示
    st.divider()
    st.subheader("📊 历史记录明细")
    try:
        # 强制不使用缓存读取 CSV
        df = pd.read_csv(READ_URL)
        if not df.empty:
            st.dataframe(df.sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)
    except:
        st.info("暂时无法读取历史数据，请确认您的 CSV 链接是否正确发布。")        "项目分值": st.session_state.score,
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
