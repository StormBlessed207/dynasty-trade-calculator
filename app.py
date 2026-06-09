import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏈 DynastyProcess Trade Optimizer")

# --- LOAD DATA ---
@st.cache_data(ttl=86400)
def load_data():
    url = "https://raw.githubusercontent.com/dynastyprocess/data/refs/heads/master/files/values.csv"
    return pd.read_csv(url)

df = load_data()

# --- LOOKUP LOGIC ---
def get_player_val(name):
    # Search the 'player' column for a match
    match = df[df['player'].str.contains(name, case=False, na=False)]
    if not match.empty:
        # Pull from the 'value_1qb' column as verified in your screenshot
        return match.iloc[0]['value_1qb'] 
    return 0

# --- SIMPLE INPUT ---
player_input = st.text_input("Enter player name to test:")
if player_input:
    val = get_player_val(player_input)
    st.write(f"Value for {player_input}: {val}")
    
    # Optional: If you want to see the exact match found
    match = df[df['player'].str.contains(player_input, case=False, na=False)]
    if not match.empty:
        st.write("Match found:", match.iloc[0]['player'])
