import streamlit as st
import pandas as pd
from datetime import datetime
import json
from streamlit_gsheets import GSheetsConnection

# --- 1. 页面配置与样式 ---
st.set_page_config(page_title="训练指挥部", page_icon="🤺", layout="centered")

# 模拟 App 的大字样式
st.markdown("""
    <style>
    .main-score { font-size: 70px !important; font-weight: 900; color: #1E1E1E; text-align: center; margin: 0; }
    .status-text { font-size: 20px; color: #FF4B4B; text-align: center; font-weight: bold; }
    .money-text { background-color: #FFF5F0; padding: 10px; border-radius: 10px; text-align: center; color: #FF4B4B; font-weight: bold; }
    </style>
    """, unsafe_allow_view_decode=True)

# --- 2. 核心逻辑：奖金计算 (对齐 SwiftUI calculateStatus) ---
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

# --- 4. 初始化 Session State (对齐 AppStorage) ---
if "today_logs" not in st.session_state: st.session_state.today_logs = []
if "total_score" not in st.session_state: st.session_state.total_score = 0
if "undo_stack" not in st.session_state: st.session_state.undo_stack = []
if "task_list" not in st.session_state: 
    # 默认任务清单 (对齐 App 初始值)
    st.session_state.task_list = [
        {"name": "没有玩游戏", "points": 20},
        {"name": "10:30 前睡觉", "points": 10},
        {"name": "完成 1 项作业", "points": 5},
        {"name": "如厕没看手机", "points": 2},
        {"name": "训练/比赛后拉伸", "points": 2}
    ]

# --- 5. 侧边栏：设置与补录 ---
with st.sidebar:
    st.title("⚙️ 指挥部设置")
    # 日期补录 (对齐需求)
    selected_date = st.date_input("记录日期", datetime.now())
    
    st.divider()
    st.subheader("📋 管理日常任务")
    for i, task in enumerate(st.session_state.task_list):
        cols = st.columns([3, 1])
        st.session_state.task_list[i]["name"] = cols[0].text_input(f"任务{i}", task["name"], label_visibility="collapsed")
        st.session_state.task_list[i]["points"] = cols[1].number_input(f"分{i}", value=task["points"], label_visibility="collapsed")
    
    if st.button("➕ 增加一行新任务"):
        st.session_state.task_list.append({"name": "新任务", "points": 5})
        st.rerun()

# --- 6. 主界面 ---
# 顶部统计信息
cloud_df = get_cloud_data()
total_lifetime_money = cloud_df["当日奖金"].astype(float).sum() if not cloud_df.empty else 0.0
completed_days = len(cloud_df["日期"].unique()) + 1

col_a, col_b = st.columns(2)
col_a.metric("坚持记录", f"第 {completed_days} 天")
col_b.metric("总累计奖金", f"¥{total_lifetime_money:.2f}")

st.divider()

# 中间大分数显示
status_str, current_money = calculate_status(st.session_state.total_score)
st.markdown(f'<p class="status-text">{status_str}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="main-score">{st.session_state.total_score}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="money-text">今日预计奖金：¥{current_money:.2f}</p>', unsafe_allow_html=True)

# 撤销按钮 (对齐 SwiftUI undoLastStep)
col_undo, _ = st.columns([1, 4])
if col_undo.button("🔙 撤销", use_container_width=True, disabled=not st.session_state.undo_stack):
    if st.session_state.undo_stack:
        last_state = st.session_state.undo_stack.pop()
        st.session_state.total_score = last_state["score"]
        st.session_state.today_logs = last_state["logs"]
        st.rerun()

# --- 7. 任务清单 (点击加分) ---
st.subheader("日常任务清单")
cols = st.columns(2)
for i, option in enumerate(st.session_state.task_list):
    if cols[i % 2].button(f"{option['name']} +{option['points']}", use_container_width=True):
        # 保存撤销状态
        st.session_state.undo_stack.append({
            "score": st.session_state.total_score,
            "logs": st.session_state.today_logs.copy()
        })
        # 更新数据
        st.session_state.total_score += option['points']
        st.session_state.today_logs.append({
            "name": option['name'],
            "points": option['points'],
            "time": datetime.now().strftime("%H:%M")
        })
        st.rerun()

# --- 8. 身体数据 ---
st.divider()
st.subheader("🩺 身体数据")
c1, c2 = st.columns(2)
weight = c1.text_input("体重 (kg)", key="w_val")
heart = c2.text_input("心率 (bpm)", key="h_val")

# --- 9. 同步云端 (对齐 App 的 CSV 导出逻辑) ---
if st.button("🚀 确认并同步到云端表格", type="primary", use_container_width=True):
    if st.session_state.total_score >= 0:
        try:
            # 这里的逻辑完全复刻您 App 里的 generateCSV
            new_entries = []
            if not st.session_state.today_logs:
                # 即使没记项目，也存一行基础数据
                new_entries.append({
                    "日期": selected_date.strftime("%Y-%m-%d"),
                    "项目明细": "无记录",
                    "项目分值": 0,
                    "当日总分": st.session_state.total_score,
                    "当日奖金": current_money,
                    "体重": weight,
                    "心率": heart
                })
            else:
                for log in st.session_state.today_logs:
                    new_entries.append({
                        "日期": selected_date.strftime("%Y-%m-%d"),
                        "项目明细": log['name'],
                        "项目分值": log['points'],
                        "当日总分": st.session_state.total_score,
                        "当日奖金": current_money,
                        "体重": weight,
                        "心率": heart
                    })
            
            # 更新表格
            df_new = pd.DataFrame(new_entries)
            df_final = pd.concat([cloud_df, df_new], ignore_index=True)
            conn.update(data=df_final)
            
            st.balloons()
            st.success("同步成功！")
            # 重置今日
            st.session_state.total_score = 0
            st.session_state.today_logs = []
            st.session_state.undo_stack = []
        except Exception as e:
            st.error(f"同步失败: {e}")

# --- 10. 历史归档 (对齐 HistoryView) ---
st.divider()
st.subheader("📊 历史记录明细")
if not cloud_df.empty:
    st.dataframe(cloud_df.sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)
