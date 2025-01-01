import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import openai
import os
from dotenv import load_dotenv
from functools import lru_cache, wraps

load_dotenv()

SPORT_KEYS = {
    'NBA': 'basketball_nba',
    'NFL': 'americanfootball_nfl',
    'NCAAF': 'americanfootball_ncaaf',
    'MLB': 'baseball_mlb',
    'NHL': 'icehockey_nhl'
}

@lru_cache(maxsize=32)
def fetch_odds_data(sport):
    try:
        api_key = os.getenv('THE_ODDS_API_KEY')
        sport_key = SPORT_KEYS.get(sport.upper(), sport.lower())
        
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
        response = requests.get(url, params={
            'apiKey': api_key,
            'regions': 'us',
            'markets': 'h2h,spreads',
            'oddsFormat': 'american'
        })
        
        if response.status_code != 200:
            return []
            
        data = response.json()
        return [format_game_data(game) for game in data if isinstance(game, dict)]
        
    except Exception as e:
        print(f"API Error: {e}")
        return []

def format_game_data(game):
    odds_h2h = {}
    if game.get('bookmakers'):
        for book in game['bookmakers']:
            for market in book.get('markets', []):
                if market.get('key') == 'h2h':
                    for outcome in market.get('outcomes', []):
                        team_name = outcome.get('name', '')
                        odds_h2h[f"odds_{team_name}"] = float(outcome.get('price', 0))

    return {
        'id': str(game.get('id', '')),
        'sport': str(game.get('sport_key', '')),
        'commence_time': str(game.get('commence_time', '')),
        'home_team': str(game.get('home_team', '')),
        'away_team': str(game.get('away_team', '')),
        **odds_h2h  # Unpack team-specific odds
    }

def extract_odds(bookmakers):
    if not bookmakers:
        return 0
    for book in bookmakers:
        for market in book.get('markets', []):
            for outcome in market.get('outcomes', []):
                return float(outcome.get('price', 0))
    return 0

def calculate_implied_probability(odds: float) -> float:
    """Calculate implied probability from American odds"""
    if odds > 0:
        return round(100 / (odds + 100), 3)
    else:
        return round(abs(odds) / (abs(odds) + 100), 3)

def calculate_ev(odds: float, prob_winning: float, bet_amount: float = 100) -> float:
    """Calculate EV for a bet
    Args:
        odds: American odds (e.g., +150, -110)
        prob_winning: Your estimated probability of winning (0-1)
        bet_amount: Amount betting
    Returns:
        Expected value in dollars
    """
    if odds > 0:
        win_amount = (odds/100) * bet_amount
    else:
        win_amount = (100/abs(odds)) * bet_amount
    
    ev = (prob_winning * win_amount) - ((1 - prob_winning) * bet_amount)
    return round(ev, 2)

def format_american_odds(odds: float) -> str:
    """Format American odds with +/- prefix"""
    if odds > 0:
        return f"+{odds:0.0f}"
    return f"{odds:0.0f}"

def generate_ai_insight(query, context=None):
    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        messages = [
            {"role": "system", "content": "You are a sports betting analytics expert."},
            {"role": "user", "content": query}
        ]
        if context:
            messages.insert(1, {"role": "system", "content": context})
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150
        )
        return response.choices[0].message['content']
    except:
        return "AI insight unavailable"

def format_historical_data(data):
    return pd.DataFrame(data).sort_values('date', ascending=False)
