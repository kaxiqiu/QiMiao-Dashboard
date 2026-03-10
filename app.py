import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. 配置中心 ---
READ_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaLJQbQAIk0Vp5PRD7U1JDyturObEh7PCdVTUiFKikO6BaqVoZIRIwzxYxHnvPBPa_yCHy5ErNm2xE/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwwbgupWtmk2yNwVs1DIyfsQe84ZZnvfC-LMly8caYaYos-o5Tqz8-V7kDCtGbbqs1g/exec"

# --- 2. 深度定制 iOS 样式 ---
st.set_page_config(page_title="训练指挥部", page_icon="🤺", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* 强力屏蔽侧边栏及其所有图标，防止重叠字母 */
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], span[data-testid="stIconMaterial"] {
        display: none !important;
    }
    
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    * { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif !important; }
    
    .ios-card {
        background: white;
        padding: 18px;
        border-radius: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 12px;
    }
    
    .score-val { font-size: 72px; font-weight: 800; color: #000; text-align: center; line-height: 1; margin: 5px 0; }
    .status-badge { font-size: 18px; color: #FF9500; font-weight: 700; text-align: center; }
    .money-label { font-size: 16px; color: #FF3B30; font-weight: 600; text-align: center; background: #FFF1F0; padding: 8px; border-radius: 10px; }
    
    /* 列表按钮样式 */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        border: none;
        background-color: white;
        color: #000;
        padding: 12px 15px;
        font-weight: 500;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    /* 撤销小按钮：极简图标风 */
    .undo-btn button {
        padding: 0px 5px !important;
        font-size: 18px !important;
        background-color: transparent !important;
        width: auto !important;
        float: right;
        box-shadow: none !important;
        border: none !important;
    }
    /* 任务列表左对齐 */
    .task-list-btn button { text-align: left !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心计算与状态初始化 ---
def calculate_status(score):
    if score >= 100: return "🏆 最好的状态", 200.0
    if score >= 90: return "🌟 出色的状态", 88.88
    if score >= 60: return "✅ 合格的状态", 10.0
    return "💪 加油呀", 0.0

if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []
if "undo_stack" not in st.session_state: st.session_state.undo_stack = []
if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {"name": "没有玩游戏", "points": 20},
        {"name": "10:30前睡觉", "points": 10},
        {"name": "实战复盘", "points": 5},
        {"name": "阅读/作业", "points": 5},
        {"name": "如厕不看手机", "points": 2}
    ]

# --- 4. 顶部：坚持天数与累计奖金 ---
try:
    df_raw = pd.read_csv(READ_URL)
    df_raw['日期'] = pd.to_datetime(df_raw['日期']).dt.date
    lifetime_money = df_raw.groupby('日期')['当日奖金'].first().sum()
    completed_days = len(df_raw['日期'].unique()) + 1
except:
    lifetime_money = 0.0; completed_days = 1

st.markdown(f"""
<div class="ios-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div><span style="font-size:12px; color:#8E8E93;">已坚持记录</span><br><span style="font-size:18px; color:#34C759; font-weight:700;">第 {completed_days} 天</span></div>
        <div style="text-align: right;"><span style="font-size:12px; color:#8E8E93;">总累计奖金</span><br><span style="font-size:18px; color:#FF3B30; font-weight:700;">¥{lifetime_money:.2f}</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 5. 核心：计分看板 ---
status_str, reward_val = calculate_status(st.session_state.score)
st.markdown(f"""
<div class="ios-card" style="text-align: center;">
    <div class="status-badge">{status_str}</div>
    <div class="score-val">{st.session_state.score}</div>
    <div class="money-label">今日预计奖金：¥{reward_val:.2f}</div>
</div>
""", unsafe_allow_html=True)

# --- 🚀 6. 核心优化：手机时间结算 (排在首位) ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 10px 5px;">📱 手机时间结算 (120min基准)</p>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    p_min = st.number_input("分钟", min_value=0, value=120, step=5, label_visibility="collapsed")
    p_pts = 20 + ((120 - p_min) // 5)
    st.write(f"💡 结算积 **{p_pts}** 分")
    if st.button("确认记录手机得分", key="p_btn"):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += p_pts
        st.session_state.details.append(f"手机结算({p_min}min): {p_pts}分")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 🚀 7. 核心优化：撤销图标对齐任务清单标题 ---
title_col, undo_col = st.columns([5, 1])
with title_col:
    st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 10px 5px;">🎯 日常打卡清单</p>', unsafe_allow_html=True)
with undo_col:
    st.markdown('<div class="undo-btn">', unsafe_allow_html=True)
    if st.button("🔙", disabled=not st.session_state.undo_stack, help="撤销上一条记录"):
        last = st.session_state.undo_stack.pop()
        st.session_state.score, st.session_state.details = last["score"], last["logs"]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

for i, task in enumerate(st.session_state.tasks):
    st.markdown('<div class="task-list-btn">', unsafe_allow_html=True)
    if st.button(f" {task['name']} 　　　　　　　　　　　　　 +{task['points']}", key=f"t_{i}"):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += task['points']
        st.session_state.details.append(f"{task['name']}(+{task['points']})")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. 身体数据 ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 20px 5px 10px;">🩺 身体数据</p>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    cw, ch = st.columns(2)
    weight = cw.text_input("体重", placeholder="kg")
    heart = ch.text_input("心率", placeholder="bpm")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 🚀 9. 核心优化：新增任务增加“存入日常”选项 ---
st.divider()
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin-bottom:10px;">🛠️ 指挥部管理</p>', unsafe_allow_html=True)
col_log, col_set = st.columns(2)

with col_log:
    with st.popover("📅 补录数据"):
        rec_date = st.date_input("选择日期", datetime.now(), label_visibility="collapsed")
if 'rec_date' not in locals(): rec_date = datetime.now()

with col_set:
    with st.popover("⚙️ 新增任务"):
        n_name = st.text_input("任务名称", placeholder="如：体能训练")
        n_pts = st.number_input("积分奖励", min_value=0, value=5)
        # 🌟 核心开关：是否永久加入清单
        is_daily = st.checkbox("存入日常任务清单", value=False)
        
        if st.button("🚀 确认添加", use_container_width=True):
            if n_name:
                # 无论如何先记一次分
                st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
                st.session_state.score += n_pts
                st.session_state.details.append(f"{n_name}(+{n_pts})")
                
                # 如果选了“存入日常”，则加入任务列表
                if is_daily:
                    st.session_state.tasks.append({"name": n_name, "points": n_pts})
                
                st.rerun()

# --- 10. 结算与同步 ---
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚀 确认结算并同步到云端", type="primary"):
    d_str = rec_date.strftime("%Y-%m-%d")
    payloads = []
    if not st.session_state.details:
        payloads.append({"日期": d_str, "项目明细": "无记录", "项目分值": 0, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": weight, "心率": heart})
    else:
        for d in st.session_state.details:
            pts = 0
            if "(+" in d: pts = int(d.split("(+")[1].split(")")[0])
            elif "分" in d and ": " in d: pts = int(d.split(": ")[1].replace("分", ""))
            payloads.append({"日期": d_str, "项目明细": d, "项目分值": pts, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": weight, "心率": heart})

    try:
        with st.spinner('同步中...'):
            for item in payloads: requests.post(SCRIPT_URL, json=item, timeout=10)
        st.balloons(); st.success("结算成功！"); st.session_state.score = 0; st.session_state.details = []; st.session_state.undo_stack = []; st.cache_data.clear(); st.rerun()
    except Exception as e: st.error(f"同步失败: {e}")

with st.expander("📊 查看历史明细"):
    try:
        df_v = pd.read_csv(READ_URL)
        st.dataframe(df_v.sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)
    except: st.info("历史载入中...")
