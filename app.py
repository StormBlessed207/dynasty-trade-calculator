import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏈 DynastyProcess Trade Optimizer")

# --- LOAD DATA ---
@st.cache_data(ttl=86400)
def load_data():
    url = "https://raw.githubusercontent.com/dynastyprocess/data/refs/heads/master/files/values.csv"
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

df = load_data()

# --- VERIFY DATA LOADED ---
if df.empty:
    st.warning("Data file is empty. Check the URL or your internet connection.")
else:
    # Show user what columns we have so we can fix the lookup
    st.write("Data loaded successfully! Available columns:", df.columns.tolist())
    
    # --- LOOKUP LOGIC ---
    def get_player_val(name):
        match = df[df['player'].str.contains(name, case=False, na=False)]
        if not match.empty:
            # Change 'value_1qb' to the specific column name found in your dataframe
            return match.iloc[0]['value_1qb'] 
        return 0

    # --- SIMPLE INPUT ---
    player_input = st.text_input("Enter player name to test:")
    if player_input:
        val = get_player_val(player_input)
        st.write(f"Value for {player_input}: {val}")
