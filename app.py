import streamlit as st
import pandas as pd

# --- APP CONFIG ---
st.set_page_config(page_title="Custom 1QB Trade Optimizer", layout="wide")
st.title("🏈 DynastyProcess Trade Optimizer")

# --- DATA PIPELINE: STABLE CSV LOADING ---
@st.cache_data(ttl=86400)
def load_data():
    url = "https://raw.githubusercontent.com/dynastyprocess/data/refs/heads/master/files/values.csv"
    return pd.read_csv(url)

df = load_data()

# --- SCORING ENGINE ---
def calculate_custom_value(player_name):
    # Search for player
    match = df[df['player'].str.contains(player_name, case=False, na=False)]
    if match.empty:
        return 0
    
    base_val = match.iloc[0]['value_1qb']
    
    # Apply your specific 1QB Scaling Multipliers
    if player_name in ["Patrick Mahomes", "C.J. Stroud", "Joe Burrow", "Dak Prescott", "Brock Purdy"]:
        return int(base_val * 1.25)
    if player_name in ["Josh Allen", "Lamar Jackson", "Jordan Love", "Justin Herbert"]:
        return int(base_val * 1.12)
    if player_name in ["Jalen Hurts", "Anthony Richardson", "Jayden Daniels", "Kyler Murray"]:
        return int(base_val * 0.85)
    if player_name in ["Baker Mayfield", "Geno Smith", "Will Levis", "Kirk Cousins", "Deshaun Watson"]:
        return int(base_val * 0.70)
    
    return int(base_val)

# --- TRADE DASHBOARD ---
st.subheader("📤 Trade Evaluator")
player_list = df['player'].tolist()

col1, col2 = st.columns(2)
with col1:
    send_assets = st.multiselect("Players you are sending:", player_list)
with col2:
    recv_assets = st.multiselect("Players you are receiving:", player_list)

if st.button("Calculate Trade Value"):
    my_total = sum(calculate_custom_value(p) for p in send_assets)
    opp_total = sum(calculate_custom_value(p) for p in recv_assets)
    
    col_a, col_b = st.columns(2)
    col_a.metric("Value Sent", f"{my_total:,}")
    col_b.metric("Value Received", f"{opp_total:,}", delta=f"{opp_total - my_total:,}")
    
    if opp_total > my_total:
        st.success("✅ This trade increases your team's total value.")
    else:
        st.error("❌ This trade decreases your team's total value.")
