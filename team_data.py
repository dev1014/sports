from nba_api.stats.endpoints import commonteamroster, playercareerstats, teaminfocommon, boxscoreadvancedv2, leaguegamefinder
from nba_api.stats.static import teams, players
from typing import Dict, List
import pandas as pd
import time
from datetime import datetime, timedelta

# Cache team IDs
TEAM_IDS = {team['full_name']: team['id'] for team in teams.get_teams()}

def get_team_id(team_name: str) -> int:
    """Get NBA team ID from team name"""
    try:
        # Try exact match first
        if team_name in TEAM_IDS:
            return TEAM_IDS[team_name]
        
        # Try partial match
        for full_name, team_id in TEAM_IDS.items():
            if team_name.lower() in full_name.lower():
                return team_id
        return None
    except Exception as e:
        print(f"Error getting team ID: {e}")
        return None

def fetch_team_players(team_name: str) -> List[Dict]:
    """Fetch current team roster from NBA API"""
    try:
        team_id = get_team_id(team_name)
        if not team_id:
            print(f"Team not found: {team_name}")
            return []
            
        # Get roster
        roster = commonteamroster.CommonTeamRoster(team_id=team_id)
        players_df = roster.get_data_frames()[0]
        
        # Format player data with safe field access
        player_list = []
        for _, player in players_df.iterrows():
            try:
                player_data = {
                    'id': str(player.get('PLAYER_ID', '')),
                    'name': str(player.get('PLAYER', '')),
                    'position': str(player.get('POSITION', 'N/A')),
                    'number': str(player.get('NUM', '')),
                    'height': str(player.get('HEIGHT', '')),
                    'weight': str(player.get('WEIGHT', '')),
                    'experience': str(player.get('SEASON_EXP', '0')),
                    'team_id': str(team_id)
                }
                
                # Only add player if we have valid ID and name
                if player_data['id'] and player_data['name']:
                    player_list.append(player_data)
                    
            except Exception as e:
                print(f"Error processing player data: {e}")
                continue
            
            time.sleep(0.1)  # Rate limiting
        
        if not player_list:
            # Fallback to hardcoded rosters if API fails
            return HARDCODED_ROSTERS.get(team_name, [])
            
        return player_list
        
    except Exception as e:
        print(f"Error fetching team roster: {e}")
        # Fallback to hardcoded rosters
        return HARDCODED_ROSTERS.get(team_name, [])

# Hardcoded rosters for fallback
HARDCODED_ROSTERS = {
    'Philadelphia 76ers': [
        {'id': '203954', 'name': 'Joel Embiid', 'position': 'C'},
        {'id': '1629875', 'name': 'Tyrese Maxey', 'position': 'G'},
        {'id': '202699', 'name': 'Tobias Harris', 'position': 'F'},
        {'id': '203115', 'name': 'Kelly Oubre Jr.', 'position': 'F'},
        {'id': '1629678', 'name': 'De\'Anthony Melton', 'position': 'G'}
    ],
    'Milwaukee Bucks': [
        {'id': '203507', 'name': 'Giannis Antetokounmpo', 'position': 'F'},
        {'id': '203081', 'name': 'Damian Lillard', 'position': 'G'},
        {'id': '201572', 'name': 'Brook Lopez', 'position': 'C'},
        {'id': '203114', 'name': 'Khris Middleton', 'position': 'F'},
        {'id': '1627749', 'name': 'Malik Beasley', 'position': 'G'}
    ]
}

def fetch_player_stats(player_id: str) -> Dict:
    """Fetch comprehensive player stats"""
    try:
        from nba_api.stats.endpoints import playergamelog, playervsplayer
        
        # Get recent games
        game_logs = playergamelog.PlayerGameLog(player_id=player_id)
        logs_df = game_logs.get_data_frames()[0].head(10)
        
        if logs_df.empty:
            return get_mock_stats(player_id)
            
        # Calculate averages and trends
        stats = {
            'points': float(logs_df['PTS'].mean()),
            'rebounds': float(logs_df['REB'].mean()),
            'assists': float(logs_df['AST'].mean()),
            'blocks': float(logs_df['BLK'].mean()),
            'steals': float(logs_df['STL'].mean()),
            'threes_made': float(logs_df['FG3M'].mean()),
            'last_games': logs_df.to_dict('records'),
            'games_played': len(logs_df),
            'trends': {
                'points_trend': 'up' if logs_df['PTS'].is_monotonic_increasing else 'down',
                'reb_trend': 'up' if logs_df['REB'].is_monotonic_increasing else 'down',
                'ast_trend': 'up' if logs_df['AST'].is_monotonic_increasing else 'down'
            },
            'last_5': {
                'points': float(logs_df.head(5)['PTS'].mean()),
                'rebounds': float(logs_df.head(5)['REB'].mean()),
                'assists': float(logs_df.head(5)['AST'].mean())
            }
        }
        
        return stats
        
    except Exception as e:
        print(f"Error fetching player stats: {e}")
        return get_mock_stats(player_id)

def get_mock_stats(player_id: str) -> Dict:
    """Return mock stats for a player"""
    return {
        'points': 0.0,
        'rebounds': 0.0,
        'assists': 0.0,
        'last_games': [],
        'games_played': 0
    }

def fetch_player_game_log(player_id: str, last_n_games: int = 10) -> pd.DataFrame:
    """Fetch player's recent game logs"""
    try:
        from nba_api.stats.endpoints import playergamelog
        
        # Get game logs for current season
        game_logs = playergamelog.PlayerGameLog(player_id=player_id)
        logs_df = game_logs.get_data_frames()[0]
        
        # Get last N games
        recent_games = logs_df.head(last_n_games)
        
        # NBA API returns dates in format 'MMM DD, YYYY'
        # Convert date format with explicit format
        return pd.DataFrame({
            'date': pd.to_datetime(recent_games['GAME_DATE'], format='%b %d, %Y'),
            'points': recent_games['PTS'],
            'rebounds': recent_games['REB'],
            'assists': recent_games['AST'],
            'opponent': recent_games['MATCHUP'],
            'minutes': recent_games['MIN']
        })
        
    except Exception as e:
        print(f"Error fetching game logs: {e}")
        # Return empty DataFrame with correct column types
        return pd.DataFrame({
            'date': pd.Series(dtype='datetime64[ns]'),
            'points': pd.Series(dtype='float64'),
            'rebounds': pd.Series(dtype='float64'),
            'assists': pd.Series(dtype='float64'),
            'opponent': pd.Series(dtype='str'),
            'minutes': pd.Series(dtype='float64')
        })

def get_team_stats(team_name: str) -> Dict:
    """Get team's current season stats"""
    try:
        team_id = get_team_id(team_name)
        if not team_id:
            return {}
            
        team_info = teaminfocommon.TeamInfoCommon(team_id=team_id)
        stats_df = team_info.get_data_frames()[0]
        
        return {
            'wins': int(stats_df['W'].iloc[0]),
            'losses': int(stats_df['L'].iloc[0]),
            'win_pct': float(stats_df['PCT'].iloc[0]),
            'conf_rank': int(stats_df['CONF_RANK'].iloc[0]),
            'home_record': stats_df['HOME_RECORD'].iloc[0],
            'away_record': stats_df['ROAD_RECORD'].iloc[0]
        }
        
    except Exception as e:
        print(f"Error fetching team stats: {e}")
        return {}

def fetch_game_props(game_id: str) -> Dict:
    """Fetch available props and odds for a game"""
    try:
        # Get game info
        game = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=game_id)
        player_stats = game.get_data_frames()[0]
        
        # Format props data
        props = {}
        for _, player in player_stats.iterrows():
            player_name = player['PLAYER_NAME']
            
            # Points props
            points_line = player['PTS'] * 0.9  # Conservative estimate
            props[f"{player_name}_Points"] = {
                'line': round(points_line, 1),
                'over_odds': 100,  # Mock odds - replace with real odds API
                'under_odds': -120
            }
            
            # Rebounds props
            reb_line = player['REB'] * 0.9
            props[f"{player_name}_Rebounds"] = {
                'line': round(reb_line, 1),
                'over_odds': -110,
                'under_odds': -110
            }
            
            # Assists props
            ast_line = player['AST'] * 0.9
            props[f"{player_name}_Assists"] = {
                'line': round(ast_line, 1),
                'over_odds': -105,
                'under_odds': -115
            }
        
        return props
        
    except Exception as e:
        print(f"Error fetching game props: {e}")
        return {}

def get_game_id_from_teams(home_team: str, away_team: str) -> str:
    """Get NBA game ID from team names"""
    try:
        games = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=get_team_id(home_team),
            season_nullable="2023-24"
        ).get_data_frames()[0]
        
        # Find matching game
        game = games[
            (games['MATCHUP'].str.contains(away_team, case=False)) &
            (games['GAME_DATE'] >= (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
        ]
        
        if not game.empty:
            return str(game.iloc[0]['GAME_ID'])
        return None
        
    except Exception as e:
        print(f"Error finding game ID: {e}")
        return None
