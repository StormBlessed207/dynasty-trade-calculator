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
def get_user_leagues(username):
    # Get user_id first
    user_resp = requests.get(f"https://api.sleeper.app/v1/user/{username}").json()
    if not user_resp: return None
    user_id = user_resp.get("user_id")
    
    # Get leagues for 2026
    leagues = requests.get(f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/2026").json()
    return leagues

@st.cache_data(ttl=3600)
def get_sleeper_roster(league_id, username):
    # Fetch roster and players map
    rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    all_players = requests.get("https://api.sleeper.app/v1/players/nfl").json()
    user_id = requests.get(f"https://api.sleeper.app/v1/user/{username}").json().get("user_id")
    
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
    
    # Custom Multipliers
    if player_name in ["Patrick Mahomes", "C.J. Stroud", "Joe Burrow", "Dak Prescott", "Brock Purdy"]: return int(base_val * 1.25)
    if player_name in ["Josh Allen", "Lamar Jackson", "Jordan Love", "Justin Herbert"]: return int(base_val * 1.12)
    return int(base_val)

# --- SIDEBAR: LEAGUE CONNECTION ---
st.sidebar.header("🔌 Connect Sleeper")
username = st.sidebar.text_input("Sleeper Username")

if username:
    leagues = get_user_leagues(username)
    if leagues:
        # User selects league from dropdown
        selected_league = st.sidebar.selectbox("Select League", leagues, format_func=lambda x: x['name'])
        
        if st.sidebar.button("Load Roster"):
            st.session_state.roster = get_sleeper_roster(selected_league['league_id'], username)
    else:
        st.sidebar.error("Could not find leagues for this user.")

if "roster" in st.session_state:
    st.subheader("📤 Select Players to Trade")
    col1, col2 = st.columns(2)
    my_send = col1.multiselect("Players you are sending:", st.session_state.roster)
    all_players = df['player'].tolist()
    opp_recv = col2.multiselect("Players you are receiving:", all_players)
    
    if st.button("Evaluate Trade"):
        my_total = sum(calculate_custom_value(p) for p in my_send)
        opp_total = sum(calculate_custom_value(p) for p in opp_recv)
        st.metric("Net Value Change", f"{opp_total - my_total:,}")
