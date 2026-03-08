import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 页面基础配置
st.set_page_config(page_title="指挥部云端版", layout="centered")
st.title("🤺 训练指挥部 (云端版)")

# 2. 建立连接 (设置 0 秒缓存，确保数据实时)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    df = conn.read(ttl=0)
    # 清理表头空格
    df.columns = [c.strip() for c in df.columns]
    return df

# 3. 奖金计算逻辑 (完全对齐 App)
def get_reward(score):
    if score >= 100: return "🏆 完美状态", 200.0
    if score >= 90:  return "🌟 出色状态", 88.88
    if score >= 60:  return "✅ 合格状态", 10.0
    return "💪 加油呀", 0.0

# 4. 初始化今日积分和明细
if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []

status, money = get_reward(st.session_state.score)

# 5. 顶部实时计分板
c1, c2 = st.columns(2)
c1.metric("今日积分", f"{st.session_state.score} Pts")
c2.metric("预计奖金", f"¥{money}")
st.info(f"状态评价：{status}")

# 6. 任务打卡区
st.divider()
st.subheader("🎯 任务快速选择")
tasks = {"没有玩游戏": 20, "10:30前睡觉": 10, "完成作业": 5, "如厕不看手机": 2, "拉伸/复盘": 2}
cols = st.columns(2)
for i, (name, p) in enumerate(tasks.items()):
    if cols[i%2].button(f"{name} +{p}", use_container_width=True):
        st.session_state.score += p
        st.session_state.details.append(name)
        st.rerun()

# 7. 今日明细管理 (解决“撤销”和“清空”)
if st.session_state.details:
    with st.expander("📝 查看今日已选明细", expanded=True):
        st.write("已选项目：" + " | ".join(st.session_state.details))
        col_undo, col_clear = st.columns(2)
        if col_undo.button("🔙 撤销上一条", use_container_width=True):
            if st.session_state.details:
                last_item = st.session_state.details.pop()
                st.session_state.score -= tasks.get(last_item, 0)
                st.rerun()
        if col_clear.button("🗑️ 清空今日记录", use_container_width=True):
            st.session_state.score = 0
            st.session_state.details = []
            st.rerun()

# 8. 身体数据输入
st.divider()
st.subheader("🩺 身体数据")
col_w, col_h = st.columns(2)
w_in = col_w.text_input("体重 (kg)", placeholder="例: 55.5")
h_in = col_h.text_input("心率 (bpm)", placeholder="例: 65")

# 9. 同步到 Google 表格 (精准匹配 7 列)
if st.button("🚀 确认并同步到云端表格", type="primary", use_container_width=True):
    if st.session_state.score > 0:
        try:
            df_old = load_data()
            # 🌟 这里的名字必须和您表格第一行一模一样 🌟
            new_row = pd.DataFrame([{
                "日期": datetime.now().strftime("%Y-%m-%d"),
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
            st.success("数据已成功同步！")
            st.session_state.score = 0
            st.session_state.details = []
            st.rerun()
        except Exception as e:
            st.error(f"同步失败，请确认表格表头名是否正确: {e}")
    else:
        st.warning("请先记录分数再提交。")

# 10. 历史记录预览 (放在最下面)
st.divider()
st.subheader("📊 历史归档预览")
try:
    df_view = load_data()
    if not df_view.empty:
        st.dataframe(df_view.sort_values("日期", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("云端目前没有数据。")
except:
    st.warning("暂时无法读取历史记录，请确认 Secrets 里的表格链接。")
