import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def fetch_historical_data(player_name, prop_type, num_games=10):
    # Mock historical data - replace with actual API call
    dates = pd.date_range(end=datetime.now(), periods=num_games).tolist()
    mock_data = []
    for date in dates:
        mock_data.append({
            'date': date,
            'player': player_name,
            'prop_type': prop_type,
            'value': np.random.normal(20, 5),  # Mock statistics
            'opponent': f"Team {np.random.randint(1, 30)}",
            'result': np.random.choice(['Over', 'Under'])
        })
    return pd.DataFrame(mock_data)

def calculate_opponent_rank(team_name):
    # Mock opponent rankings - replace with actual data
    rankings = {f"Team {i}": i for i in range(1, 31)}
    return rankings.get(team_name, 15)

def identify_arbitrage_opportunities(odds_data):
    opportunities = []
    for game in odds_data:
        if len(game.get('bookmakers', [])) > 1:
            best_odds = {'home': -1000, 'away': -1000}
            for book in game['bookmakers']:
                for outcome in book.get('markets', [{}])[0].get('outcomes', []):
                    if outcome['price'] > best_odds[outcome['name'].lower()]:
                        best_odds[outcome['name'].lower()] = outcome['price']
            
            # Check for arbitrage
            if best_odds['home'] > 0 and best_odds['away'] > 0:
                prob_sum = (100/best_odds['home'] + 100/best_odds['away'])
                if prob_sum < 1:
                    opportunities.append({
                        'game': f"{game['home_team']} vs {game['away_team']}",
                        'best_home': best_odds['home'],
                        'best_away': best_odds['away'],
                        'profit': (1 - prob_sum) * 100
                    })
    return opportunities

def get_trending_props():
    # Mock trending props data
    return [{
        'player': 'Player A',
        'prop': 'Points',
        'line': 20.5,
        'trend': 'Up',
        'last_5': [18, 22, 25, 21, 24]
    }]

def format_ev_display(ev_value):
    color = 'green' if ev_value > 0 else 'red'
    return f"<span style='color: {color}'>${ev_value:.2f}</span>"
