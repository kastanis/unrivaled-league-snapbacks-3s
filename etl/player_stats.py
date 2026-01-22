"""Player statistics and analytics."""

import pandas as pd
from datetime import date, timedelta
from typing import Optional
from etl import data_loader


def calculate_player_averages(player_id: int, last_n_games: Optional[int] = None) -> dict:
    """
    Calculate player statistics averages.

    Args:
        player_id: Player ID
        last_n_games: If provided, calculate for last N games. Otherwise season average.

    Returns:
        Dictionary with averages
    """
    player_scores = data_loader.load_player_game_scores()

    if player_scores is None or player_scores.empty:
        return {
            'games_played': 0,
            'avg_fantasy_points': 0.0,
            'total_fantasy_points': 0.0
        }

    player_data = player_scores[player_scores['player_id'] == player_id]

    if player_data.empty:
        return {
            'games_played': 0,
            'avg_fantasy_points': 0.0,
            'total_fantasy_points': 0.0
        }

    # Filter out DNP games if status column exists
    if 'status' in player_data.columns:
        player_data = player_data[player_data['status'] == 'played']

    if player_data.empty:
        return {
            'games_played': 0,
            'avg_fantasy_points': 0.0,
            'total_fantasy_points': 0.0
        }

    # Sort by date
    if 'game_date' in player_data.columns:
        player_data = player_data.sort_values('game_date', ascending=False)

    # Filter to last N games if specified
    if last_n_games is not None:
        player_data = player_data.head(last_n_games)

    games_played = len(player_data)
    total_points = player_data['fantasy_points'].sum()
    avg_points = total_points / games_played if games_played > 0 else 0.0

    return {
        'games_played': games_played,
        'avg_fantasy_points': round(avg_points, 2),
        'total_fantasy_points': round(total_points, 2)
    }


def get_player_trend(player_id: int) -> str:
    """
    Determine if player is hot or cold based on recent performance.

    Args:
        player_id: Player ID

    Returns:
        'hot' (🔥), 'cold' (🧊), or 'neutral' (-)
    """
    recent = calculate_player_averages(player_id, last_n_games=3)
    season = calculate_player_averages(player_id)

    if recent['games_played'] < 2 or season['games_played'] < 5:
        return 'neutral'

    # Hot if recent avg is 20% better than season avg
    if recent['avg_fantasy_points'] > season['avg_fantasy_points'] * 1.2:
        return 'hot'

    # Cold if recent avg is 20% worse than season avg
    if recent['avg_fantasy_points'] < season['avg_fantasy_points'] * 0.8:
        return 'cold'

    return 'neutral'


def get_all_player_stats() -> pd.DataFrame:
    """
    Get comprehensive stats for all players who have played.

    Returns:
        DataFrame with player stats
    """
    player_scores = data_loader.load_player_game_scores()

    if player_scores is None or player_scores.empty:
        return pd.DataFrame()

    players = data_loader.load_players()

    # Calculate stats for each player
    player_stats = []

    for player_id in player_scores['player_id'].unique():
        player_info = players[players['player_id'] == player_id]

        if player_info.empty:
            continue

        season_stats = calculate_player_averages(player_id)
        recent_stats = calculate_player_averages(player_id, last_n_games=5)
        trend = get_player_trend(player_id)

        # Get last game points (excluding DNP)
        player_data = player_scores[player_scores['player_id'] == player_id]
        # Filter out DNP games if status column exists
        if 'status' in player_data.columns:
            player_data = player_data[player_data['status'] == 'played']
        if 'game_date' in player_data.columns:
            player_data = player_data.sort_values('game_date', ascending=False)
        last_game_points = player_data['fantasy_points'].iloc[0] if not player_data.empty else 0.0

        player_stats.append({
            'player_id': player_id,
            'player_name': player_info['player_name'].iloc[0],
            'team': player_info['team'].iloc[0],
            'games_played': season_stats['games_played'],
            'season_avg': season_stats['avg_fantasy_points'],
            'last_game_points': round(last_game_points, 2),
            'last_5_avg': recent_stats['avg_fantasy_points'],
            'total_points': season_stats['total_fantasy_points'],
            'trend': trend
        })

    if not player_stats:
        return pd.DataFrame()

    df = pd.DataFrame(player_stats)
    return df.sort_values('season_avg', ascending=False)
