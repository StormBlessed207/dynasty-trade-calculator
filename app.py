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
def get_my_roster(league_id, username):
    rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    all_players = requests.get("https://api.sleeper.app/v1/players/nfl").json()
    user_id = requests.get(f"https://api.sleeper.app/v1/user/{username}").json().get("user_id")
    
    for r in rosters:
        if r['owner_id'] == user_id:
            return [all_players.get(pid, {}).get('full_name') for pid in r['players'] if pid in all_players]
    return []

# --- LOGIC ---
df = load_data()
top_15 = df.nlargest(15, 'value_1qb')['player'].tolist()

def calculate_custom_value(player_name):
    match = df[df['player'].str.contains(player_name, case=False, na=False)]
    if match.empty: return 0
    base_val = match.iloc[0]['value_1qb']
    # Your custom multipliers
    if player_name in ["Patrick Mahomes", "C.J. Stroud", "Joe Burrow", "Dak Prescott", "Brock Purdy"]: return int(base_val * 1.25)
    if player_name in ["Josh Allen", "Lamar Jackson", "Jordan Love", "Justin Herbert"]: return int(base_val * 1.12)
    return int(base_val)

# --- SIDEBAR: LEAGUE CONNECTION ---
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
    
    if status == "complete":
        my_players = get_my_roster(st.session_state.league['league_id'], username)
        st.success("Draft Complete: Displaying your roster.")
    else:
        my_players = top_15
        st.info(f"Draft Status: {status}. Displaying Top 15 players by value.")

    col1, col2 = st.columns(2)
    my_send = col1.multiselect("Select players to send:", my_players)
    all_players = df['player'].tolist()
    opp_recv = col2.multiselect("Select players to receive:", all_players)
    
    if st.button("Evaluate Trade"):
        my_total = sum(calculate_custom_value(p) for p in my_send)
        opp_total = sum(calculate_custom_value(p) for p in opp_recv)
        st.metric("Net Value Change", f"{opp_total - my_total:,}")
