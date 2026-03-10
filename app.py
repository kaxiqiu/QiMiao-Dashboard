import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. 配置中心 ---
READ_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaLJQbQAIk0Vp5PRD7U1JDyturObEh7PCdVTUiFKikO6BaqVoZIRIwzxYxHnvPBPa_yCHy5ErNm2xE/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwwbgupWtmk2yNwVs1DIyfsQe84ZZnvfC-LMly8caYaYos-o5Tqz8-V7kDCtGbbqs1g/exec"

# --- 2. 深度定制 CSS ---
st.set_page_config(page_title="训练指挥部", page_icon="🤺", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* 强力屏蔽所有 Streamlit 侧边栏按钮和图标 */
    [data-testid="stSidebarCollapsedControl"], .st-emotion-cache-6qob1r, span[data-testid="stIconMaterial"] {
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
    
    /* 统一按钮样式，防止图标文字溢出 */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        border: none;
        background-color: white;
        color: #000;
        padding: 12px 15px;
        text-align: center;
        font-weight: 500;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    /* 打卡按钮左对齐 */
    .task-btn button { text-align: left !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 初始化状态 ---
if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []
if "undo_stack" not in st.session_state: st.session_state.undo_stack = []
if "show_log" not in st.session_state: st.session_state.show_log = False
if "show_settings" not in st.session_state: st.session_state.show_settings = False
if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {"name": "没有玩游戏", "points": 20},
        {"name": "10:30前睡觉", "points": 10},
        {"name": "实战复盘", "points": 5},
        {"name": "如厕不看手机", "points": 2}
    ]

# --- 4. 顶部统计 ---
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

# --- 5. 核心计分中心 ---
status_str, reward_val = (calculate_status := lambda s: ("🏆 最好的状态", 200.0) if s >= 100 else ("🌟 出色的状态", 88.88) if s >= 90 else ("✅ 合格的状态", 10.0) if s >= 60 else ("💪 加油呀", 0.0))(st.session_state.score)
st.markdown(f"""
<div class="ios-card" style="text-align: center;">
    <div class="status-badge">{status_str}</div>
    <div class="score-val">{st.session_state.score}</div>
    <div class="money-label">今日预计奖金：¥{reward_val:.2f}</div>
</div>
""", unsafe_allow_html=True)

# --- 6. 功能按键区 (手动切换逻辑，彻底避开 expand_more) ---
c1, c2, c3 = st.columns(3)
if c1.button("📅 补录"): 
    st.session_state.show_log = not st.session_state.show_log
    st.session_state.show_settings = False
if c2.button("🔙 撤销"):
    if st.session_state.undo_stack:
        last = st.session_state.undo_stack.pop()
        st.session_state.score, st.session_state.details = last["score"], last["logs"]
        st.rerun()
if c3.button("⚙️ 设置"): 
    st.session_state.show_settings = not st.session_state.show_settings
    st.session_state.show_log = False

# 补录面板
if st.session_state.show_log:
    with st.container():
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        st.write("📅 选择补录日期")
        record_date = st.date_input("日期", datetime.now(), label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    record_date = datetime.now()

# 设置面板
if st.session_state.show_settings:
    with st.container():
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        st.write("⚙️ 新增日常任务")
        new_name = st.text_input("任务名称", key="new_name")
        new_pts = st.number_input("积分", min_value=0, value=5, key="new_pts")
        if st.button("➕ 确认添加项"):
            if new_name:
                st.session_state.tasks.append({"name": new_name, "points": new_pts})
                st.session_state.show_settings = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 打卡任务清单 ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 10px 5px;">日常任务清单</p>', unsafe_allow_html=True)
for i, task in enumerate(st.session_state.tasks):
    st.markdown('<div class="task-btn">', unsafe_allow_html=True)
    if st.button(f" {task['name']} 　　　　　　　　　　　　　 +{task['points']}", key=f"t_{i}"):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += task['points']
        st.session_state.details.append(f"{task['name']}(+{task['points']})")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. 手机时长结算 ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 20px 5px 10px;">📱 手机时间结算 (分钟)</p>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    p_min = st.number_input("时长", min_value=0, value=120, step=5, label_visibility="collapsed")
    p_pts = 20 + ((120 - p_min) // 5)
    st.write(f"💡 结算积 **{p_pts}** 分 (120min基准)")
    if st.button("确认记录手机得分", key="p_btn"):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += p_pts
        st.session_state.details.append(f"手机结算({p_min}min): {p_pts}分")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 9. 同步结算 ---
if st.button("🚀 确认结算并同步到云端", type="primary"):
    d_str = record_date.strftime("%Y-%m-%d")
    payloads = []
    if not st.session_state.details:
        payloads.append({"日期": d_str, "项目明细": "无记录", "项目分值": 0, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": "0", "心率": "0"})
    else:
        for d in st.session_state.details:
            pts = 0
            if "(+" in d: pts = int(d.split("(+")[1].split(")")[0])
            elif "分" in d and ": " in d: pts = int(d.split(": ")[1].replace("分", ""))
            payloads.append({"日期": d_str, "项目明细": d, "项目分值": pts, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": "0", "心率": "0"})

    try:
        with st.spinner('同步中...'):
            for item in payloads: requests.post(SCRIPT_URL, json=item, timeout=10)
        st.balloons(); st.success("结算成功！"); st.session_state.score = 0; st.session_state.details = []; st.session_state.undo_stack = []; st.cache_data.clear(); st.rerun()
    except Exception as e: st.error(f"同步失败: {e}")

# --- 10. 历史 ---
with st.expander("📊 查看历史明细"):
    try:
        df_v = pd.read_csv(READ_URL)
        st.dataframe(df_view := df_v.sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)
    except: st.info("历史记录载入中...")
