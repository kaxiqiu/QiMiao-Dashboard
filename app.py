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
    /* 基础背景和字体 */
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    * { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Icons", "Helvetica Neue", Helvetica, Arial, sans-serif !important; }
    
    /* 卡片样式 */
    .ios-card {
        background: white;
        padding: 18px;
        border-radius: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 12px;
    }
    
    /* 计分看板 */
    .score-title { font-size: 14px; color: #8E8E93; font-weight: 500; }
    .score-val { font-size: 72px; font-weight: 800; color: #000000; text-align: center; font-variant-numeric: tabular-nums; line-height: 1; margin: 10px 0; }
    .status-badge { font-size: 18px; color: #FF9500; font-weight: 700; text-align: center; }
    .money-label { font-size: 16px; color: #FF3B30; font-weight: 600; text-align: center; background: #FFF1F0; padding: 8px; border-radius: 10px; margin-top: 10px; }
    
    /* 顶部小统计 */
    .stat-label { font-size: 12px; color: #8E8E93; }
    .stat-val-green { font-size: 18px; color: #34C759; font-weight: 700; }
    .stat-val-red { font-size: 18px; color: #FF3B30; font-weight: 700; }
    
    /* 列表按钮模拟 iOS List Item */
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
        transition: 0.2s;
    }
    .stButton > button:hover { background-color: #E5E5EA; border: none; color: #000; }
    .stButton > button:active { background-color: #D1D1D6; transform: scale(0.98); }
    
    /* 调整输入框 */
    .stTextInput input { border-radius: 10px; background: #E5E5EA; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心算法 ---
def calculate_status(score):
    if score >= 100: return "🏆 最好的状态", 200.0
    if score >= 90: return "🌟 出色的状态", 88.88
    if score >= 60: return "✅ 合格的状态", 10.0
    return "💪 加油呀", 0.0

# 初始化 Session
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

# --- 4. 侧边栏管理 ---
with st.sidebar:
    st.title("⚙️ 指挥部设置")
    selected_date = st.date_input("记录日期", datetime.now())
    st.divider()
    st.subheader("➕ 自定义日常")
    n_name = st.text_input("任务名")
    n_pts = st.number_input("积分", min_value=0, value=5)
    if st.button("添加到清单"):
        if n_name:
            st.session_state.custom_tasks.append({"name": n_name, "points": n_pts})
            st.rerun()

# --- 5. 顶部统计卡片 (对齐 App 头部) ---
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
        <div><span class="stat-label">已坚持记录</span><br><span class="stat-val-green">第 {completed_days} 天</span></div>
        <div style="text-align: right;"><span class="stat-label">总累计奖金</span><br><span class="stat-val-red">¥{lifetime_money:.2f}</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 6. 核心看板 ---
status_str, reward_val = calculate_status(st.session_state.score)
st.markdown(f"""
<div class="ios-card" style="text-align: center; padding: 30px 10px;">
    <div class="status-badge">{status_str}</div>
    <div class="score-val">{st.session_state.score}</div>
    <div class="money-label">今日预计奖金：¥{reward_val:.2f}</div>
</div>
""", unsafe_allow_html=True)

# 撤销操作 (放在看板正下方)
c_undo, c_gap = st.columns([1, 3])
if c_undo.button("🔙 撤销"):
    if st.session_state.undo_stack:
        last = st.session_state.undo_stack.pop()
        st.session_state.score = last["score"]
        st.session_state.details = last["logs"]
        st.rerun()

# --- 7. 任务打卡 (模拟手机 List) ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin-left: 5px;">日常任务清单 (点击加分)</p>', unsafe_allow_html=True)
for i, task in enumerate(st.session_state.custom_tasks):
    if st.button(f" {task['name']} 　　　　　　　　　　　　　　 +{task['points']}", key=f"t_{i}"):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += task['points']
        st.session_state.details.append(f"{task['name']}(+{task['points']})")
        st.rerun()

# --- 8. 手机时间自动结算 (大叔核心逻辑) ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin-left: 5px; margin-top: 20px;">当日手机时间结算</p>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    p_min = st.slider("手机使用时长 (分钟)", 0, 300, 120, 5)
    # 逻辑：120min=20分，每少5min+1，每多5min-1
    diff = 120 - p_min
    p_pts = 20 + (diff // 5)
    st.markdown(f"📱 结算结果：**{p_pts} 分** <span style='color:#8E8E93; font-size:12px;'>(120min基准)</span>", unsafe_allow_html=True)
    if st.button("确认记录手机结算", type="secondary"):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += p_pts
        st.session_state.details.append(f"手机结算({p_min}min): {p_pts}分")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 9. 身体数据 ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin-left: 5px;">今日身体数据</p>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    c_w, c_h = st.columns(2)
    w_val = c_w.text_input("体重 (kg)", placeholder="0.0")
    h_val = c_h.text_input("心率 (bpm)", placeholder="0")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 10. 同步结算 ---
if st.button("🚀 确认结算并同步到云端表格", type="primary"):
    # 构造 payloads (完全复刻 App CSV 逻辑)
    date_str = selected_date.strftime("%Y-%m-%d")
    payloads = []
    if not st.session_state.details:
        payloads.append({"日期": date_str, "项目明细": "无记录", "项目分值": 0, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": w_val, "心率": h_val})
    else:
        for d in st.session_state.details:
            pts = 0
            if "(+" in d: pts = int(d.split("(+")[1].split(")")[0])
            elif "分" in d and ": " in d: pts = int(d.split(": ")[1].replace("分", ""))
            payloads.append({"日期": date_str, "项目明细": d, "项目分值": pts, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": w_val, "心率": h_val})

    try:
        with st.spinner('同步中...'):
            for item in payloads:
                requests.post(SCRIPT_URL, json=item, timeout=10)
        st.balloons()
        st.success("结算成功！记录已清零。")
        st.session_state.score = 0
        st.session_state.details = []
        st.session_state.undo_stack = []
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"同步失败: {e}")

# --- 11. 历史预览 ---
with st.expander("📊 查看历史记录明细"):
    try:
        df_view = pd.read_csv(READ_URL)
        st.dataframe(df_view.sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)
    except:
        st.info("数据读取中...")
