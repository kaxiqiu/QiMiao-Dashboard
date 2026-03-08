import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 页面配置与样式 (修正了之前的参数报错) ---
st.set_page_config(page_title="训练指挥部", page_icon="🤺", layout="centered")

# 模拟 App 的大字样式和评价框
st.markdown("""
    <style>
    .main-score { font-size: 80px !important; font-weight: 900; color: #1E1E1E; text-align: center; margin-bottom: 0px; }
    .status-text { font-size: 22px; color: #FF4B4B; text-align: center; font-weight: bold; margin-top: 10px; }
    .money-badge { background-color: #FFF5F0; padding: 10px; border-radius: 12px; text-align: center; color: #FF4B4B; font-weight: bold; border: 1px solid #FFD8C2; }
    </style>
    """, unsafe_allow_html=True) # 这里已修正为正确的参数名

# --- 2. 核心逻辑：奖金计算 (完全对齐 SwiftUI) ---
def calculate_status(score):
    if score >= 100: return "最好的状态", 200.0
    if score >= 90: return "出色的状态", 88.88
    if score >= 60: return "合格的状态", 10.0
    return "加油呀", 0.0

# --- 3. 连接 Google Sheets ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_cloud_data():
    try:
        df = conn.read(ttl=0)
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame(columns=["日期", "项目明细", "项目分值", "当日总分", "当日奖金", "体重", "心率"])

# --- 4. 初始化状态 (对齐 AppStorage) ---
if "today_logs" not in st.session_state: st.session_state.today_logs = []
if "total_score" not in st.session_state: st.session_state.total_score = 0
if "undo_stack" not in st.session_state: st.session_state.undo_stack = []

# 模拟 App 的任务清单与点击计数 (用于排序)
if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {"name": "没有玩游戏", "points": 20, "clicks": 0},
        {"name": "10:30 前睡觉", "points": 10, "clicks": 0},
        {"name": "完成 1 项作业", "points": 5, "clicks": 0},
        {"name": "如厕没看手机", "points": 2, "clicks": 0},
        {"name": "训练/比赛后拉伸", "points": 2, "clicks": 0}
    ]

# --- 5. 侧边栏：补录与管理 ---
with st.sidebar:
    st.title("⚙️ 指挥部管理")
    selected_date = st.date_input("选择记录日期", datetime.now())
    
    st.divider()
    st.subheader("📋 调整任务清单")
    for i, t in enumerate(st.session_state.tasks):
        cols = st.columns([3, 1])
        st.session_state.tasks[i]["name"] = cols[0].text_input(f"项{i}", t["name"], label_visibility="collapsed")
        st.session_state.tasks[i]["points"] = cols[1].number_input(f"分{i}", value=t["points"], label_visibility="collapsed")
    
    if st.button("➕ 增加新任务项"):
        st.session_state.tasks.append({"name": "新训练项", "points": 5, "clicks": 0})
        st.rerun()

# --- 6. 主界面：看板 (对齐 SwiftUI 布局) ---
cloud_df = get_cloud_data()
lifetime_money = pd.to_numeric(cloud_df["当日奖金"], errors='coerce').sum() if not cloud_df.empty else 0.0
days_count = len(cloud_df["日期"].unique()) + 1

c_top1, c_top2 = st.columns(2)
c_top1.metric("已坚持记录", f"第 {days_count} 天")
c_top2.metric("总累计奖金", f"¥{lifetime_money:.2f}")

st.divider()

# 核心计分器
status_str, reward_val = calculate_status(st.session_state.total_score)
st.markdown(f'<p class="status-text">{status_str}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="main-score">{st.session_state.total_score}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="money-badge">今日预计奖金：¥{reward_val:.2f}</p>', unsafe_allow_html=True)

# 撤销按钮
col_undo, _ = st.columns([1, 4])
if col_undo.button("🔙 撤销", disabled=not st.session_state.undo_stack):
    last_state = st.session_state.undo_stack.pop()
    st.session_state.total_score = last_state["score"]
    st.session_state.today_logs = last_state["logs"]
    st.rerun()

# --- 7. 任务点击区 (按点击量排序，对齐 App 习惯) ---
st.subheader("日常任务打卡")
sorted_tasks = sorted(st.session_state.tasks, key=lambda x: x['clicks'], reverse=True)
cols = st.columns(2)
for i, task in enumerate(sorted_tasks):
    if cols[i % 2].button(f"{task['name']} +{task['points']}", use_container_width=True):
        # 保存撤销状态
        st.session_state.undo_stack.append({
            "score": st.session_state.total_score,
            "logs": st.session_state.today_logs.copy()
        })
        # 更新数据
        st.session_state.total_score += task['points']
        st.session_state.today_logs.append({"name": task['name'], "points": task['points']})
        # 增加点击计数
        for original_task in st.session_state.tasks:
            if original_task['name'] == task['name']: original_task['clicks'] += 1
        st.rerun()

# --- 8. 身体数据 ---
st.divider()
st.subheader("🩺 身体数据")
cw, ch = st.columns(2)
weight = cw.text_input("体重 (kg)", placeholder="55.0")
heart = ch.text_input("心率 (bpm)", placeholder="60")

# --- 9. 同步逻辑 (对齐 App 的 generateCSV 逻辑) ---
if st.button("🚀 确认并同步到云端表格", type="primary", use_container_width=True):
    try:
        new_rows = []
        date_str = selected_date.strftime("%Y-%m-%d")
        
        if not st.session_state.today_logs:
            # 即使没项目也存一行
            new_rows.append([date_str, "无记录", 0, st.session_state.total_score, reward_val, weight, heart])
        else:
            for log in st.session_state.today_logs:
                new_rows.append([date_str, log['name'], log['points'], st.session_state.total_score, reward_val, weight, heart])
        
        # 写入表格
        new_df = pd.DataFrame(new_rows, columns=["日期", "项目明细", "项目分值", "当日总分", "当日奖金", "体重", "心率"])
        updated_df = pd.concat([cloud_df, new_df], ignore_index=True)
        conn.update(data=updated_df)
        
        st.balloons()
        st.success("同步成功！")
        # 重置
        st.session_state.total_score = 0
        st.session_state.today_logs = []
        st.session_state.undo_stack = []
        st.rerun()
    except Exception as e:
        st.error(f"同步失败: {e}")

# --- 10. 历史记录预览 ---
st.divider()
st.subheader("📊 历史记录明细")
if not cloud_df.empty:
    st.dataframe(cloud_df.sort_values("日期", ascending=False), use_container_width=True, hide_index=True)
