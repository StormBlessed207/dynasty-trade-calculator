import streamlit as st
import pandas as pd

# --- DATA PIPELINE: STABLE CSV LOADING ---
@st.cache_data(ttl=86400) # Caches the data for 24 hours
def load_dynasty_process_data():
    url = "https://raw.githubusercontent.com/dynastyprocess/data/refs/heads/master/files/values.csv"
    try:
        # Loading directly from the stable repository
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Could not load data: {e}")
        return pd.DataFrame()

# Load the data
df = load_dynasty_process_data()

# --- MAPPING & LOOKUP ---
def get_player_value(player_name, league_format="1qb"):
    """
    Looks up player value from the DataFrame.
    league_format options: '1qb' (value_1qb) or '2qb' (value_2qb)
    """
    col_name = "value_1qb" if league_format == "1qb" else "value_2qb"
    
    # Filter for the player (case insensitive match)
    match = df[df['player'].str.lower() == player_name.lower()]
    
    if not match.empty:
        return int(match.iloc[0][col_name])
    return 0 # Default if player not found
