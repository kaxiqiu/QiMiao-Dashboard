import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. 配置中心 (请确认链接准确) ---
READ_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaLJQbQAIk0Vp5PRD7U1JDyturObEh7PCdVTUiFKikO6BaqVoZIRIwzxYxHnvPBPa_yCHy5ErNm2xE/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwwbgupWtmk2yNwVs1DIyfsQe84ZZnvfC-LMly8caYaYos-o5Tqz8-V7kDCtGbbqs1g/exec"

# --- 2. 页面配置与美化 ---
st.set_page_config(page_title="训练指挥部", page_icon="🤺", layout="centered")

st.markdown("""
    <style>
    .main-score { font-size: 80px !important; font-weight: 900; color: #1E1E1E; text-align: center; margin-bottom: 0px; }
    .status-text { font-size: 22px; color: #FF4B4B; text-align: center; font-weight: bold; }
    .money-badge { background-color: #FFF5F0; padding: 15px; border-radius: 12px; text-align: center; color: #FF4B4B; font-weight: bold; border: 1px solid #FFD8C2; }
    .phone-calc-box { background-color: #F0F7FF; padding: 20px; border-radius: 10px; border: 1px solid #BEE3F8; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心算法 ---
def calculate_status(score):
    if score >= 100: return "最好的状态", 200.0
    if score >= 90: return "出色的状态", 88.88
    if score >= 60: return "合格的状态", 10.0
    return "加油呀", 0.0

# --- 4. 初始化 Session 状态 (对齐 AppStorage) ---
if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []
if "undo_stack" not in st.session_state: st.session_state.undo_stack = []
if "custom_tasks" not in st.session_state:
    st.session_state.custom_tasks = [
        {"name": "没有玩游戏", "points": 20},
        {"name": "10:30前睡觉", "points": 10},
        {"name": "实战复盘", "points": 5},
        {"name": "作业/阅读", "points": 5},
        {"name": "拉伸放松", "points": 2}
    ]

# --- 5. 侧边栏：自行添加任务 ---
with st.sidebar:
    st.title("⚙️ 指挥部管理")
    selected_date = st.date_input("记录日期", datetime.now())
    
    st.divider()
    st.subheader("➕ 添加新任务")
    new_task_name = st.text_input("任务名称", placeholder="如：体能加练")
    new_task_pts = st.number_input("奖励积分", min_value=0, value=5)
    if st.button("将此项加入打卡清单", use_container_width=True):
        if new_task_name:
            st.session_state.custom_tasks.append({"name": new_task_name, "points": new_task_pts})
            st.rerun()

    st.divider()
    if st.button("🔄 强制刷新历史数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- 6. 顶部看板：累积奖金与天数 (读取云端) ---
try:
    df_raw = pd.read_csv(READ_URL)
    df_raw['日期'] = pd.to_datetime(df_raw['日期']).dt.date
    # 累积奖金算法：每天只计入第一次结算的奖金
    lifetime_money = df_raw.groupby('日期')['当日奖金'].first().sum()
    completed_days = len(df_raw['日期'].unique()) + 1
except:
    lifetime_money = 0.0
    completed_days = 1

c_stat1, c_stat2 = st.columns(2)
c_stat1.metric("已坚持记录", f"第 {completed_days} 天")
c_stat2.metric("总累计奖金", f"¥{lifetime_money:.2f}")

st.divider()

# --- 7. 主分数显示 ---
status_str, reward_val = calculate_status(st.session_state.score)
st.markdown(f'<p class="status-text">{status_str}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="main-score">{st.session_state.score}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="money-badge">今日预计奖金：¥{reward_val}</p>', unsafe_allow_html=True)

# 撤销功能
if st.button("🔙 撤销上一条记录", disabled=not st.session_state.undo_stack):
    last_state = st.session_state.undo_stack.pop()
    st.session_state.score = last_state["score"]
    st.session_state.details = last_state["logs"]
    st.rerun()

# --- 8. 任务打卡区 (动态生成) ---
st.divider()
st.subheader("🎯 常规项目打卡")
cols = st.columns(2)
for i, task in enumerate(st.session_state.custom_tasks):
    if cols[i % 2].button(f"{task['name']} +{task['points']}", key=f"t_{i}", use_container_width=True):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += task['points']
        st.session_state.details.append(f"{task['name']}(+{task['points']})")
        st.rerun()

# --- 9. 📱 手机时间结算逻辑 (大叔专属规则) ---
st.divider()
st.subheader("📱 手机时间自动结算")
with st.container():
    st.markdown('<div class="phone-calc-box">', unsafe_allow_html=True)
    phone_min = st.number_input("今日手机使用时长 (分钟)", min_value=0, value=120, step=5)
    
    # 规则：120min=20分，每少5min +1分，每多5min -1分
    # 积分 = 20 + (120 - 实际时长) / 5
    diff = 120 - phone_min
    calc_points = 20 + (diff // 5)
    
    st.write(f"📊 **计算结果**：{phone_min}分钟 → **结算积分为 {calc_points} 分**")
    
    if st.button("确认并记录手机得分", use_container_width=True):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += calc_points
        st.session_state.details.append(f"手机结算({phone_min}min): {calc_points}分")
        st.toast(f"手机得分 {calc_points} 已计入总分")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 10. 身体数据 ---
st.divider()
st.subheader("🩺 身体数据")
cw, ch = st.columns(2)
weight = cw.text_input("体重 (kg)", placeholder="55.0")
heart = ch.text_input("心率 (bpm)", placeholder="60")

# --- 11. 🚀 同步结算 (确认并清零今日) ---
if st.button("🚀 确认结算并同步到表格", type="primary", use_container_width=True):
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # 构造发送给 Google 的明细列表
    if not st.session_state.details:
        payloads = [{"日期": date_str, "项目明细": "无记录", "项目分值": 0, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": weight, "心率": heart}]
    else:
        payloads = []
        for d in st.session_state.details:
            # 提取明细中的分值
            pts = 0
            try:
                if "(+" in d: pts = int(d.split("(+")[1].split(")")[0])
                elif ": " in d: pts = int(d.split(": ")[1].replace("分", ""))
            except: pts = 0
            
            payloads.append({
                "日期": date_label if 'date_label' in locals() else date_str,
                "项目明细": d,
                "项目分值": pts,
                "当日总分": st.session_state.score,
                "当日奖金": reward_val,
                "体重": weight,
                "心率": heart
            })

    try:
        with st.spinner('正在同步至云端...'):
            for item in payloads:
                requests.post(SCRIPT_URL, json=item, timeout=10)
        
        st.balloons()
        st.success("结算成功！今日分数已存入云端，记录已清零。")
        # 彻底清零 (对齐手机 App 结算逻辑)
        st.session_state.score = 0
        st.session_state.details = []
        st.session_state.undo_stack = []
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"同步失败，请检查网络或脚本链接: {e}")

# --- 12. 历史展示 (读取 CSV) ---
st.divider()
st.subheader("📊 历史记录查询")
try:
    df_display = pd.read_csv(READ_URL)
    st.dataframe(df_display.sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)
except:
    st.info("读取历史数据中...")
