import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. 配置中心 ---
READ_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaLJQbQAIk0Vp5PRD7U1JDyturObEh7PCdVTUiFKikO6BaqVoZIRIwzxYxHnvPBPa_yCHy5ErNm2xE/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwwbgupWtmk2yNwVs1DIyfsQe84ZZnvfC-LMly8caYaYos-o5Tqz8-V7kDCtGbbqs1g/exec"

# --- 2. 铁律 CSS (彻底解决居中与手机端横排) ---
st.set_page_config(page_title="训练指挥部", page_icon="🤺", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* 强力屏蔽冗余 */
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], span[data-testid="stIconMaterial"] { display: none !important; }
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    
    /* 核心卡片容器 */
    .ios-box {
        background-color: white;
        border-radius: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        padding: 20px 12px;
        margin-bottom: 15px;
        text-align: center;
    }

    /* 积分居中：锁定坐标 */
    .score-display {
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .score-val { font-size: 85px !important; font-weight: 800; color: #000; line-height: 1; margin: 10px 0; }
    .status-badge { font-size: 15px; color: #FF9500; font-weight: 700; }
    .money-label { font-size: 14px; color: #FF3B30; font-weight: 600; background: #FFF1F0; padding: 6px 15px; border-radius: 10px; display: inline-block; }

    /* 核心铁律：强制 4 列横排，绝不换行 */
    [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important;
        gap: 4px !important;
        width: 100% !important;
    }
    [data-testid="column"] {
        width: 100% !important;
        min-width: 0px !important;
    }

    /* 管理工具按钮微型化 */
    .stButton > button, .stPopover > button {
        width: 100% !important;
        padding: 8px 0 !important;
        font-size: 11px !important;
        border-radius: 10px !important;
        background-color: #F2F2F7 !important;
        border: none !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
    }

    /* 任务清单按钮左对齐 */
    .task-list-btn button { text-align: left !important; padding: 12px 15px !important; background-color: white !important; font-size: 15px !important; box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 逻辑初始化 ---
if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []
if "undo_stack" not in st.session_state: st.session_state.undo_stack = []
if "tasks" not in st.session_state:
    st.session_state.tasks = [{"name": "没有玩游戏", "points": 20}, {"name": "10:30前睡觉", "points": 10}, {"name": "实战复盘", "points": 5}, {"name": "阅读/作业", "points": 5}, {"name": "如厕不看手机", "points": 2}]

# --- 4. 顶部统计 ---
try:
    df_raw = pd.read_csv(READ_URL); df_raw['日期'] = pd.to_datetime(df_raw['日期']).dt.date
    lifetime_money = df_raw.groupby('日期')['当日奖金'].first().sum()
    completed_days = len(df_raw['日期'].unique()) + 1
except:
    lifetime_money = 0.0; completed_days = 1

st.markdown(f"""
<div style="background: white; padding: 12px; border-radius: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 12px; display: flex; justify-content: space-between;">
    <div><span style="font-size:11px; color:#8E8E93;">已坚持记录</span><br><span style="font-size:16px; color:#34C759; font-weight:700;">第 {completed_days} 天</span></div>
    <div style="text-align: right;"><span style="font-size:11px; color:#8E8E93;">总累计奖金</span><br><span style="font-size:17px; color:#FF3B30; font-weight:700;">¥{lifetime_money:.2f}</span></div>
</div>
""", unsafe_allow_html=True)

# --- 🚀 5. 核心：大看板 (纯净版) ---
today_label = datetime.now().strftime("%Y-%m-%d")
status_str, reward_val = (lambda s: ("🏆 最好的状态", 200.0) if s >= 100 else ("🌟 出色的状态", 88.88) if s >= 90 else ("✅ 合格的状态", 10.0) if s >= 60 else ("💪 加油呀", 0.0))(st.session_state.score)

st.markdown(f"""
<div class="ios-box">
    <div class="score-display">
        <div class="status-badge">{status_str} <span style="font-weight:400; color:#8E8E93;">| {today_label}</span></div>
        <div class="score-val">{st.session_state.score}</div>
        <div class="money-label">预计奖金：¥{reward_val:.2f}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 6. 📱 手机时长结算 ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 15px 5px 5px;">📱 手机时长 (120min基准)</p>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div style="background:white; padding:15px; border-radius:15px; box-shadow:0 1px 3px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
    p_min = st.number_input("分钟", min_value=0, value=120, step=5, label_visibility="collapsed")
    p_pts = 20 + ((120 - p_min) // 5)
    st.write(f"💡 结算积分：**{p_pts}** 分")
    if st.button("确认记录手机时长", key="p_btn"):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += p_pts; st.session_state.details.append(f"手机结算({p_min}min): {p_pts}分"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 打卡任务清单 ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 15px 5px 5px;">🎯 任务打卡清单</p>', unsafe_allow_html=True)
for i, task in enumerate(st.session_state.tasks):
    st.markdown('<div class="task-list-btn">', unsafe_allow_html=True)
    if st.button(f" {task['name']} 　　　　　　　　　　　　　 +{task['points']}", key=f"t_{i}"):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += task['points']; st.session_state.details.append(f"{task['name']}(+{task['points']})"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 🚀 8. 核心变动：管理工具栏挪到日常任务下面 ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 20px 5px 5px;">🛠️ 指挥部管理工具</p>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("🔙撤销"):
        if st.session_state.undo_stack:
            last = st.session_state.undo_stack.pop()
            st.session_state.score, st.session_state.details = last["score"], last["logs"]; st.rerun()
with c2:
    with st.popover("📅补录"):
        rec_date = st.date_input("补录日期", datetime.now(), label_visibility="collapsed")
if 'rec_date' not in locals(): rec_date = datetime.now()
with c3:
    if st.button("🧹清除"):
        st.session_state.score = 0; st.session_state.details = []; st.session_state.undo_stack = []; st.rerun()
with c4:
    with st.popover("⚙️新增任务"):
        n_name = st.text_input("任务名称", placeholder="如：体能特训")
        n_pts = st.number_input("积分奖励", min_value=0, value=5)
        is_daily = st.checkbox("存入日常清单", value=True)
        if st.button("🚀 确认添加"):
            if n_name:
                st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
                st.session_state.score += n_pts; st.session_state.details.append(f"{n_name}(+{n_pts})")
                if is_daily: st.session_state.tasks.append({"name": n_name, "points": n_pts})
                st.rerun()

# --- 9. 身体数据 ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 15px 5px 5px;">🩺 身体数据</p>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div style="background:white; padding:15px; border-radius:15px; box-shadow:0 1px 3px rgba(0,0,0,0.1); display:flex; gap:10px;">', unsafe_allow_html=True)
    cw, ch = st.columns(2)
    weight = cw.text_input("体重", placeholder="kg", label_visibility="collapsed")
    heart = ch.text_input("心率", placeholder="bpm", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 10. 同步与结算 ---
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚀 确认结算并同步到云端", type="primary"):
    d_str = rec_date.strftime("%Y-%m-%d")
    payloads = []
    if not st.session_state.details:
        payloads.append({"日期": d_str, "项目明细": "无记录", "项目分值": 0, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": weight, "心率": heart})
    else:
        for d in st.session_state.details:
            pts = 0
            try:
                if "(+" in d: pts = int(d.split("(+")[1].split(")")[0])
                elif ": " in d: pts = int(d.split(": ")[1].replace("分", ""))
            except: pts = 0
            payloads.append({"日期": d_str, "项目明细": d, "项目分值": pts, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": weight, "心率": heart})
    try:
        with st.spinner('同步中...'):
            for item in payloads: requests.post(SCRIPT_URL, json=item, timeout=10)
        st.balloons(); st.success("已存档！"); st.session_state.score = 0; st.session_state.details = []; st.session_state.undo_stack = []; st.cache_data.clear(); st.rerun()
    except Exception as e: st.error(f"同步失败: {e}")

with st.expander("📊 查看历史明细"):
    try:
        df_v = pd.read_csv(READ_URL); st.dataframe(df_v.sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)
    except: st.info("历史载入中...")
