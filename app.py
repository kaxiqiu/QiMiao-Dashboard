import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 页面配置
st.set_page_config(page_title="指挥部完全体", layout="centered")
st.title("🤺 训练指挥部 (网页专业版)")

# 2. 建立连接
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(ttl=0)
        df.columns = [c.strip() for c in df.columns] # 强制清理表头空格
        return df
    except Exception as e:
        st.error(f"连接云端失败，请检查 Secrets 配置或表格表头: {e}")
        return pd.DataFrame()

# 3. 奖金逻辑
def get_reward(score):
    if score >= 100: return "🏆 完美状态", 200.0
    if score >= 90:  return "🌟 出色状态", 88.88
    if score >= 60:  return "✅ 合格状态", 10.0
    return "💪 加油呀", 0.0

# 4. 初始化状态
if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []

# --- 🚀 新增功能：日期选择 (支持补录) ---
st.sidebar.header("📅 日历补录")
record_date = st.sidebar.date_input("选择记录日期", value=datetime.now())
formatted_date = record_date.strftime("%Y-%m-%d")

# 5. 顶部看板
status, money = get_reward(st.session_state.score)
c1, c2 = st.columns(2)
c1.metric("当前积分", f"{st.session_state.score} Pts")
c2.metric("预计奖金", f"¥{money}")

# 6. 任务选择 (常规项目)
st.divider()
st.subheader("🎯 常规训练项打卡")
tasks = {"没有玩游戏": 20, "10:30前睡觉": 10, "实战复盘": 5, "基础拉伸": 2, "如厕不看手机": 2}
cols = st.columns(2)
for i, (name, p) in enumerate(tasks.items()):
    if cols[i%2].button(f"{name} +{p}", use_container_width=True):
        st.session_state.score += p
        st.session_state.details.append(name)
        st.rerun()

# --- 🚀 新增功能：添加临时/常规项目 ---
with st.expander("➕ 添加自定义任务"):
    new_task = st.text_input("任务名称", placeholder="如：手部专项训练")
    new_pts = st.number_input("奖励分值", min_value=1, value=5)
    if st.button("记录该项"):
        if new_task:
            st.session_state.score += new_pts
            st.session_state.details.append(new_task)
            st.success(f"已录入: {new_task}")
            st.rerun()

# 7. 管理操作
if st.session_state.details:
    st.info("今日已选: " + " | ".join(st.session_state.details))
    col_undo, col_clear = st.columns(2)
    if col_undo.button("🔙 撤销上一条"):
        if st.session_state.details:
            st.session_state.details.pop() # 网页版暂不扣分，建议直接清空重录
            st.warning("已撤销，建议调整后重新提交")
    if col_clear.button("🗑️ 清空重来"):
        st.session_state.score = 0
        st.session_state.details = []
        st.rerun()

# 8. 身体数据
st.divider()
st.subheader("🩺 身体数据")
col_w, col_h = st.columns(2)
w_in = col_w.text_input("体重 (kg)")
h_in = col_h.text_input("心率 (bpm)")

# 9. 同步云端 (严格匹配大叔的 7 列)
if st.button("🚀 确认并同步到云端表格", type="primary", use_container_width=True):
    if st.session_state.score >= 0:
        try:
            df_old = load_data()
            new_row = pd.DataFrame([{
                "日期": formatted_date, # 使用侧边栏选定的日期
                "项目明细": " | ".join(st.session_state.details),
                "项目分值": st.session_state.score,
                "当日总分": st.session_state.score,
                "当日奖金": money,
                "体重": w_in,
                "心率": h_in
            }])
            df_updated = pd.concat([df_old, new_row], ignore_index=True)
            conn.update(data=df_updated)
            st.balloons()
            st.success(f"已成功同步至 {formatted_date} 的记录！")
            st.session_state.score = 0
            st.session_state.details = []
        except Exception as e:
            st.error(f"同步失败: {e}")

# 10. 历史归档查询
st.divider()
st.subheader("📊 历史数据查询")
df_view = load_data()
if not df_view.empty:
    st.dataframe(df_view.sort_values("日期", ascending=False), use_container_width=True, hide_index=True)
