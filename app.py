import streamlit as st
import pandas as pd
import requests

# --- APP CONFIG ---
st.set_page_config(layout="wide")
st.title("🏈 DynastyProcess + Sleeper Trade Optimizer")

# --- DATA PIPELINE ---
@st.cache_data(ttl=86400)
def load_data():
    url = "https://raw.githubusercontent.com/dynastyprocess/data/refs/heads/master/files/values.csv"
    return pd.read_csv(url)

@st.cache_data(ttl=3600)
def get_sleeper_roster(username, league_id):
    # Fetch roster for a specific league
    url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    players_url = "https://api.sleeper.app/v1/players/nfl"
    
    rosters = requests.get(url).json()
    all_players = requests.get(players_url).json()
    
    # Get user_id for username
    user_url = f"https://api.sleeper.app/v1/user/{username}"
    user_id = requests.get(user_url).json().get("user_id")
    
    # Find team roster
    my_roster = []
    for r in rosters:
        if r['owner_id'] == user_id:
            for p_id in r['players']:
                p_name = all_players.get(p_id, {}).get('full_name')
                if p_name: my_roster.append(p_name)
    return my_roster

# --- LOGIC ---
df = load_data()

def calculate_custom_value(player_name):
    match = df[df['player'].str.contains(player_name, case=False, na=False)]
    if match.empty: return 0
    base_val = match.iloc[0]['value_1qb']
    
    # Your Custom Multipliers
    if player_name in ["Patrick Mahomes", "C.J. Stroud", "Joe Burrow", "Dak Prescott", "Brock Purdy"]: return int(base_val * 1.25)
    if player_name in ["Josh Allen", "Lamar Jackson", "Jordan Love", "Justin Herbert"]: return int(base_val * 1.12)
    return int(base_val)

# --- SIDEBAR: LEAGUE CONNECTION ---
st.sidebar.header("🔌 Connect Sleeper")
username = st.sidebar.text_input("Sleeper Username")
league_id = st.sidebar.text_input("League ID") # Required to fetch roster

if username and league_id:
    roster = get_sleeper_roster(username, league_id)
    
    st.subheader("📤 Select Players to Trade")
    col1, col2 = st.columns(2)
    
    # Only show YOUR roster in the 'Send' list
    my_send = col1.multiselect("Players you are sending:", roster)
    
    # Full player list for the 'Receive' list (since you don't know their roster)
    all_players = df['player'].tolist()
    opp_recv = col2.multiselect("Players you are receiving:", all_players)
    
    if st.button("Evaluate Trade"):
        my_total = sum(calculate_custom_value(p) for p in my_send)
        opp_total = sum(calculate_custom_value(p) for p in opp_recv)
        
        st.metric("Net Value Change", f"{opp_total - my_total:,}")
        if opp_total > my_total: st.success("Trade Up!")
        else: st.error("Trade Down!")
