import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. 配置中心 ---
READ_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTaLJQbQAIk0Vp5PRD7U1JDyturObEh7PCdVTUiFKikO6BaqVoZIRIwzxYxHnvPBPa_yCHy5ErNm2xE/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwwbgupWtmk2yNwVs1DIyfsQe84ZZnvfC-LMly8caYaYos-o5Tqz8-V7kDCtGbbqs1g/exec"

# --- 2. 深度定制 iOS 样式 (锁定紧凑布局) ---
st.set_page_config(page_title="训练指挥部", page_icon="🤺", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* 屏蔽冗余 */
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], span[data-testid="stIconMaterial"] {
        display: none !important;
    }
    
    [data-testid="stAppViewContainer"] { background-color: #F2F2F7; }
    * { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif !important; }
    
    /* 核心：大方框容器强制居中 */
    [data-testid="stElementContainer"] > div[data-style-border="true"] {
        background-color: white !important;
        border: none !important;
        border-radius: 20px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        padding: 15px 10px !important;
        margin-bottom: 10px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }

    .score-val { font-size: 80px; font-weight: 800; color: #000; line-height: 1; margin: 10px 0; text-align: center; width: 100%; }
    .status-badge { font-size: 15px; color: #FF9500; font-weight: 700; text-align: center; width: 100%; }
    .date-text { font-size: 13px; color: #8E8E93; font-weight: 400; }
    .money-label { font-size: 14px; color: #FF3B30; font-weight: 600; background: #FFF1F0; padding: 6px 12px; border-radius: 10px; display: inline-block; margin-bottom: 15px; }
    
    /* 按钮栏紧凑布局 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 4px !important; /* 极小间距 */
    }
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }

    /* 按钮极简风格 */
    .stButton > button, .stPopover > button {
        width: 100% !important; 
        border-radius: 10px !important; 
        border: none !important;
        background-color: #F2F2F7 !important; 
        color: #000 !important; 
        padding: 8px 0 !important;
        font-weight: 600 !important; 
        font-size: 11px !important; /* 缩小字体确保不换行 */
        box-shadow: none !important;
    }

    /* 列表按钮 */
    .task-list-btn button { text-align: left !important; padding: 12px 15px !important; background-color: white !important; box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important; font-size: 14px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 逻辑初始化 ---
if "score" not in st.session_state: st.session_state.score = 0
if "details" not in st.session_state: st.session_state.details = []
if "undo_stack" not in st.session_state: st.session_state.undo_stack = []
if "tasks" not in st.session_state:
    st.session_state.tasks = [{"name": "没有玩游戏", "points": 20}, {"name": "10:30前睡觉", "points": 10}, {"name": "阅读/作业", "points": 5}, {"name": "实战复盘", "points": 5}, {"name": "如厕不看手机", "points": 2}]

# --- 4. 顶部统计 ---
try:
    df_raw = pd.read_csv(READ_URL); df_raw['日期'] = pd.to_datetime(df_raw['日期']).dt.date
    lifetime_money = df_raw.groupby('日期')['当日奖金'].first().sum()
    completed_days = len(df_raw['日期'].unique()) + 1
except:
    lifetime_money = 0.0; completed_days = 1

st.markdown(f"""
<div style="background: white; padding: 15px; border-radius: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
    <div><span style="font-size:12px; color:#8E8E93;">已坚持记录</span><br><span style="font-size:18px; color:#34C759; font-weight:700;">第 {completed_days} 天</span></div>
    <div style="text-align: right;"><span style="font-size:12px; color:#8E8E93;">总累计奖金</span><br><span style="font-size:18px; color:#FF3B30; font-weight:700;">¥{lifetime_money:.2f}</span></div>
</div>
""", unsafe_allow_html=True)

# --- 🚀 5. 核心：紧凑型集成中控台 ---
today_str = datetime.now().strftime("%Y-%m-%d")
status_str, reward_val = (lambda s: ("🏆 最好的状态", 200.0) if s >= 100 else ("🌟 出色的状态", 88.88) if s >= 90 else ("✅ 合格的状态", 10.0) if s >= 60 else ("💪 加油呀", 0.0))(st.session_state.score)

with st.container(border=True):
    # 顶部状态与日期 (居中)
    st.markdown(f'<div class="status-badge">{status_str} <span class="date-text">| {today_str}</span></div>', unsafe_allow_html=True)
    # 大分数 (居中)
    st.markdown(f'<div class="score-val">{st.session_state.score}</div>', unsafe_allow_html=True)
    # 奖金标签 (居中)
    st.markdown(f'<div class="money-label">预计奖金：¥{reward_val:.2f}</div>', unsafe_allow_html=True)
    
    # 紧凑横向工具栏 (四合一)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🔙撤销", key="undo"):
            if st.session_state.undo_stack:
                last = st.session_state.undo_stack.pop()
                st.session_state.score, st.session_state.details = last["score"], last["logs"]; st.rerun()
    with c2:
        with st.popover("📅补录"):
            rec_date = st.date_input("补录日期", datetime.now(), label_visibility="collapsed")
    with c3:
        if st.button("🧹清除", key="clear"):
            st.session_state.score = 0; st.session_state.details = []; st.session_state.undo_stack = []; st.rerun()
    with c4:
        with st.popover("⚙️设置"):
            n_name = st.text_input("任务名")
            n_pts = st.number_input("积分", min_value=0, value=5)
            if st.button("🚀确认"):
                if n_name:
                    st.session_state.tasks.append({"name": n_name, "points": n_pts})
                    st.session_state.score += n_pts
                    st.session_state.details.append(f"{n_name}(+{n_pts})")
                    st.rerun()

if 'rec_date' not in locals(): rec_date = datetime.now()

# --- 6. 📱 手机时间结算 ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 15px 5px 5px;">📱 手机时长 (120min基准)</p>', unsafe_allow_html=True)
with st.container(border=True):
    p_min = st.number_input("分钟", min_value=0, value=120, step=5, label_visibility="collapsed")
    p_pts = 20 + ((120 - p_min) // 5)
    st.write(f"💡 结算积分：**{p_pts}** 分")
    if st.button("确认记录手机得分", key="p_btn"):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += p_pts; st.session_state.details.append(f"手机结算({p_min}min): {p_pts}分"); st.rerun()

# --- 7. 打卡清单 ---
st.markdown('<p style="font-weight: 600; color: #8E8E93; margin: 15px 5px 5px;">🎯 任务清单</p>', unsafe_allow_html=True)
for i, task in enumerate(st.session_state.tasks):
    st.markdown('<div class="task-list-btn">', unsafe_allow_html=True)
    if st.button(f" {task['name']} 　　　　　　　　　　　　　 +{task['points']}", key=f"t_{i}"):
        st.session_state.undo_stack.append({"score": st.session_state.score, "logs": st.session_state.details.copy()})
        st.session_state.score += task['points']; st.session_state.details.append(f"{task['name']}(+{task['points']})"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. 同步结算 ---
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚀 确认结算并同步到云端", type="primary"):
    d_str = rec_date.strftime("%Y-%m-%d")
    payloads = []
    if not st.session_state.details:
        payloads.append({"日期": d_str, "项目明细": "无记录", "项目分值": 0, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": "0", "心率": "0"})
    else:
        for d in st.session_state.details:
            pts = 0
            try:
                if "(+" in d: pts = int(d.split("(+")[1].split(")")[0])
                elif ": " in d: pts = int(d.split(": ")[1].replace("分", ""))
            except: pts = 0
            payloads.append({"日期": d_str, "项目明细": d, "项目分值": pts, "当日总分": st.session_state.score, "当日奖金": reward_val, "体重": "0", "心率": "0"})
    try:
        with st.spinner('同步中...'):
            for item in payloads: requests.post(SCRIPT_URL, json=item, timeout=10)
        st.balloons(); st.success("结算成功！"); st.session_state.score = 0; st.session_state.details = []; st.session_state.undo_stack = []; st.cache_data.clear(); st.rerun()
    except Exception as e: st.error(f"同步失败: {e}")

with st.expander("📊 历史记录明细"):
    try:
        df_v = pd.read_csv(READ_URL); st.dataframe(df_v.sort_values(by="日期", ascending=False), use_container_width=True, hide_index=True)
    except: st.info("历史载入中...")
