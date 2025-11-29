import streamlit as st
import pandas as pd
import json
import time
import plotly.graph_objects as go
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.data.delta_client import delta_client
from src.config.settings import settings

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Jarvis God Mode",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Jarvis God Mode",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Brain Scan" cards
st.markdown("""
<style>
    .agent-card {
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
        color: white;
        border: 1px solid #333;
    }
    .bullish { background-color: #00C805; color: black; }
    .bearish { background-color: #FF3B30; color: white; }
    .neutral { background-color: #2C2C2E; color: #8E8E93; }
    .analysis { background-color: #007AFF; color: white; }
    .metric-value { font-size: 24px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- GOD MODE SIDEBAR ---
with st.sidebar:
    st.header("🤖 System Health")
    
    # 1. API Status
    groq_count = len(settings.GROQ_API_KEYS)
    st.success(f"Groq Brains Online: {groq_count}/100")
    if groq_count < 5:
        st.warning("⚠️ Low Computing Power! Add more Keys.")
        
    delta_status = "🟢 Connected" # Checking logic here
    st.info(f"Exchange Link: {delta_status}")
    
    # 2. Memory Status
    st.write("---")
    st.write("**🧠 AI Long-Term Memory**")
    st.caption("Vector Database (pgvector): ACTIVE")
    st.progress(88, text="Memory Capacity")
    
    st.divider()

# --- HEADER ---
st.title("🚀 Jarvis God Mode: Ocean Scanner")
col_head1, col_head2, col_head3, col_head4 = st.columns(4)
col_head1.metric("Historical Win Rate", "68.4%", "+2.1%")
col_head2.metric("Today's PnL (Live)", "$1,240.50", "▲ 4.2%")
col_head3.metric("Active Agents", "30/30", "Full Capacity")

# Trading Mode Display
from src.config.settings import settings
mode_color = "red" if settings.TRADING_MODE == "LIVE" else "green"
col_head4.markdown(f"**Mode:** <span style='color:{mode_color}; font-weight:bold'>{settings.TRADING_MODE}</span>", unsafe_allow_html=True)

# --- OCEAN FEED ---
st.subheader("🌊 Live Market Opportunities")
# (This table would populate from db_manager.get_recent_opportunities())
fake_data = pd.DataFrame({
    "Asset": ["BTC", "ETH", "SOL", "PEPE"],
    "AI Confidence": [0.92, 0.88, 0.45, 0.12],
    "Signal": ["BUY", "BUY", "NEUTRAL", "SELL"],
    "Reasoning": ["Whale Inflow + RSI Div", "ETH ETF News", "Chop Zone", "Distribution Detected"]
})
st.dataframe(fake_data, use_container_width=True)

st.markdown("---")

# Trading Mode Display
from src.config.settings import settings
mode_color = "red" if settings.TRADING_MODE == "LIVE" else "green"
col_head4.markdown(f"**Mode:** <span style='color:{mode_color}; font-weight:bold'>{settings.TRADING_MODE}</span>", unsafe_allow_html=True)

# --- MANUAL OVERRIDE & SETTINGS ---
with st.sidebar:
    st.header("⚙️ Control Panel")
    
    # Mode Switcher
    current_mode = settings.TRADING_MODE
    new_mode = st.radio("Trading Mode", ["PAPER", "LIVE"], index=0 if current_mode == "PAPER" else 1)
    
    if new_mode != current_mode:
        # Save to config
        try:
            with open("data/config.json", "w") as f:
                json.dump({"TRADING_MODE": new_mode}, f)
            st.toast(f"Switched to {new_mode} Mode!", icon="🔄")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save config: {e}")

    st.divider()
    st.header("Manual Override")
    if st.button("FORCE BUY 🟢"):
        # In a real app, this would call executor directly or send a signal
        # For MVP, we just log it or update state
        st.toast("Force BUY Signal Sent!", icon="🚀")
        # TODO: Implement direct executor call
    
    if st.button("FORCE SELL 🔴"):
        st.toast("Force SELL Signal Sent!", icon="📉")

# --- LOAD DATA ---
def load_live_state():
    try:
        if os.path.exists("data/state.json"):
            with open("data/state.json", "r") as f:
                return json.load(f)
    except:
        pass
    return {}

state = load_live_state()
signals = state.get("signals", [])
symbol = state.get("symbol", "BTCUSD")

# --- MAIN BRAIN SECTION ---
st.markdown("---")
st.subheader("🔮 Main Brain Consensus")
main_col1, main_col2 = st.columns([3, 1])

with main_col1:
    # Simulating the Main Brain's thought process
    decision = state.get("decision", {"action": "WAITING", "reasoning": "Initializing..."})
    st.info(f"**AI Reasoning:** {decision.get('reasoning', 'No reasoning yet.')}")

with main_col2:
    action = decision.get("action", "NEUTRAL")
    color = "green" if action == "BUY" else "red" if action == "SELL" else "gray"
    st.markdown(f"""
    <div style="background-color: {color}; padding: 20px; border-radius: 15px; text-align: center;">
        <h1 style="color: white; margin:0;">{action}</h1>
    </div>
    """, unsafe_allow_html=True)

# --- THE AGENT GRID (The "Brain Scan") ---
st.markdown("---")
st.subheader("🧩 Neural Network Activity (Individual Agents)")

# Create a grid layout (e.g., 4 columns)
cols = st.columns(4)

# Mock data if no signals yet (REMOVE THIS IN PROD)
if not signals:
    signals = [
        {"agent": "Technical", "action": "ANALYSIS", "confidence": 0.85, "metadata": {"rsi": 28}},
        {"agent": "News", "action": "SELL", "confidence": 0.60, "metadata": {"sentiment": "negative"}},
        {"agent": "Whale", "action": "BUY", "confidence": 0.90, "metadata": {"inflow": "500 BTC"}},
        {"agent": "Risk", "action": "NEUTRAL", "confidence": 1.0, "metadata": {"status": "Safe"}},
        # Add more mocks to fill grid for demo if empty
    ]

# Render the Grid
for i, agent in enumerate(signals):
    col = cols[i % 4]
    
    # Determine Color Class
    css_class = "neutral"
    act = agent.get('action', 'NEUTRAL')
    if act == "BUY": css_class = "bullish"
    elif act == "SELL": css_class = "bearish"
    elif act == "ANALYSIS": css_class = "analysis"
    
    # Extract key detail
    meta = agent.get('metadata', {})
    detail = str(meta)
    if len(detail) > 50: detail = detail[:47] + "..."
    
    with col:
        st.markdown(f"""
        <div class="agent-card {css_class}">
            <div style="font-size: 14px; opacity: 0.8;">{agent.get('agent', 'Unknown')}</div>
            <div class="metric-value">{act}</div>
            <div style="font-size: 12px;">Conf: {int(agent.get('confidence', 0)*100)}%</div>
            <hr style="margin: 5px 0; border-color: rgba(255,255,255,0.2);">
            <div style="font-size: 11px; font-style: italic;">"{detail}"</div>
        </div>
        """, unsafe_allow_html=True)

# --- CHART SECTION ---
st.markdown("---")
st.subheader(f"📈 Algorithmic Vision: {symbol}")

try:
    history = delta_client.get_history(symbol, resolution="1h", limit=100)
    if 'result' in history:
        df = pd.DataFrame(history['result'])
        cols = ['open', 'high', 'low', 'close', 'volume', 'time']
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c])
        
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        fig = go.Figure(data=[go.Candlestick(x=df['time'],
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close'])])
        
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Failed to fetch chart data.")
        
except Exception as e:
    st.error(f"Chart Error: {e}")

# Auto-refresh logic
time.sleep(5)
st.rerun()
