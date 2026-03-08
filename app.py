import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 基础配置 ---
st.set_page_config(page_title="奇妙训练指挥部", page_icon="🤺", layout="centered")

# --- 2. 建立实时连接 (ttl=0 解决“数据不出”的关键) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_full_data():
    # 强制不使用缓存，每次刷新都去抓云端最新的
    df = conn.read(ttl=0)
    # 清理表头可能的空格
    df.columns = [c.strip() for c in df.columns]
    return df

# --- 3. 初始化 Session (实现实时计分和撤销) ---
if "today_score" not in st.session_state:
    st.session_state.today_score = 0
if "today_logs" not in st.session_state:
    st.session_state.today_logs = []

# --- 4. 奖金逻辑 (完全对齐 App) ---
def get_reward_info(score):
    if score >= 100: return "🏆 最好的糖糖", 200.0
    if score >= 90:  return "🌟 出色的糖糖", 88.88
    if score >= 60:  return "✅ 合格的糖糖", 10.0
    return "💪 加油呀", 0.0

# --- 5. 顶部实时看板 ---
status_text, money = get_reward_info(st.session_state.today_score)

st.title("🤺 训练数字化指挥部")
m1, m2 = st.columns(2)
m1.metric("今日积分", f"{st.session_state.today_score} Pts")
m2.metric("当前奖金", f"¥{money}")
st.write(f"**评价：** {status_text}")

# --- 6. 核心：打卡任务区 ---
st.divider()
st.subheader("🎯 任务快速打卡")
tasks = {
    "没有玩游戏": 20, "10:30前睡觉": 10, 
    "完成作业": 5, "复盘比赛": 2, 
    "如厕不看手机": 2, "训练拉伸": 2
}

cols = st.columns(2)
for i, (name, pts) in enumerate(tasks.items()):
    btn_col = cols[i % 2]
    if btn_col.button(f"{name} +{pts}", use_container_width=True):
        st.session_state.today_score += pts
        st.session_state.today_logs.append({"项目": name, "分值": pts, "时间": datetime.now().strftime("%H:%M")})
        st.rerun()

# --- 7. 今日明细与管理 ---
if st.session_state.today_logs:
    with st.expander("📝 查看今日已录明细", expanded=True):
        st.table(pd.DataFrame(st.session_state.today_logs))
        c1, c2 = st.columns(2)
        if c1.button("🔙 撤销上一条", use_container_width=True):
            last = st.session_state.today_logs.pop()
            st.session_state.today_score -= last['分值']
            st.rerun()
        if c2.button("🗑️ 清空今日记录", use_container_width=True):
            st.session_state.today_score = 0
            st.session_state.today_logs = []
            st.rerun()

# --- 8. 身体数据与同步 ---
st.divider()
st.subheader("🩺 身体数据录入")
cw, ch = st.columns(2)
weight_val = cw.text_input("体重 (kg)", placeholder="55.5")
heart_val = ch.text_input("心率 (bpm)", placeholder="60")

if st.button("🚀 确认并同步到云端表格", type="primary", use_container_width=True):
    if st.session_state.today_score > 0:
        # ⚠️ 这里必须匹配您之前导出 CSV 的列名 ⚠️
        new_row = {
            "日期": datetime.now().strftime("%Y-%m-%d"),
            "得分": st.session_state.today_score,
            "奖金": money,
            "体重": weight_val,
            "心率": heart_val
        }
        try:
            old_df = load_full_data()
            updated_df = pd.concat([old_df, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(data=updated_df)
            st.balloons()
            st.success("🎉 数据已成功同步到云端！")
            st.session_state.today_score = 0
            st.session_state.today_logs = []
        except Exception as e:
            st.error(f"同步失败: {e}")
    else:
        st.warning("请先打卡后再提交。")

# --- 9. 历史归档预览 (直接显示，解决数据看不见的问题) ---
st.divider()
st.subheader("📊 历史记录预览")
try:
    history_df = load_full_data()
    if not history_df.empty:
        # 按照日期倒序排列，让最新的在最上面
        st.dataframe(
            history_df.sort_values(by="日期", ascending=False), 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("目前的云端表格没有数据。")
except:
    st.warning("连接表格失败，请检查 Google Sheets 权限或表头是否包含：日期,得分,奖金,体重,心率")
