import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import altair as alt

def fetch_player_stats(player_name: str, last_n_games: int = 10) -> pd.DataFrame:
    """Return player stats for last N games"""
    dates = pd.date_range(end=datetime.now(), periods=last_n_games)
    
    # Player-specific base stats
    if 'Embiid' in player_name:
        base_stats = {'pts': 35, 'reb': 12, 'ast': 6}
    elif 'Giannis' in player_name:
        base_stats = {'pts': 32, 'reb': 11, 'ast': 5}
    else:
        base_stats = {'pts': 20, 'reb': 5, 'ast': 4}

    # Generate realistic stats with some variance
    data = []
    for date in dates:
        data.append({
            'date': date,
            'points': max(0, np.random.normal(base_stats['pts'], 5)),
            'rebounds': max(0, np.random.normal(base_stats['reb'], 3)),
            'assists': max(0, np.random.normal(base_stats['ast'], 2)),
            'player': player_name
        })
    
    return pd.DataFrame(data).round(1)

def calculate_kelly_criterion(probability: float, odds: float, bankroll: float = 1000) -> float:
    if odds <= 0:
        decimal_odds = 1 + (100 / abs(odds))
    else:
        decimal_odds = 1 + (odds / 100)
    q = 1 - probability
    kelly = (probability * (decimal_odds - 1) - q) / (decimal_odds - 1)
    return max(0, min(kelly * bankroll, bankroll * 0.05))  # Cap at 5% of bankroll

def create_performance_chart(stats_df: pd.DataFrame, metric: str) -> alt.Chart:
    base = alt.Chart(stats_df).encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y(f'{metric}:Q', title=metric.title()),
        tooltip=['date', metric]
    )
    
    line = base.mark_line(color='steelblue')
    points = base.mark_circle(color='steelblue')
    
    chart = (line + points).properties(
        width=600,
        height=300,
        title=f"{metric.title()} Over Time"
    ).interactive()
    
    return chart

def create_metrics_comparison(stats_df: pd.DataFrame) -> alt.Chart:
    # Melt the dataframe for multiple metrics
    metrics_df = stats_df.melt(
        id_vars=['date'], 
        value_vars=['points', 'rebounds', 'assists'],
        var_name='metric', 
        value_name='value'
    )
    
    chart = alt.Chart(metrics_df).mark_line().encode(
        x='date:T',
        y='value:Q',
        color='metric:N',
        tooltip=['date', 'metric', 'value']
    ).properties(
        width=600,
        height=300,
        title="Player Performance Metrics"
    ).interactive()
    
    return chart

def identify_middle_opportunities(odds_data: list) -> list:
    middles = []
    for game in odds_data:
        books = game.get('bookmakers', [])
        if len(books) < 2:
            continue
            
        spreads = {}
        for book in books:
            for market in book.get('markets', []):
                if market.get('key') == 'spreads':
                    for outcome in market.get('outcomes', []):
                        point = float(outcome.get('point', 0))
                        spreads[book['key']] = point
                        
        for book1 in spreads:
            for book2 in spreads:
                if book1 != book2:
                    if spreads[book1] > spreads[book2]:
                        middle_size = spreads[book1] - spreads[book2]
                        if middle_size > 0:
                            middles.append({
                                'game': f"{game['home_team']} vs {game['away_team']}",
                                'middle_size': middle_size,
                                'book1': f"{book1} ({spreads[book1]})",
                                'book2': f"{book2} ({spreads[book2]})"
                            })
    return middles

def generate_player_insights(player_stats: pd.DataFrame) -> dict:
    recent = player_stats.tail(5)
    insights = {
        'avg_points': recent['points'].mean(),
        'trend': 'up' if recent['points'].is_monotonic_increasing else 'down',
        'consistency': recent['points'].std(),
        'ceiling': recent['points'].max(),
        'floor': recent['points'].min()
    }
    return insights
