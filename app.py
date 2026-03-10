import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. 配置中心 ---
READ_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaLJQbQAIk0Vp5PRD7U1JDyturObEh7PCdVTUiFKikO6BaqVoZIRIwzxYxHnvPBPa_yCHy5ErNm2xE/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwwbgupWtmk2yNwVs1DIyfsQe84ZZnvfC-LMly8caYaYos-o5Tqz8-V7kDCtGbbqs1g/exec"

# --- 2. iOS 深度美化 CSS ---
st.set_page_config(page_title="训练指挥部", page_icon="🤺", layout="centered")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    * { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif !important; }
    
    .ios-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 12px;
    }
    
    .score-val { font-size: 72px; font-weight: 800; color: #000; text-align: center; line-height: 1; margin: 10px 0; }
    .status-badge { font-size: 18px; color: #FF9500; font-weight: 700; text-align: center; }
    .money-label { font-size: 16px; color: #FF3B30; font-weight: 600; text-align: center; background: #FFF1F0; padding: 8px; border-radius: 10px; }
    
    .stat-label { font-size: 12px; color: #8E8E93; }
    .stat-val-green { font-size: 18px; color: #34C759; font-weight: 700; }
    .stat-val-red { font-size: 18px; color: #FF3B30; font-weight: 700; }
    
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        border: none;
        background-color: white;
        color: #000;
        padding: 12px 15px;
        text-align: left;
        font-weight: 500;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .stButton > button:hover { background-color: #E5E5EA; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心算法 ---
def calculate_status(score):
    if score >= 100: return "🏆 最好的状态", 200.0
    if score >= 90: return "🌟 出色的状态", 88.88
    if score >= 60: return "✅ 合格的状态", 10.0
    return "💪 加油呀", 0.0

if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []
if "undo_stack" not in st.session_state: st.session_state.undo_stack = []
if "custom_tasks" not in st.session_state:
    st.session_state.custom_tasks = [
        {"name": "没有玩游戏", "points": 20},
        {"name": "10:30前睡觉", "points": 10},
        {"name": "实战复盘", "points": 5},
        {"name": "如厕不看手机", "points": 2}
    ]

# --- 4. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 设置")
    selected_date = st.date_input("记录日期", datetime.now())
    st.divider()
    n_name = st.text_input("新增任务名")
    n_pts = st.number_input("积分", min_value=0, value=5)
    if st.button("➕ 添加到打卡清单"):
        if n_name:
            st.session_state.custom_tasks.append({"name": n_name, "points": n_pts})
            st.rerun()

# --- 5. 顶部统计 ---
try:
    df_raw = pd.read_csv(READ_URL)
    df_raw['日期'] = pd.to_datetime(df_raw['日期']).dt.date
    lifetime_money = df_raw.groupby('日期')['当日奖金'].first().sum()
    completed_days = len(df_raw['日期'].unique()) + 1
except:
    lifetime_money = 0.0; completed_days = 1

st.markdown(f"""
<div class="ios-card">
    <div style="display: flex; justify-content: space-between;">
        <div><span class="stat-label">已坚持记录</span><br><span class="stat-val-green">第 {completed_days} 天</span></div>
        <div style="text-align: right;"><span class="stat-label">总累计奖金</span><br><span class="stat-val-red">¥{lifetime_money:.2f}</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 6. 计分中心 ---
status_str, reward_val = calculate_status(st.session_state.score)
st.markdown(f"""
<div class="ios-card" style="text-align: center;">
    <div class="status-badge">{status_str}</div>
    <div class="score-val">{st.session_state.score}</div>
    <div class="money-label">今日预计奖金：¥{reward_val:.2f}</div>
</div>
""", unsafe_allow_html=True)

# 撤销
if st.button("🔙 撤销上一条", key="undo_btn"):
    if st.session_state.undo_stack:
        last = st.session_state.undo_stack.pop()
        st.session_state.score, st.session_state.details = last["score"], last["logs"]
        st.rerun()

# --- 7. 打卡清单 ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 10px 5px;">日常任务打卡</p>', unsafe_allow_html=True)
for i, task in enumerate(st.session_state.custom_tasks):
    if st.button(f" {task['name']} 　　　　　　　　　　　　　 +{task['points']}", key=f"t_{i}"):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += task['points']
        st.session_state.details.append(f"{task['name']}(+{task['points']})")
        st.rerun()

# --- 8. 手机时间结算 (直接填数字版) ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 20px 5px 10px;">📱 手机时间结算 (分钟)</p>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    # 🌟 这里改成了数字输入框
    p_min = st.number_input("输入今日时长", min_value=0, max_value=1440, value=120, step=5, label_visibility="collapsed")
    diff = 120 - p_min
    p_pts = 20 + (diff // 5)
    st.write(f"💡 120min基准 ➔ **自动积 {p_pts} 分**")
    if st.button("确认记录手机得分", type="secondary"):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += p_pts
        st.session_state.details.append(f"手机结算({p_min}min): {p_pts}分")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 9. 身体数据 ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 10px 5px;">今日身体数据</p>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    cw, ch = st.columns(2)
    w_v = cw.text_input("体重 (kg)", placeholder="0.0")
    h_v = ch.text_input("心率 (bpm)", placeholder="0")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 10. 同步结算 ---
if st.button("🚀 确认结算并同步到云端", type="primary"):
    d_str = selected_date.strftime("%Y-%m-%d")
    payloads = []
    if not st.session_state.details:
        payloads.append({"日期": d_str, "项目明细": "无记录", "项目分值": 0, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": w_v, "心率": h_v})
    else:
        for d in st.session_state.details:
            pts = 0
            if "(+" in d: pts = int(d.split("(+")[1].split(")")[0])
            elif "分" in d and ": " in d: pts = int(d.split(": ")[1].replace("分", ""))
            payloads.append({"日期": d_str, "项目明细": d, "项目分值": pts, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": w_v, "心率": h_v})

    try:
        with st.spinner('同步中...'):
            for item in payloads: requests.post(SCRIPT_URL, json=item, timeout=10)
        st.balloons(); st.success("结算成功！"); st.session_state.score = 0; st.session_state.details = []; st.session_state.undo_stack = []; st.cache_data.clear(); st.rerun()
    except Exception as e: st.error(f"同步失败: {e}")

# --- 11. 历史 ---
with st.expander("📊 历史记录明细"):
    try:
        df_v = pd.read_csv(READ_URL)
        st.dataframe(df_v.sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)
    except: st.info("数据读取中...")
