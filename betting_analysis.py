import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import altair as alt
from utils import calculate_ev, calculate_implied_probability
from sklearn.linear_model import LinearRegression
import numpy as np

def analyze_player_performance(stats_df: pd.DataFrame | dict, metric: str) -> dict:
    """Analyze player performance from either DataFrame or dictionary stats"""
    if isinstance(stats_df, dict):
        # If we have a single game stats dictionary
        return {
            'recent_trend': 'neutral',
            'last_5_avg': stats_df.get(metric, 0),
            'last_10_avg': stats_df.get(metric, 0),
            'consistency': 0,
            'peak': stats_df.get(metric, 0),
            'peak_date': pd.Timestamp.now(),
            'momentum': 0
        }
    
    # If we have historical stats DataFrame
    try:
        last_5 = stats_df.tail(5)
        last_10 = stats_df.tail(10)
        
        analysis = {
            'recent_trend': 'up' if last_5[metric].is_monotonic_increasing else 'down',
            'last_5_avg': last_5[metric].mean(),
            'last_10_avg': last_10[metric].mean(),
            'consistency': last_5[metric].std(),
            'peak': last_10[metric].max(),
            'peak_date': stats_df.loc[stats_df[metric].idxmax(), 'date'],
            'momentum': (last_5[metric].mean() - last_10[metric].mean()) / last_10[metric].mean()
        }
        return analysis
    except Exception as e:
        print(f"Error analyzing performance: {e}")
        return {
            'recent_trend': 'unknown',
            'last_5_avg': 0,
            'last_10_avg': 0,
            'consistency': 0,
            'peak': 0,
            'peak_date': pd.Timestamp.now(),
            'momentum': 0
        }

def find_high_ev_opportunities(odds_data: list, min_ev: float = 5.0) -> pd.DataFrame:
    if not odds_data:
        return pd.DataFrame()
        
    opportunities = []
    
    try:
        for game in odds_data:
            for book in game.get('bookmakers', []):
                for market in book.get('markets', []):
                    for outcome in market.get('outcomes', []):
                        try:
                            price = float(outcome.get('price', 0))
                            implied_prob = calculate_implied_probability(price)
                            ev = calculate_ev(price, implied_prob)
                            
                            if ev > min_ev:
                                opportunities.append({
                                    'game': f"{game['home_team']} vs {game['away_team']}",
                                    'bet_type': market.get('key', 'unknown'),
                                    'outcome': outcome.get('name', 'Unknown'),
                                    'odds': price,
                                    'bookmaker': book.get('title', 'Unknown'),
                                    'ev': ev,
                                    'implied_prob': implied_prob
                                })
                        except (ValueError, TypeError, KeyError) as e:
                            print(f"Error processing outcome: {e}")
                            continue
                            
        if not opportunities:
            # Return empty DataFrame with defined columns
            return pd.DataFrame(columns=[
                'game', 'bet_type', 'outcome', 'odds', 
                'bookmaker', 'ev', 'implied_prob'
            ])
            
        df = pd.DataFrame(opportunities)
        if 'ev' in df.columns:
            return df.sort_values('ev', ascending=False)
        return df
        
    except Exception as e:
        print(f"Error in find_high_ev_opportunities: {e}")
        return pd.DataFrame()

def create_comparison_chart(stats1: pd.DataFrame, stats2: pd.DataFrame, 
                          player1: str, player2: str, metric: str, 
                          add_trend: bool = True,
                          prediction_days: int = 5) -> alt.Chart:
    """Create an interactive comparison chart with trend lines and predictions"""
    
    def add_predictions(df: pd.DataFrame, days: int) -> pd.DataFrame:
        if len(df) < 3:  # Need at least 3 points for meaningful prediction
            return df
            
        # Convert dates to numeric (days since first game)
        df = df.copy()
        df['days'] = (df['date'] - df['date'].min()).dt.total_seconds() / (24*60*60)
        
        # Fit linear regression
        model = LinearRegression()
        X = df['days'].values.reshape(-1, 1)
        y = df[metric].values
        model.fit(X, y)
        
        # Generate future dates and predictions
        last_day = df['days'].max()
        future_days = np.linspace(last_day + 1, last_day + days, days)
        predictions = model.predict(future_days.reshape(-1, 1))
        
        # Create prediction DataFrame
        pred_df = pd.DataFrame({
            'date': pd.date_range(start=df['date'].max() + pd.Timedelta(days=1), periods=days),
            'days': future_days,
            metric: predictions,
            'type': 'prediction'
        })
        
        df['type'] = 'actual'
        return pd.concat([df, pred_df])
    
    # Prepare data with predictions
    df1 = add_predictions(stats1.copy(), prediction_days)
    df2 = add_predictions(stats2.copy(), prediction_days)
    df1['player'] = player1
    df2['player'] = player2
    
    # Combine data
    combined = pd.concat([df1, df2]).reset_index(drop=True)
    
    # Base chart
    base = alt.Chart(combined).encode(
        x=alt.X('date:T', title='Date',
                axis=alt.Axis(format='%b %d', labelAngle=-45)),
        color=alt.Color('player:N', legend=alt.Legend(title="Player"))
    )
    
    # Actual data lines and points
    actual_data = combined[combined['type'] == 'actual']
    lines = base.mark_line(size=2).encode(
        y=alt.Y(f'{metric}:Q', title=metric.title())
    ).transform_filter(
        alt.datum.type == 'actual'
    )
    
    points = base.mark_circle(size=60).encode(
        y=alt.Y(f'{metric}:Q'),
        tooltip=['date:T', metric, 'player']
    ).transform_filter(
        alt.datum.type == 'actual'
    )
    
    # Prediction lines
    pred_data = combined[combined['type'] == 'prediction']
    predictions = base.mark_line(
        strokeDash=[6, 6],
        stroke='red',
        size=2
    ).encode(
        y=alt.Y(f'{metric}:Q')
    ).transform_filter(
        alt.datum.type == 'prediction'
    )
    
    # Add trend lines if requested
    if add_trend:
        trend_lines = base.transform_regression(
            'date', metric,
            groupby=['player'],
            method='linear'
        ).mark_line(
            size=3,
            strokeDash=[5,5],
            opacity=0.5
        ).encode(
            y=alt.Y(f'{metric}:Q')
        ).transform_filter(
            alt.datum.type == 'actual'
        )
        chart = (lines + points + trend_lines + predictions)
    else:
        chart = (lines + points + predictions)
    
    return chart.properties(
        width=600,
        height=300,
        title=f"{metric.title()} Comparison - Last {len(stats1)} Games (with {prediction_days}-day prediction)"
    ).interactive()

def find_enhanced_middles(odds_data: list, min_middle: float = 1.0) -> list:
    middles = []
    
    for game in odds_data:
        spreads = {}
        totals = {}
        
        for book in game.get('bookmakers', []):
            for market in book.get('markets', []):
                if market.get('key') == 'spreads':
                    for outcome in market.get('outcomes', []):
                        spreads[f"{book['key']}_{outcome['name']}"] = {
                            'point': float(outcome.get('point', 0)),
                            'price': outcome.get('price', 0)
                        }
                elif market.get('key') == 'totals':
                    for outcome in market.get('outcomes', []):
                        totals[f"{book['key']}_{outcome['name']}"] = {
                            'point': float(outcome.get('point', 0)),
                            'price': outcome.get('price', 0)
                        }
        
        # Check for spread middles
        for book1 in spreads:
            for book2 in spreads:
                if book1 != book2:
                    middle_size = spreads[book1]['point'] - spreads[book2]['point']
                    if middle_size >= min_middle:
                        middles.append({
                            'game': f"{game['home_team']} vs {game['away_team']}",
                            'type': 'spread',
                            'middle_size': middle_size,
                            'book1': book1.split('_')[0],
                            'book2': book2.split('_')[0],
                            'line1': spreads[book1]['point'],
                            'line2': spreads[book2]['point'],
                            'odds1': spreads[book1]['price'],
                            'odds2': spreads[book2]['price']
                        })
        
        # Check for totals middles
        for book1 in totals:
            for book2 in totals:
                if book1 != book2:
                    middle_size = totals[book1]['point'] - totals[book2]['point']
                    if middle_size >= min_middle:
                        middles.append({
                            'game': f"{game['home_team']} vs {game['away_team']}",
                            'type': 'total',
                            'middle_size': middle_size,
                            'book1': book1.split('_')[0],
                            'book2': book2.split('_')[0],
                            'line1': totals[book1]['point'],
                            'line2': totals[book2]['point'],
                            'odds1': totals[book1]['price'],
                            'odds2': totals[book2]['price']
                        })
    
    return middles
