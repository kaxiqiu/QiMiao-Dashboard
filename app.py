import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. 配置中心 (电缆接通) ---
READ_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaLJQbQAIk0Vp5PRD7U1JDyturObEh7PCdVTUiFKikO6BaqVoZIRIwzxYxHnvPBPa_yCHy5ErNm2xE/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwwbgupWtmk2yNwVs1DIyfsQe84ZZnvfC-LMly8caYaYos-o5Tqz8-V7kDCtGbbqs1g/exec"

# --- 2. 页面配置与大字样式 ---
st.set_page_config(page_title="训练指挥部", page_icon="🤺", layout="centered")

st.markdown("""
    <style>
    .main-score { font-size: 80px !important; font-weight: 900; color: #1E1E1E; text-align: center; margin-bottom: 0px; }
    .status-text { font-size: 22px; color: #FF4B4B; text-align: center; font-weight: bold; }
    .money-badge { background-color: #FFF5F0; padding: 10px; border-radius: 12px; text-align: center; color: #FF4B4B; font-weight: bold; border: 1px solid #FFD8C2; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心算法 (完全对齐 SwiftUI 逻辑) ---
def calculate_status(score):
    if score >= 100: return "最好的状态", 200.0
    if score >= 90: return "出色的状态", 88.88
    if score >= 60: return "合格的状态", 10.0
    return "加油呀", 0.0

# 初始化 Session 状态
if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []
if "undo_stack" not in st.session_state: st.session_state.undo_stack = []

# --- 4. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 管理面板")
    selected_date = st.date_input("记录日期", datetime.now())
    if st.button("🔄 强制刷新云端数据"):
        st.cache_data.clear()
        st.rerun()

# --- 5. 顶部统计 (累积奖金与天数逻辑修正) ---
try:
    # 预先读取云端数据进行计算
    df_raw = pd.read_csv(READ_URL)
    df_raw['日期'] = pd.to_datetime(df_raw['日期']).dt.date
    
    # 算法修正：先按日期分组取每天的第一行奖金，再求和，防止重复计算明细奖金
    lifetime_money = df_raw.groupby('日期')['当日奖金'].first().sum()
    # 坚持天数 = 历史去重天数 + 1
    completed_days = len(df_raw['日期'].unique()) + 1
except:
    lifetime_money = 0.0
    completed_days = 1

c_stat1, c_stat2 = st.columns(2)
c_stat1.metric("已坚持记录", f"第 {completed_days} 天")
c_stat2.metric("总累计奖金", f"¥{lifetime_money:.2f}")

st.divider()

# --- 6. 主看板 ---
status_str, reward_val = calculate_status(st.session_state.score)
st.markdown(f'<p class="status-text">{status_str}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="main-score">{st.session_state.score}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="money-badge">今日预计奖金：¥{reward_val}</p>', unsafe_allow_html=True)

# 撤销按钮
col_undo, _ = st.columns([1, 4])
if col_undo.button("🔙 撤销", disabled=not st.session_state.undo_stack):
    last_state = st.session_state.undo_stack.pop()
    st.session_state.score = last_state["score"]
    st.session_state.details = last_state["logs"]
    st.rerun()

# --- 7. 任务打卡区 ---
st.divider()
st.subheader("🎯 任务打卡")
tasks = {"没有玩游戏": 20, "10:30前睡觉": 10, "实战复盘": 5, "作业/阅读": 5, "拉伸放松": 2, "如厕不看手机": 2}
cols = st.columns(2)
for i, (name, p) in enumerate(tasks.items()):
    if cols[i % 2].button(f"{name} +{p}", key=f"btn_{i}", use_container_width=True):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += p
        st.session_state.details.append(name)
        st.rerun()

# --- 8. 身体数据 ---
st.divider()
cw, ch = st.columns(2)
weight = cw.text_input("体重 (kg)", placeholder="55.0")
heart = ch.text_input("心率 (bpm)", placeholder="60")

# --- 9. 同步与当日结算 (写入) ---
if st.button("🚀 确认并同步到云端表格", type="primary", use_container_width=True):
    # 构造数据包 (对齐 generateCSV 逻辑)
    if not st.session_state.details:
        # 即使没打卡也生成一行空记录
        payloads = [{
            "日期": selected_date.strftime("%Y-%m-%d"),
            "项目明细": "无记录",
            "项目分值": 0,
            "当日总分": st.session_state.score,
            "当日奖金": reward_val,
            "体重": weight,
            "心率": heart
        }]
    else:
        payloads = [{
            "日期": selected_date.strftime("%Y-%m-%d"),
            "项目明细": task_name,
            "项目分值": tasks.get(task_name, 0),
            "当日总分": st.session_state.score,
            "当日奖金": reward_val,
            "体重": weight,
            "心率": heart
        } for task_name in st.session_state.details]

    try:
        # 逐条发送或批量发送（根据您的脚本逻辑，这里演示逐条发送以确保明细完整）
        for item in payloads:
            requests.post(SCRIPT_URL, json=item, timeout=10)
        
        st.balloons()
        st.success("当日结算成功！数据已存入云端历史。")
        # 结算重置
        st.session_state.score = 0
        st.session_state.details = []
        st.session_state.undo_stack = []
        st.cache_data.clear() # 清除缓存以便立刻看到新数据
        st.rerun()
    except Exception as e:
        st.error(f"同步失败: {e}")

# --- 10. 历史记录预览 ---
st.divider()
st.subheader("📊 历史记录明细")
try:
    df_display = pd.read_csv(READ_URL)
    df_display['日期'] = pd.to_datetime(df_display['日期']).dt.date
    st.dataframe(df_display.sort_values(by=["日期", "项目明细"], ascending=[False, True]), use_container_width=True, hide_index=True)
except:
    st.info("正在读取历史记录...")
