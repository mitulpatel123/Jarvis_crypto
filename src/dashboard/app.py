import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import time
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.data.delta_client import delta_client

st.set_page_config(page_title="Jarvis Crypto Dashboard", layout="wide")

st.title("🧠 Jarvis Crypto Trader - Real-Time Dashboard")

# Sidebar
st.sidebar.header("Control Panel")
symbol = st.sidebar.text_input("Symbol", "BTCUSD")
refresh_rate = st.sidebar.slider("Refresh Rate (s)", 1, 60, 5)

# Load State
def load_state():
    try:
        if os.path.exists("data/state.json"):
            with open("data/state.json", "r") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading state: {e}")
    return None

state = load_state()

# Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Live Chart: {symbol}")
    
    # Fetch Live OHLC
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

with col2:
    st.subheader("Main Brain Decision 🧠")
    if state:
        decision = state.get("decision", {})
        action = decision.get("action", "NEUTRAL")
        confidence = decision.get("confidence", 0.0)
        reasoning = decision.get("reasoning", "No reasoning available.")
        
        color = "green" if action == "BUY" else "red" if action == "SELL" else "gray"
        st.markdown(f"<h2 style='color: {color};'>{action} ({confidence})</h2>", unsafe_allow_html=True)
        st.info(reasoning)
        
        st.markdown(f"**Last Update:** {state.get('last_update')}")
    else:
        st.info("Waiting for agent data...")

# Agent Signals Table
st.subheader("Agent Signals")
if state and "signals" in state:
    signals_df = pd.DataFrame(state["signals"])
    st.dataframe(signals_df, use_container_width=True)
else:
    st.write("No signals available.")

# Auto-Refresh
time.sleep(refresh_rate)
st.rerun()
