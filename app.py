import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- 1. 基础配置与数据持久化 ---
st.set_page_config(page_title="奇妙的自管-数字化指挥部", layout="wide")

# 数据文件路径（保存在当前文件夹）
DATA_FILE = "qimiao_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "rewards": [
            {"name": "没有玩游戏", "points": 20},
            {"name": "10:30 前睡觉", "points": 10},
            {"name": "做了一件之前做不到的事", "points": 5},
            {"name": "训练/比赛后拉伸", "points": 2},
            {"name": "如厕没看手机", "points": 2},
            {"name": "仔细复盘比赛", "points": 2},
            {"name": "看书 100 页", "points": 1},
            {"name": "完成 1 项作业", "points": 1}
        ],
        "today_logs": [],
        "health_data": {"weight": "", "heart_rate": "", "burned": "", "intake": ""},
        "last_reset": datetime.now().strftime("%Y-%m-%d")
    }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.store, f, ensure_ascii=False, indent=4)

# 初始化 Session State
if 'store' not in st.session_state:
    st.session_state.store = load_data()

# --- 2. 核心逻辑函数 ---
def calculate_status(score):
    if score >= 100: return "最好的糖糖", 200.0
    if score >= 95: return "完美的糖糖", 100.0
    if score >= 90: return "出色的糖糖", 88.88
    if score >= 80: return "优秀的糖糖", 66.66
    if score >= 70: return "进阶的糖糖", 20.0
    if score >= 60: return "合格的糖糖", 10.0
    return "加油呀", 0.0

def add_entry(name, points):
    entry = {
        "id": datetime.now().timestamp(),
        "时间": datetime.now().strftime("%H:%M:%S"),
        "任务": name,
        "得分": points
    }
    st.session_state.store["today_logs"].insert(0, entry)
    save_data()

# --- 3. 侧边栏：身体数据管理 ---
with st.sidebar:
    st.title("📊 身体数据")
    date_str = datetime.now().strftime("%Y-%m-%d")
    st.info(f"今天是：{date_str}")
    
    # 获取现有数据
    h = st.session_state.store["health_data"]
    weight = st.text_input("体重 (kg)", value=h.get("weight", ""))
    hr = st.text_input("静心心率 (bpm)", value=h.get("heart_rate", ""))
    burned = st.text_input("运动消耗 (kcal)", value=h.get("burned", ""))
    intake = st.text_input("摄入热量 (kcal)", value=h.get("intake", ""))
    
    if st.button("💾 保存身体数据"):
        st.session_state.store["health_data"] = {
            "weight": weight, "heart_rate": hr, "burned": burned, "intake": intake
        }
        save_data()
        st.success("身体数据已存档！")
        
    st.divider()
    st.subheader("⚙️ 任务清单管理")
    new_task_name = st.text_input("新增固定任务名")
    new_task_pts = st.number_input("设定分值", value=1)
    if st.button("➕ 加入固定清单"):
        if new_task_name:
            st.session_state.store["rewards"].append({"name": new_task_name, "points": new_task_pts})
            save_data()
            st.rerun()

# --- 4. 主界面：仪表盘 ---
st.title("🛡️ 奇妙的自管 - 数字化指挥部")

# 计算总分
today_total = sum(item['得分'] for item in st.session_state.store["today_logs"])
status_name, money = calculate_status(today_total)

# 顶部三张卡片
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("今日累计总分", f"{today_total} 分")
with col2:
    st.metric("当前状态评估", status_name)
with col3:
    st.metric("预计今日奖金", f"¥ {money}")

st.divider()

# --- 5. 核心功能区：左右分栏 ---
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("✅ 日常任务（点击加分）")
    # 动态生成按钮布局
    reward_cols = st.columns(3)
    for idx, r in enumerate(st.session_state.store["rewards"]):
        with reward_cols[idx % 3]:
            if st.button(f"{r['name']} +{r['points']}", key=f"btn_{idx}", use_container_width=True):
                add_entry(r['name'], r['points'])
                st.rerun()
    
    st.divider()
    st.subheader("📝 自定义补录")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        custom_name = st.text_input("任务名称", placeholder="比如：洗车、帮邻居...", key="custom_n")
    with c2:
        custom_pts = st.number_input("分值", value=5, key="custom_p")
    with c3:
        st.write(" ") # 对齐
        if st.button("快速存入", use_container_width=True):
            if custom_name:
                add_entry(custom_name, custom_pts)
                st.rerun()

with right_col:
    st.subheader("📱 手机时间结算")
    phone_mins = st.number_input("今日使用分钟", value=120, step=10)
    if st.button("一键结算手机分", use_container_width=True):
        earned = 20 + ((120 - phone_mins) // 10) * 2
        add_entry(f"手机结算 ({phone_mins}min)", earned)
        st.rerun()
    
    st.divider()
    st.subheader("🕒 最近记录")
    if st.session_state.store["today_logs"]:
        # 显示最近的5条记录
        recent_df = pd.DataFrame(st.session_state.store["today_logs"]).head(10)
        st.dataframe(recent_df[["时间", "任务", "得分"]], hide_index=True)
        if st.button("⚠️ 撤销最近一条"):
            if st.session_state.store["today_logs"]:
                st.session_state.store["today_logs"].pop(0)
                save_data()
                st.rerun()
    else:
        st.info("暂无记录")

# --- 6. 底部数据看板 ---
st.divider()
with st.expander("📊 查看今日完整明细"):
    if st.session_state.store["today_logs"]:
        full_df = pd.DataFrame(st.session_state.store["today_logs"])
        st.table(full_df[["时间", "任务", "得分"]])
    else:
        st.write("还没有数据哦~")

if st.button("🗑️ 清空今日数据 (谨慎!)"):
    st.session_state.store["today_logs"] = []
    save_data()
    st.rerun()