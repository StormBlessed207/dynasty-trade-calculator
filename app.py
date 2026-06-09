import streamlit as st
import requests
import pandas as pd

# Set up page styling
st.set_page_config(page_title="Custom 1QB Scoring Trade Optimizer", layout="wide")
st.title("🏈 Custom Dynasty 1QB Trade Optimizer")
st.markdown("---")

# Global Configuration
SEASON = "2026"  

# --- API HELPERS (WITH BUILT-IN CACHING) ---
@st.cache_data(ttl=3600)
def load_global_players():
    try:
        return requests.get("https://api.sleeper.app/v1/players/nfl").json()
    except Exception:
        return {}

@st.cache_data(ttl=900)
def load_live_market_values():
    url = "https://api.fantasycalc.com/values/current?isDynasty=true&isSuperflex=false&numTeams=12&ppr=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            value_map = {}
            for item in response.json():
                player_obj = item.get("player", {})
                name = player_obj.get("name")
                val = item.get("value", 0)
                if name:
                    # Strip spaces, punctuation, and suffixes to find clean base names
                    clean_name = name.lower().replace(".", "").replace("'", "").replace(" ", "")
                    # Strip common suffixes so base matches remain seamless
                    for suffix in ["ii", "iii", "jr", "sr"]:
                        if clean_name.endswith(suffix) and len(clean_name) > len(suffix) + 3:
                            clean_name = clean_name[:-len(suffix)]
                    value_map[clean_name] = int(val)
            return value_map
        return {}
    except Exception:
        return {}

def get_user_id(username):
    url = f"https://api.sleeper.app/v1/user/{username}"
    response = requests.get(url)
    return response.json().get("user_id") if response.status_code == 200 and response.json() else None

def get_user_leagues(user_id):
    url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{SEASON}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else []

def get_league_metadata(league_id):
    rosters_url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    users_url = f"https://api.sleeper.app/v1/league/{league_id}/users"
    return requests.get(rosters_url).json(), requests.get(users_url).json()

# --- CUSTOM SCORING SCALING LOGIC ---
def lookup_and_modify_value(name_str, market_values):
    clean = name_str.lower().replace(".", "").replace("'", "").replace(" ", "")
    for suffix in ["ii", "iii", "jr", "sr"]:
        if clean.endswith(suffix) and len(clean) > len(suffix) + 3:
            clean = clean[:-len(suffix)]
            
    # Base fallback architecture if name is fully omitted from the API feed
    is_qb = name_str in ["Patrick Mahomes", "Josh Allen", "Lamar Jackson", "Jalen Hurts", "C.J. Stroud", "Anthony Richardson", "Jayden Daniels", "Baker Mayfield"]
    default_fallback = 2200 if is_qb else 7500
    
    base_val = market_values.get(clean, default_fallback) 
    
    # --- CUSTOM SCORING SCALING ENGINE ---
    if name_str in ["Patrick Mahomes", "C.J. Stroud", "Joe Burrow", "Dak Prescott", "Brock Purdy"]:
        return int(base_val * 1.25)
        
    if name_str in ["Josh Allen", "Lamar Jackson", "Jordan Love", "Justin Herbert"]:
        return int(base_val * 1.12)

    if name_str in ["Jalen Hurts", "Anthony Richardson", "Jayden Daniels", "Kyler Murray"]:
        return int(base_val * 0.85)
        
    if name_str in ["Baker Mayfield", "Geno Smith", "Will Levis", "Kirk Cousins", "Deshaun Watson"]:
        return int(base_val * 0.70)

    return base_val

# --- APPLICATION SIDEBAR CONTROL ---
st.sidebar.header("🔑 Account Connection")
username_input = st.sidebar.text_input("Sleeper Username", placeholder="Enter username...")
load_btn = st.sidebar.button("🔌 Load League Data")

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "leagues" not in st.session_state:
    st.session_state.leagues = []

if load_btn and username_input:
    with st.spinner("Connecting..."):
        uid = get_user_id(username_input)
        if uid:
            st.session_state.user_id = uid
            st.session_state.leagues = get_user_leagues(uid)
            st.sidebar.success(f"Connected!")
        else:
            st.sidebar.error("Username not found.")

# --- MAIN DASHBOARD FRAMEWORK ---
if st.session_state.user_id and st.session_state.leagues:
    league_options = {lg["name"]: lg["league_id"] for lg in st.session_state.leagues}
    selected_league_name = st.selectbox("🎯 Select Active League", list(league_options.keys()))
    active_league_id = league_options[selected_league_name]
    
    market_values = load_live_market_values()
    rosters, users_data = get_league_metadata(active_league_id)
    
    user_map = {}
    for u in users_data:
        uid = u.get("user_id")
        display_name = u.get("display_name", "Unknown")
        team_name = u.get("metadata", {}).get("team_name", display_name)
        user_map[uid] = {"name": display_name, "team": team_name}
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ Active Rules Engine")
    st.sidebar.info("⚡ 1QB Format Overrides Loaded:\n• 6 pt Pass TD\n• -4 pt INT\n• +0.3 Per Completion")
    
    simulation_pool = [
        "Justin Jefferson", "CeeDee Lamb", "Ja'Marr Chase", "Amon-Ra St. Brown", 
        "Breece Hall", "Bijan Robinson", "Jahmyr Gibbs", "Malik Nabers",
        "Patrick Mahomes", "Josh Allen", "Lamar Jackson", "Jalen Hurts", 
        "C.J. Stroud", "Anthony Richardson", "Jayden Daniels", "Baker Mayfield"
    ]
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📤 Your Simulated Offer")
        my_trade_pieces = st.multiselect("Select players to send:", simulation_pool, key="my_send_assets")
    with col2:
        st.subheader("📥 Opponent's Assets")
        opponent_labels = [f"{info['team']} ({info['name']})" for uid, info in user_map.items() if uid != st.session_state.user_id]
        selected_opp = st.selectbox("🤝 Select Trading Partner", opponent_labels if opponent_labels else ["Opponent 1"])
        opp_trade_pieces = st.multiselect("Select players to receive:", simulation_pool, key="opp_recv_assets")
                    
    if st.button("🔥 Run Live Valuation Analysis", use_container_width=True):
        st.subheader("📊 Custom Trade Evaluation Summary")
        
        my_total_val = sum(lookup_and_modify_value(p, market_values) for p in my_trade_pieces)
        opp_total_val = sum(lookup_and_modify_value(p, market_values) for p in opp_trade_pieces)
        
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown(f"**Custom Value You Give:** `{my_total_val:,} pts`")
            for p in my_trade_pieces:
                clean_p = p.lower().replace(".", "").replace("'", "").replace(" ", "")
                for sfx in ["ii", "iii", "jr", "sr"]:
                    if clean_p.endswith(sfx) and len(clean_p) > len(sfx) + 3:
                        clean_p = clean_p[:-len(sfx)]
                is_qb = p in ["Patrick Mahomes", "Josh Allen", "Lamar Jackson", "Jalen Hurts", "C.J. Stroud", "Anthony Richardson", "Jayden Daniels", "Baker Mayfield"]
                base = market_values.get(clean_p, 2200 if is_qb else 7500)
                custom = lookup_and_modify_value(p, market_values)
                st.write(f"• {p} (Market 1QB: {base:,} ➔ **Custom: {custom:,}**)")
        with c_right:
            st.markdown(f"**Custom Value You Receive:** `{opp_total_val:,} pts`")
            for p in opp_trade_pieces:
                clean_p = p.lower().replace(".", "").replace("'", "").replace(" ", "")
                for sfx in ["ii", "iii", "jr", "sr"]:
                    if clean_p.endswith(sfx) and len(clean_p) > len(sfx) + 3:
                        clean_p = clean_p[:-len(sfx)]
                is_qb = p in ["Patrick Mahomes", "Josh Allen", "Lamar Jackson", "Jalen Hurts", "C.J. Stroud", "Anthony Richardson", "Jayden Daniels", "Baker Mayfield"]
                base = market_values.get(clean_p, 2200 if is_qb else 7500)
                custom = lookup_and_modify_value(p, market_values)
                st.write(f"• {p} (Market 1QB: {base:,} ➔ **Custom: {custom:,}**)")
                
        st.markdown("---")
        net_difference = opp_total_val - my_total_val
        if net_difference > 150:
            st.success(f"✅ **Trade Win!** Net custom value increase of `+{abs(net_difference):,}` points.")
        elif net_difference < -150:
            st.error(f"❌ **Trade Loss!** You are giving away `-{abs(net_difference):,}` points of value.")
        else:
            st.info(f"⚖️ **Fair Trade.** Net variance is only `{net_difference:,}` points.")
else:
    st.info("💡 Please enter your Sleeper Username in the sidebar menu and click 'Load League Data' to populate your team dashboard.")
