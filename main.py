import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import *
from data_utils import *
from datetime import datetime, timedelta
import requests
import os
import time
from stats_utils import *
import altair as alt
from betting_analysis import *
from team_data import fetch_team_players, fetch_player_stats, fetch_game_props, get_game_id_from_teams, fetch_player_game_log

# Define HARDCODED_ROSTERS and PROP_CATEGORIES
HARDCODED_ROSTERS = {
    "Team A": [{"name": "Player 1", "position": "G"}, {"name": "Player 2", "position": "F"}],
    "Team B": [{"name": "Player 3", "position": "C"}, {"name": "Player 4", "position": "G"}]
}

PROP_CATEGORIES = {
    "Points": {"thresholds": [10, 15, 20]},
    "Rebounds": {"thresholds": [5, 10, 15]},
    "Assists": {"thresholds": [3, 5, 7]}
}

st.set_page_config(page_title="Sports Betting Analytics", layout="wide")

# Initialize session states
if 'selected_game' not in st.session_state:
    st.session_state.selected_game = None
if 'selected_players' not in st.session_state:
    st.session_state.selected_players = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Add session state for filters
if 'prop_count' not in st.session_state:
    st.session_state.prop_count = {'total': 0, 'filtered': 0}
if 'saved_props' not in st.session_state:
    st.session_state.saved_props = []

# Enhanced sidebar with more navigation options
st.sidebar.title("Sports Betting Analytics")
page = st.sidebar.radio("Navigation", 
    ["Dashboard", "Props", "EV+", "Boosts", "Arbitrage", "Middle Bets"])

# Global filters in sidebar
with st.sidebar.expander("Global Filters", expanded=True):
    global_sport = st.selectbox("Sport", list(SPORT_KEYS.keys()), key="global_sport")
    prop_types = ["Points", "Rebounds", "Assists", "Blocks", "Steals", "Threes Made"]
    selected_props = st.multiselect("Proposition Types", prop_types, default=["Points"])
    show_over = st.checkbox("Show Over", value=True)
    show_under = st.checkbox("Show Under", value=True)
    min_odds = st.slider("Minimum Odds", -300, 300, -200)
    min_ev_slider = st.slider("Minimum EV", -10.0, 10.0, 0.0)

# Display prop count in sidebar
st.sidebar.metric("Live Props", 
    f"{st.session_state.prop_count['filtered']}/{st.session_state.prop_count['total']}")

# Enhanced AI Assistant in sidebar
with st.sidebar.expander("AI Betting Assistant", expanded=True):
    context = f"Current game: {st.session_state.selected_game}" if st.session_state.selected_game else ""
    user_question = st.text_input("Ask about betting strategies or insights:")
    
    # Add quick question buttons
    quick_questions = st.columns(2)
    with quick_questions[0]:
        if st.button("Analyze Matchup"):
            if st.session_state.selected_game:
                home_team, away_team = st.session_state.selected_game.split(" vs ")
                user_question = f"Analyze the matchup between {home_team} and {away_team}"
            else:
                st.error("Please select a game first.")
    with quick_questions[1]:
        if st.button("Find Value Bets"):
            user_question = "What are the best value bets in this game?"
            
    if user_question:
        with st.spinner("Analyzing..."):
            response = generate_ai_insight(user_question, context)
            st.session_state.chat_history.append({"q": user_question, "a": response})
            
    for chat in st.session_state.chat_history[-3:]:
        st.write(f"❓ {chat['q']}")
        st.info(f"🤖 {chat['a']}")

if page == "Dashboard":
    col1, col2, col3 = st.columns([2,2,1])
    with col1:
        sport_type = st.selectbox("Sport", list(SPORT_KEYS.keys()), key="sport_select")
        
    data = fetch_odds_data(sport_type)
    if data:
        df = pd.DataFrame(data)
        df['commence_time'] = pd.to_datetime(df['commence_time'])
        games = [f"{row['home_team']} vs {row['away_team']}" for _, row in df.iterrows()]
        
        with col2:
            selected_game = st.selectbox("Select Game", games, key="game_select")
            st.session_state.selected_game = selected_game
        
        with col3:
            st.metric("Game Time", df[df.apply(lambda x: f"{x['home_team']} vs {x['away_team']}" == selected_game, axis=1)]['commence_time'].iloc[0].strftime('%I:%M %p'))

        if selected_game:
            game_row = df[df.apply(lambda x: f"{x['home_team']} vs {x['away_team']}" == selected_game, axis=1)].iloc[0]
            home_team = game_row['home_team']
            away_team = game_row['away_team']
            
            tabs = st.tabs(["Game Props", "Player Analysis"])
            
            with tabs[0]:
                col1, col2 = st.columns([3,2])
                with col1:
                    bet_type = st.selectbox("Bet Type", ["Team", "Player Props"])
                    
                    if bet_type == "Team":
                        team_options = [home_team, away_team]
                        selected_team = st.selectbox("Select Team to Win", team_options)
                        bet_amount = st.number_input("Bet Amount ($)", min_value=1, value=100)
                        
                        odds_key = f"odds_{selected_team}"
                        if odds_key in game_row:
                            team_odds = float(game_row[odds_key])
                            implied_prob = calculate_implied_probability(team_odds)
                            
                            # Display odds info
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("American Odds", format_american_odds(team_odds))
                                if team_odds > 0:
                                    st.caption(f"Bet ${bet_amount} to win ${(team_odds/100 * bet_amount):.2f}")
                                else:
                                    st.caption(f"Bet ${bet_amount} to win ${(100/abs(team_odds) * bet_amount):.2f}")
                                    
                            with col2:
                                st.metric("Win Probability", f"{implied_prob:.1%}")
                                st.caption(f"Based on {selected_team} odds")
                                
                            with col3:
                                # Calculate EV using implied probability
                                ev = calculate_ev(team_odds, implied_prob, bet_amount)
                                st.metric("Expected Value", f"${ev:.2f}")
                                if ev > 0:
                                    st.caption("✅ +EV Bet")
                                else:
                                    st.caption("❌ -EV Bet")
                            
                            # Show bet breakdown
                            with st.expander("View Bet Details"):
                                win_amount = (team_odds/100 * bet_amount) if team_odds > 0 else (100/abs(team_odds) * bet_amount)
                                st.write(f"Win Scenario ({implied_prob:.1%} chance):")
                                st.write(f"• Win ${win_amount:.2f}")
                                st.write(f"Loss Scenario ({(1-implied_prob):.1%} chance):")
                                st.write(f"• Lose ${bet_amount:.2f}")
                                st.write("Expected Value Calculation:")
                                st.write(f"EV = ({implied_prob:.3f} × ${win_amount:.2f}) - ({1-implied_prob:.3f} × ${bet_amount:.2f})")
                                st.write(f"EV = ${ev:.2f}")
                        
                    else:  # Player Props
                        # Get real-time roster data
                        home_players = fetch_team_players(home_team)
                        away_players = fetch_team_players(away_team)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            team = st.selectbox("Select Team", [home_team, away_team])
                            players = home_players if team == home_team else away_players
                            
                            if not players:
                                st.error(f"No players found for {team}")
                                st.stop()
                                
                            player_options = [p['name'] for p in players]
                            if not player_options:
                                st.error("No players available")
                                st.stop()
                                
                            selected_player = st.selectbox(
                                "Select Player",
                                options=player_options,
                                format_func=lambda x: f"{x} ({next((p['position'] for p in players if p['name'] == x), 'N/A')})"
                            )
                        
                        with col2:
                            prop_type = st.selectbox("Prop Type", ["Points", "Rebounds", "Assists"])
                            bet_amount = st.number_input("Bet Amount ($)", min_value=1, value=100)
                        
                        # Get player stats and props safely
                        try:
                            player = next((p for p in players if p['name'] == selected_player), None)
                            if player:
                                player_id = player['id']
                                stats = fetch_player_stats(player_id)
                                
                                game_id = get_game_id_from_teams(home_team, away_team)
                                props = fetch_game_props(game_id) if game_id else {}
                                prop_data = props.get(selected_player, {}).get(prop_type.lower(), None)
                                
                                # Display stats and odds
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric(f"Season Avg {prop_type}", f"{stats[prop_type.lower()]:.1f}")
                                with col2:
                                    if prop_data:
                                        st.metric("Line", f"{prop_data['line']:.1f}")
                                        st.metric("Over Odds", format_american_odds(prop_data['over_odds']))
                                with col3:
                                    if prop_data:
                                        ev_over = calculate_ev(
                                            prop_data['over_odds'],
                                            calculate_implied_probability(prop_data['over_odds']),
                                            bet_amount
                                        )
                                        st.metric("Over EV", f"${ev_over:.2f}")
                                        if ev_over > 0:
                                            st.caption("✅ Positive EV Bet")
                            else:
                                st.error("Player not found")
                                
                        except Exception as e:
                            st.error(f"Error fetching player data: {e}")

            with tabs[1]:
                col1, col2 = st.columns([3,2])
                with col1:
                    st.subheader("Player Comparison")
                    
                    # Time range selector
                    time_range = st.select_slider(
                        "Analysis Period",
                        options=[5, 10, 15, 20, 25, 30],
                        value=10,
                        help="Number of games to analyze"
                    )
                    
                    # Fetch team rosters
                    home_roster = fetch_team_players(home_team)
                    away_roster = fetch_team_players(away_team)

                    col1, col2 = st.columns(2)
                    with col1:
                        player1 = st.selectbox(
                            f"{home_team} Players", 
                            options=[p['name'] for p in home_roster],
                            key="player1"
                        )
                    with col2:
                        player2 = st.selectbox(
                            f"{away_team} Players", 
                            options=[p['name'] for p in away_roster],
                            key="player2"
                        )
                    
                    if player1 and player2:
                        metrics = st.multiselect(
                            "Select Metrics to Compare",
                            ["points", "rebounds", "assists"],
                            default=["points"]
                        )
                        
                        try:
                            player1_id = next(p['id'] for p in home_roster if p['name'] == player1)
                            player2_id = next(p['id'] for p in away_roster if p['name'] == player2)
                            
                            # Fetch extended game logs
                            logs1 = fetch_player_game_log(player1_id, time_range)
                            logs2 = fetch_player_game_log(player2_id, time_range)
                            
                            # Create comparison charts for each metric
                            for metric in metrics:
                                st.subheader(f"{metric.title()} Comparison")
                                chart = create_comparison_chart(
                                    stats1=logs1,
                                    stats2=logs2,
                                    player1=player1,
                                    player2=player2,
                                    metric=metric,
                                    add_trend=True  # Changed from show_trend_line
                                )
                                st.altair_chart(chart, use_container_width=True)
                                
                                # Calculate and show trends
                                trend1 = logs1[metric].rolling(3).mean()
                                trend2 = logs2[metric].rolling(3).mean()
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric(
                                        f"{player1} Trend",
                                        f"{trend1.iloc[-1]:.1f}",
                                        f"{trend1.iloc[-1] - trend1.iloc[0]:.1f}"
                                    )
                                with col2:
                                    st.metric(
                                        f"{player2} Trend",
                                        f"{trend2.iloc[-1]:.1f}",
                                        f"{trend2.iloc[-1] - trend2.iloc[0]:.1f}"
                                    )
                            
                            # Add AI analysis
                            if st.button("Get AI Analysis"):
                                analysis_prompt = f"""
                                Compare {player1} and {player2} based on their last {time_range} games:
                                {player1}: {logs1[metrics].mean().to_dict()}
                                {player2}: {logs2[metrics].mean().to_dict()}
                                Which player has been performing better and why?
                                """
                                with st.spinner("Analyzing players..."):
                                    insight = generate_ai_insight(analysis_prompt)
                                    st.info(insight)
                        
                        except Exception as e:
                            st.error(f"Error comparing players: {e}")

elif page == "Props":
    st.title("Player Props Analysis")
    
    # Enhanced filters in expandable section
    with st.expander("Advanced Filters", expanded=True):
        filter_cols = st.columns([2,2,2,1])
        with filter_cols[0]:
            teams = st.multiselect("Teams", ["All Teams"] + list(HARDCODED_ROSTERS.keys()))
            positions = st.multiselect("Positions", ["All Positions", "G", "F", "C"])
        with filter_cols[1]:
            selected_props = st.multiselect("Prop Types", list(PROP_CATEGORIES.keys()))
            variations = st.multiselect("Variations", ["Over", "Under"], default=["Over", "Under"])
        with filter_cols[2]:
            min_threshold = st.number_input("Min Line", 0.5, 50.0, 0.5)
            min_ev_input = st.number_input("Min EV", -20.0, 20.0, 0.0)
        with filter_cols[3]:
            min_win_rate = st.slider("Min Win%", 0, 100, 50)
            show_hot = st.checkbox("🔥 Hot Only", False)

    # Process and display props
    all_props = []
    for team in (teams if teams and "All Teams" not in teams else HARDCODED_ROSTERS.keys()):
        players = fetch_team_players(team)
        for player in players:
            if positions and "All Positions" not in positions and player['position'] not in positions:
                continue
                
            # Fetch detailed player stats
            stats = fetch_player_stats(player['id'])
            game_logs = fetch_player_game_log(player['id'], 10)
            
            for prop_type in selected_props:
                for threshold in PROP_CATEGORIES[prop_type]["thresholds"]:
                    if threshold < min_threshold:
                        continue
                        
                    for variation in variations:
                        prop_key = prop_type.lower()
                        
                        # Calculate detailed metrics
                        last_5_games = game_logs[prop_key].tail(5)
                        last_10_games = game_logs[prop_key].tail(10)
                        
                        win_rate_5 = (
                            (last_5_games > threshold if variation == "Over" else last_5_games < threshold)
                            .mean() * 100
                        )
                        win_rate_10 = (
                            (last_10_games > threshold if variation == "Over" else last_10_games < threshold)
                            .mean() * 100
                        )
                        
                        if show_hot and win_rate_5 < 80:
                            continue
                            
                        if win_rate_5 < min_win_rate:
                            continue
                        
                        # Get odds and calculate EV
                        odds = 100  # Mock odds, replace with real odds API
                        implied_prob = calculate_implied_probability(odds)
                        ev = calculate_ev(odds, implied_prob)
                        
                        if ev < min_ev_input:
                            continue
                        
                        prop_data = {
                            "Player": player['name'],
                            "Team": team,
                            "Position": player['position'],
                            "Prop": f"{variation} {threshold} {prop_type}",
                            "Line": threshold,
                            "Odds": format_american_odds(odds),
                            "L5 Avg": f"{last_5_games.mean():.1f}",
                            "L10 Avg": f"{last_10_games.mean():.1f}",
                            "Win% L5": f"{win_rate_5:.0f}%",
                            "Win% L10": f"{win_rate_10:.0f}%",
                            "EV": ev,
                            "Trend": "🔥" if win_rate_5 >= 80 else ("📈" if win_rate_5 > win_rate_10 else "📉")
                        }
                        all_props.append(prop_data)
    
    # Update prop count
    total_props = len(all_props)
    st.session_state.prop_count = {'total': total_props, 'filtered': len(all_props)}
    
    # Display props table with enhanced formatting
    if all_props:
        props_df = pd.DataFrame(all_props)
        
        # Add sorting functionality
        sort_col = st.selectbox("Sort By", props_df.columns)
        sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)
        props_df = props_df.sort_values(sort_col, ascending=(sort_order == "Ascending"))
        
        # Display table with conditional formatting
        st.dataframe(
            props_df.style
            .apply(lambda x: [
                'background-color: lightgreen' if 'Win%' in col and float(str(val).strip('%')) >= 80
                else 'background-color: yellow' if 'Win%' in col and float(str(val).strip('%')) >= 60
                else 'background-color: lightcoral' if 'EV' in col and float(val) < 0
                else 'background-color: lightgreen' if 'EV' in col and float(val) > 0
                else '' for col, val in x.items()
            ], axis=1)
            .format({
                'Line': '{:.1f}',
                'EV': '${:.2f}',
                'L5 Avg': '{:.1f}',
                'L10 Avg': '{:.1f}'
            }),
            use_container_width=True
        )
        
        # Save functionality
        selected_rows = st.multiselect(
            "Select props to save",
            range(len(props_df)),
            format_func=lambda x: f"{props_df.iloc[x]['Player']} - {props_df.iloc[x]['Prop']}"
        )
        
        if st.button("Save Selected Props"):
            for idx in selected_rows:
                prop = props_df.iloc[idx].to_dict()
                if prop not in st.session_state.saved_props:
                    st.session_state.saved_props.append(prop)
            st.success(f"Saved {len(selected_rows)} props")
    else:
        st.info("No props found matching your criteria")

elif page == "EV+":
    st.title("Expected Value Analysis")
    ev_props = [p for p in st.session_state.saved_props if p['EV'] > 0]
    if ev_props:
        st.dataframe(pd.DataFrame(ev_props))
    else:
        st.info("No positive EV props saved yet")

# Auto-refresh control
st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Auto-refresh")
if auto_refresh:
    time.sleep(30)
    st.rerun()
