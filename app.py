import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 页面配置
st.set_page_config(page_title="指挥部云端版", layout="centered")
st.title("🤺 训练指挥部 (云端版)")

# 2. 建立连接 (获取实时数据)
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 奖金计算逻辑
def get_reward(score):
    if score >= 100: return "🏆 完美状态", 200.0
    if score >= 90:  return "🌟 出色状态", 88.88
    if score >= 60:  return "✅ 合格状态", 10.0
    return "💪 加油呀", 0.0

# 4. 初始化 SessionState (实现实时点击)
if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []

status, money = get_reward(st.session_state.score)

# 5. 顶部看板
c1, c2 = st.columns(2)
c1.metric("今日总分", f"{st.session_state.score} Pts")
c2.metric("预计奖金", f"¥{money}")
st.info(f"状态评价：{status}")

# 6. 任务打卡区
st.divider()
st.subheader("🎯 任务选择")
tasks = {"没有玩游戏": 20, "10:30前睡觉": 10, "完成作业": 5, "如厕不看手机": 2, "拉伸/复盘": 2}
cols = st.columns(2)
for i, (name, p) in enumerate(tasks.items()):
    if cols[i%2].button(f"{name} +{p}", use_container_width=True):
        st.session_state.score += p
        st.session_state.details.append(name)
        st.rerun()

# 7. 撤销按钮
if st.session_state.details:
    if st.button("🔙 撤销上一条", type="secondary"):
        last_item = st.session_state.details.pop()
        st.session_state.score -= tasks.get(last_item, 0)
        st.rerun()

# 8. 身体数据输入
st.divider()
st.subheader("🩺 身体数据")
col_w, col_h = st.columns(2)
w_in = col_w.text_input("体重 (kg)", placeholder="例: 55.5")
h_in = col_h.text_input("心率 (bpm)", placeholder="例: 65")

# 9. 同步到 Google 表格
if st.button("🚀 确认并同步到云端表格", type="primary", use_container_width=True):
    if st.session_state.score > 0:
        # 获取旧数据
        df_old = conn.read(ttl=0)
        # 构造符合您表头的新行
        new_row = pd.DataFrame([{
            "日期": datetime.now().strftime("%Y-%m-%d"),
            "项目明细": " | ".join(st.session_state.details),
            "项目分值": st.session_state.score,
            "当日总分": st.session_state.score,
            "当日奖金": money,
            "体重": w_in,
            "心率": h_in
        }])
        # 合并并上传
        df_updated = pd.concat([df_old, new_row], ignore_index=True)
        conn.update(data=df_updated)
        
        st.balloons()
        st.success("同步成功！")
        # 重置今日
        st.session_state.score = 0
        st.session_state.details = []
    else:
        st.warning("请先打卡记分。")

# 10. 历史预览
st.divider()
st.subheader("📊 历史记录查询")
df_view = conn.read(ttl=0)
if not df_view.empty:
    st.dataframe(df_view.sort_values("日期", ascending=False), use_container_width=True, hide_index=True)        if c2.button("🗑️ 清空今日记录", use_container_width=True):
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
