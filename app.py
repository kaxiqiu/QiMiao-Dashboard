import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. 配置中心 ---
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
# 动态任务清单状态
if "custom_tasks" not in st.session_state:
    st.session_state.custom_tasks = [
        {"name": "没有玩游戏", "points": 20},
        {"name": "10:30前睡觉", "points": 10},
        {"name": "实战复盘", "points": 5},
        {"name": "如厕不看手机", "points": 2}
    ]

# --- 5. 侧边栏：管理与补录 ---
with st.sidebar:
    st.title("⚙️ 指挥部管理")
    selected_date = st.date_input("记录日期", datetime.now())
    
    st.divider()
    st.subheader("➕ 自行添加新任务")
    new_task_name = st.text_input("任务名称", placeholder="如：手部专项训练")
    new_task_pts = st.number_input("奖励积分", min_value=0, value=5)
    if st.button("将此项加入打卡清单", use_container_width=True):
        if new_task_name:
            st.session_state.custom_tasks.append({"name": new_task_name, "points": new_task_pts})
            st.success(f"已添加：{new_task_name}")
            st.rerun()

    st.divider()
    if st.button("🔄 强制刷新云端数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- 6. 顶部统计 (累积奖金逻辑) ---
try:
    df_raw = pd.read_csv(READ_URL)
    df_raw['日期'] = pd.to_datetime(df_raw['日期']).dt.date
    # 算法：按日期去重取当日奖金，再求和
    lifetime_money = df_raw.groupby('日期')['当日奖金'].first().sum()
    completed_days = len(df_raw['日期'].unique()) + 1
except:
    lifetime_money = 0.0
    completed_days = 1

c_stat1, c_stat2 = st.columns(2)
c_stat1.metric("已坚持记录", f"第 {completed_days} 天")
c_stat2.metric("总累计奖金", f"¥{lifetime_money:.2f}")

st.divider()

# --- 7. 主看板 ---
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

# --- 8. 任务打卡区 (动态生成) ---
st.divider()
st.subheader("🎯 任务打卡清单")
cols = st.columns(2)
for i, task in enumerate(st.session_state.custom_tasks):
    if cols[i % 2].button(f"{task['name']} +{task['points']}", key=f"t_{i}", use_container_width=True):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += task['points']
        st.session_state.details.append(f"{task['name']}(+{task['points']})")
        st.rerun()

# --- 9. 🚀 新增：当日手机时间结算 ---
st.divider()
st.subheader("📱 当日手机时间结算")
col_phone1, col_phone2 = st.columns([3, 1])
phone_time = col_phone1.text_input("今日手机总时长/备注", placeholder="如：1小时20分")
if col_phone2.button("记录时长", use_container_width=True):
    if phone_time:
        st.session_state.details.append(f"手机结算: {phone_time}")
        st.toast(f"已记录手机时长: {phone_time}")

# --- 10. 身体数据 ---
st.divider()
st.subheader("🩺 身体数据")
cw, ch = st.columns(2)
weight = cw.text_input("体重 (kg)", placeholder="55.0")
heart = ch.text_input("心率 (bpm)", placeholder="60")

# --- 11. 同步与结算 ---
if st.button("🚀 确认并同步到云端表格", type="primary", use_container_width=True):
    # 构造数据包
    date_str = selected_date.strftime("%Y-%m-%d")
    if not st.session_state.details:
        payloads = [{"日期": date_str, "项目明细": "无记录", "项目分值": 0, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": weight, "心率": heart}]
    else:
        # 将每一项明细拆分为一行发送
        payloads = []
        for d in st.session_state.details:
            # 提取分值（简单逻辑：如果明细里带+号，提取数字）
            pts = 0
            if "(+" in d:
                try: pts = int(d.split("(+")[1].split(")")[0])
                except: pts = 0
            
            payloads.append({
                "日期": date_str,
                "项目明细": d,
                "项目分值": pts,
                "当日总分": st.session_state.score,
                "当日奖金": reward_val,
                "体重": weight,
                "心率": heart
            })

    try:
        with st.spinner('正在同步数据...'):
            for item in payloads:
                requests.post(SCRIPT_URL, json=item, timeout=10)
        
        st.balloons()
        st.success("当日结算完成！")
        # 重置当前状态 (对齐 App 结算)
        st.session_state.score = 0
        st.session_state.details = []
        st.session_state.undo_stack = []
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"同步失败: {e}")

# --- 12. 历史记录预览 ---
st.divider()
st.subheader("📊 历史记录查询")
try:
    df_display = pd.read_csv(READ_URL)
    df_display['日期'] = pd.to_datetime(df_display['日期']).dt.date
    st.dataframe(df_display.sort_values(by=["日期"], ascending=False), use_container_width=True, hide_index=True)
except:
    st.info("读取历史记录中...")
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
