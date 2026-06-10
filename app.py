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
def get_league_data(league_id):
    return requests.get(f"https://api.sleeper.app/v1/league/{league_id}").json()

@st.cache_data(ttl=600)
def get_all_league_rosters(league_id):
    try:
        rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
        users = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users").json()
        all_players = requests.get("https://api.sleeper.app/v1/players/nfl").json()
        
        user_map = {u['user_id']: u.get('display_name', 'Unknown') for u in users}
        
        full_rosters = {}
        for r in rosters:
            owner_id = r.get('owner_id')
            manager_name = user_map.get(owner_id, "Unknown Team")
            # Filter players correctly
            player_ids = r.get('players', [])
            player_names = [all_players.get(pid, {}).get('full_name') for pid in player_ids if pid in all_players]
            full_rosters[manager_name] = player_names
        return full_rosters
    except Exception as e:
        st.error(f"Error fetching rosters: {e}")
        return {}

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
    else:
        st.sidebar.error("Could not find leagues.")

# --- MAIN DISPLAY ---
if "league" in st.session_state:
    league_info = get_league_data(st.session_state.league['league_id'])
    status = league_info.get("status")
    
    st.subheader(f"Trade Evaluator (Status: {status})")
    
    if status == "complete":
        all_teams = get_all_league_rosters(st.session_state.league['league_id'])
        
        if not all_teams:
            st.warning("No rosters found for this league.")
        else:
            col1, col2 = st.columns(2)
            # Select Your Team
            my_team = col1.selectbox("Select Your Team:", list(all_teams.keys()))
            my_players = all_teams.get(my_team, [])
            my_send = col1.multiselect("Select players to send:", my_players)
            
            # Select Opponent Team
            opp_team = col2.selectbox("Select Opponent Team:", list(all_teams.keys()))
            opp_players = all_teams.get(opp_team, [])
            opp_recv = col2.multiselect("Select players to receive:", opp_players)
    else:
        st.info("Draft in progress/Pre-draft. Using Top 15 players for simulation.")
        col1, col2 = st.columns(2)
        my_send = col1.multiselect("Select players to send:", top_15)
        opp_recv = col2.multiselect("Select players to receive:", top_15)
    
    if st.button("Evaluate Trade"):
        my_total = sum(calculate_custom_value(p) for p in my_send)
        opp_total = sum(calculate_custom_value(p) for p in opp_recv)
        st.metric("Net Value Change", f"{opp_total - my_total:,}")
