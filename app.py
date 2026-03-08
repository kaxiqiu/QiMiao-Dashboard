import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. 配置中心 (已根据大叔提供的链接更新) ---
# 🌟 注意：这里我帮您把 pubhtml 改成了 output=csv，这样程序才能读取
READ_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaLJQbQAIk0Vp5PRD7U1JDyturObEh7PCdVTUiFKikO6BaqVoZIRIwzxYxHnvPBPa_yCHy5ErNm2xE/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwwbgupWtmk2yNwVs1DIyfsQe84ZZnvfC-LMly8caYaYos-o5Tqz8-V7kDCtGbbqs1g/exec"

# --- 2. 页面基础配置 ---
st.set_page_config(page_title="指挥部完全体", page_icon="🤺", layout="centered")

st.markdown("""
    <style>
    .main-score { font-size: 80px !important; font-weight: 900; color: #1E1E1E; text-align: center; margin-bottom: 0px; }
    .status-text { font-size: 22px; color: #FF4B4B; text-align: center; font-weight: bold; }
    .money-badge { background-color: #FFF5F0; padding: 10px; border-radius: 12px; text-align: center; color: #FF4B4B; font-weight: bold; border: 1px solid #FFD8C2; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心逻辑 ---
def calculate_status(score):
    if score >= 100: return "🏆 完美状态", 200.0
    if score >= 90: return "🌟 出色状态", 88.88
    if score >= 60: return "✅ 合格状态", 10.0
    return "💪 加油呀", 0.0

if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []
if "undo_stack" not in st.session_state: st.session_state.undo_stack = []

# --- 4. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 管理面板")
    selected_date = st.date_input("记录日期", datetime.now())
    if st.button("🔄 强制刷新数据"):
        st.cache_data.clear()
        st.rerun()

# --- 5. 主看板 ---
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

# --- 6. 任务打卡区 ---
st.divider()
st.subheader("🎯 任务选择")
tasks = {"没有玩游戏": 20, "10:30前睡觉": 10, "实战复盘": 5, "作业/阅读": 5, "拉伸放松": 2}
cols = st.columns(2)
for i, (name, p) in enumerate(tasks.items()):
    if cols[i % 2].button(f"{name} +{p}", use_container_width=True):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += p
        st.session_state.details.append(name)
        st.rerun()

# --- 7. 身体数据 ---
st.divider()
cw, ch = st.columns(2)
weight = cw.text_input("体重 (kg)", placeholder="55.0")
heart = ch.text_input("心率 (bpm)", placeholder="60")

# --- 8. 同步逻辑 (写入) ---
if st.button("🚀 确认并同步到云端表格", type="primary", use_container_width=True):
    payload = {
        "日期": selected_date.strftime("%Y-%m-%d"),
        "项目明细": " | ".join(st.session_state.details) if st.session_state.details else "无记录",
        "项目分值": st.session_state.score,
        "当日总分": st.session_state.score,
        "当日奖金": reward_val,
        "体重": weight,
        "心率": heart
    }
    try:
        response = requests.post(SCRIPT_URL, json=payload, timeout=10)
        st.balloons()
        st.success("同步成功！")
        st.session_state.score = 0
        st.session_state.details = []
        st.session_state.undo_stack = []
        st.rerun()
    except Exception as e:
        st.error(f"同步失败: {e}")

# --- 9. 历史记录 (读取) ---
st.divider()
st.subheader("📊 历史记录预览")
try:
    df = pd.read_csv(READ_URL)
    # 强制将日期转为日期格式以便排序
    df['日期'] = pd.to_datetime(df['日期']).dt.date
    st.dataframe(df.sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)
except Exception as e:
    st.info("读取历史记录中... 若长时间未出数据，请确认表格已‘发布为CSV’")            "score": st.session_state.score,
            "logs": st.session_state.details.copy()
        })
        st.session_state.score += p
        st.session_state.details.append(name)
        st.rerun()

# --- 7. 身体数据输入 ---
st.divider()
st.subheader("🩺 身体数据")
cw, ch = st.columns(2)
weight = cw.text_input("体重 (kg)", placeholder="55.0")
heart = ch.text_input("心率 (bpm)", placeholder="60")

# --- 8. 同步逻辑 (修正了报错的字典构造) ---
if st.button("🚀 确认并同步到表格", type="primary", use_container_width=True):
    if "这里填入" in SCRIPT_URL:
        st.error("大叔，您还没填入 Script URL 哦！")
    else:
        # 构造数据包 (严格对应您的 7 列)
        payload = {
            "日期": selected_date.strftime("%Y-%m-%d"),
            "项目明细": " | ".join(st.session_state.details) if st.session_state.details else "无记录",
            "项目分值": st.session_state.score,
            "当日总分": st.session_state.score,
            "当日奖金": reward_val,
            "体重": weight,
            "心率": heart
        }
        
        try:
            response = requests.post(SCRIPT_URL, json=payload, timeout=10)
            st.balloons()
            st.success("同步成功！数据已存入表格。")
            # 重置今日
            st.session_state.score = 0
            st.session_state.details = []
            st.session_state.undo_stack = []
        except Exception as e:
            st.error(f"同步失败: {e}")

# --- 9. 历史记录 (读 CSV 方案) ---
st.divider()
st.subheader("📊 历史记录预览")
if "这里填入" in READ_URL:
    st.info("请在代码顶部填入发布的 CSV 链接来查看历史数据。")
else:
    try:
        df = pd.read_csv(READ_URL)
        if not df.empty:
            st.dataframe(df.sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)
    except:
        st.info("暂时无法读取历史记录，请确认已发布到网络并选择了 CSV 格式。")            res = requests.post(SCRIPT_URL, json=payload, timeout=10)
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
