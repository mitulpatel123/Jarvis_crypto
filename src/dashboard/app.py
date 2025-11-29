import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import asyncio
import os
from src.data.db_manager import db_manager

st.set_page_config(page_title="Jarvis God Mode", layout="wide")

# Sidebar
st.sidebar.title("🎮 Control Center")
selected_mode = st.sidebar.radio("View Data For:", ["BACKTEST", "PAPER", "LIVE"])

st.title(f"🚀 Jarvis Operations: {selected_mode}")

# 1. Fetch Data from DB for Selected Mode
# (Note: In production, use a synchronous wrapper or run async in loop)
# For this UI snippet, we assume a helper function gets the data
conn_str = os.getenv("DATABASE_URL", "postgresql://mitulpatel@localhost/jarvis_crypto")
try:
    import psycopg2
    conn = psycopg2.connect(conn_str)
    query = f"SELECT * FROM trades WHERE mode = '{selected_mode}' ORDER BY entry_time DESC LIMIT 50"
    trades_df = pd.read_sql(query, conn)
    conn.close()
except Exception as e:
    st.error(f"DB Error: {e}")
    trades_df = pd.DataFrame()

# 2. Metrics
total_trades = len(trades_df)
win_rate = "0%"
if total_trades > 0:
    wins = len(trades_df[trades_df['profit_loss'] > 0])
    win_rate = f"{(wins/total_trades)*100:.1f}%"

c1, c2, c3 = st.columns(3)
c1.metric("Total Trades", total_trades)
c2.metric("Win Rate", win_rate)
c3.metric("Database Status", "🟢 Online")

# 3. Trade History Table
st.subheader("📜 Trade Log")
st.dataframe(trades_df, use_container_width=True)

# 4. Agent Health
st.subheader("🧠 Neural Network Status")
st.write("Checking active agents in `src/agents/`...")
# (You can list active files here)
agent_files = [f for f in os.listdir("src/agents") if f.endswith("_agent.py")]
st.write(f"Active Agents: {len(agent_files)}")
st.json(agent_files)
