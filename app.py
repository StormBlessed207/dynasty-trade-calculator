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

@st.cache_data(ttl=600)
def get_user_leagues(username):
    user_resp = requests.get(f"https://api.sleeper.app/v1/user/{username}").json()
    if not user_resp: return None
    user_id = user_resp.get("user_id")
    return requests.get(f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/2026").json()

@st.cache_data(ttl=600)
def get_all_league_rosters(league_id):
    rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    users = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users").json()
    all_players = requests.get("https://api.sleeper.app/v1/players/nfl").json()
    
    user_map = {u['user_id']: u.get('display_name', 'Unknown') for u in users}
    
    full_rosters = {}
    for r in rosters:
        owner_id = r.get('owner_id')
        manager_name = user_map.get(owner_id, "Unknown Team")
        player_ids = r.get('players', [])
        player_names = [all_players.get(pid, {}).get('full_name') for pid in player_ids if pid in all_players]
        full_rosters[manager_name] = player_names
    return full_rosters

# --- LOGIC ---
df = load_data()
top_15 = df.nlargest(15, 'value_1qb')['player'].tolist()

def calculate_custom_value(player_name):
    match = df[df['player'].str.contains(player_name, case=False, na=False)]
    if match.empty: return 0
    base_val = match.iloc[0]['value_1qb']
    if player_name in ["Patrick Mahomes", "C.J. Stroud", "Joe Burrow", "Dak Prescott", "Brock Purdy"]: return int(base_val * 1.25)
    if player_name in ["Josh Allen", "Lamar Jackson", "Jordan Love", "Justin Herbert"]: return int(base_val * 1.12)
    return int(base_val)

# --- SIDEBAR ---
st.sidebar.header("🔌 Connect Sleeper")
username = st.sidebar.text_input("Sleeper Username")

if username:
    leagues = get_user_leagues(username)
    if leagues:
        selected_league = st.sidebar.selectbox("Select League", leagues, format_func=lambda x: x['name'])
        if st.sidebar.button("Load League Data"):
            st.session_state.league = selected_league
            st.session_state.rosters = get_all_league_rosters(selected_league['league_id'])

# --- MAIN DISPLAY ---
if "rosters" in st.session_state:
    all_teams = st.session_state.rosters
    
    col1, col2 = st.columns(2)
    
    # 1. Select Your Team
    my_team = col1.selectbox("Select Your Team:", list(all_teams.keys()), key="my_team_select")
    my_players = all_teams.get(my_team, [])
    my_send = col1.multiselect("Select players to send:", my_players)
    
    # 2. Select Opponent Team
    opp_team = col2.selectbox("Select Opponent Team:", list(all_teams.keys()), key="opp_team_select")
    opp_players = all_teams.get(opp_team, [])
    opp_recv = col2.multiselect("Select players to receive:", opp_players)
    
    if st.button("Evaluate Trade"):
        my_total = sum(calculate_custom_value(p) for p in my_send)
        opp_total = sum(calculate_custom_value(p) for p in opp_recv)
        st.metric("Net Value Change", f"{opp_total - my_total:,}")
else:
    st.info("Please connect your Sleeper account to see teams.")
