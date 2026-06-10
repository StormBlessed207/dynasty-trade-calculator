import streamlit as st
import pandas as pd
import requests

# --- DATA PIPELINE ---
@st.cache_data(ttl=86400)
def load_data():
    url = "https://raw.githubusercontent.com/dynastyprocess/data/refs/heads/master/files/values.csv"
    return pd.read_csv(url)

@st.cache_data(ttl=600) # Cache for 10 mins during draft season
def get_league_status(league_id):
    # Fetch league metadata to check status
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

# --- APP LOGIC ---
df = load_data()
top_15 = df.nlargest(15, 'value_1qb')['player'].tolist() # Fetch Top 15

# ... (Sidebar username/league selection remains same)

if "selected_league" in st.session_state:
    status_data = get_league_status(st.session_state.selected_league['league_id'])
    status = status_data.get("status") # "pre_draft", "drafting", or "complete"
    
    if status == "complete":
        my_players = get_my_roster(st.session_state.selected_league['league_id'], username)
        st.success("Draft Complete: Displaying your roster.")
    else:
        my_players = top_15
        st.info(f"Draft Status: {status}. Displaying Top 15 Players.")

    # Display selection
    my_send = st.multiselect("Select players to trade:", my_players)
