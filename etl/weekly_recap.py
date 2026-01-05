"""Weekly/daily recap generator."""

import pandas as pd
from datetime import date
from typing import Optional, Dict, List
from etl import data_loader


def generate_daily_recap(game_date: date) -> Optional[Dict]:
    """
    Generate recap for a specific game date.

    Args:
        game_date: Date to generate recap for

    Returns:
        Dictionary with recap data or None if no data
    """
    # Load data
    player_scores = data_loader.load_player_game_scores()
    manager_scores = data_loader.load_manager_daily_scores()
    managers = data_loader.load_managers()
    players = data_loader.load_players()
    lineups = data_loader.load_lineups()

    if player_scores is None or player_scores.empty:
        return None

    # Filter to this date
    daily_player_scores = player_scores[player_scores['game_date'] == game_date]
    daily_manager_scores = manager_scores[manager_scores['game_date'] == game_date] if manager_scores is not None else pd.DataFrame()

    if daily_player_scores.empty:
        return None

    # Top scorer of the day
    top_scorer_row = daily_player_scores.loc[daily_player_scores['fantasy_points'].idxmax()]
    top_scorer_player = players[players['player_id'] == top_scorer_row['player_id']]

    top_scorer = {
        'player_name': top_scorer_player['player_name'].iloc[0] if not top_scorer_player.empty else 'Unknown',
        'team': top_scorer_player['team'].iloc[0] if not top_scorer_player.empty else 'Unknown',
        'fantasy_points': round(top_scorer_row['fantasy_points'], 2)
    }

    # Manager of the day
    manager_of_day = None
    if not daily_manager_scores.empty:
        # Aggregate by manager (in case multiple games on this date)
        manager_day_totals = daily_manager_scores.groupby('manager_id').agg({
            'total_points': 'sum',
            'active_players_count': 'sum'
        }).reset_index()

        top_manager_row = manager_day_totals.loc[manager_day_totals['total_points'].idxmax()]
        top_manager = managers[managers['manager_id'] == top_manager_row['manager_id']]

        manager_of_day = {
            'manager_name': top_manager['manager_name'].iloc[0] if not top_manager.empty else 'Unknown',
            'team_name': top_manager['team_name'].iloc[0] if not top_manager.empty else 'Unknown',
            'total_points': round(top_manager_row['total_points'], 2),
            'active_players_count': int(top_manager_row['active_players_count'])
        }

    # Biggest bench mistake (benched someone who scored high)
    biggest_mistake = None
    if lineups is not None and not lineups.empty:
        date_lineups = lineups[lineups['game_date'] == game_date]

        if not date_lineups.empty:
            # Get all benched players with their scores
            benched = date_lineups[date_lineups['status'] == 'bench']
            benched_scores = benched.merge(daily_player_scores, on='player_id', how='inner')

            if not benched_scores.empty:
                # Find highest scoring benched player
                worst_bench = benched_scores.loc[benched_scores['fantasy_points'].idxmax()]
                benched_player = players[players['player_id'] == worst_bench['player_id']]
                manager = managers[managers['manager_id'] == worst_bench['manager_id']]

                biggest_mistake = {
                    'manager_name': manager['manager_name'].iloc[0] if not manager.empty else 'Unknown',
                    'player_name': benched_player['player_name'].iloc[0] if not benched_player.empty else 'Unknown',
                    'fantasy_points': round(worst_bench['fantasy_points'], 2)
                }

    return {
        'game_date': game_date,
        'top_scorer': top_scorer,
        'manager_of_day': manager_of_day,
        'biggest_bench_mistake': biggest_mistake,
        'games_played': len(daily_player_scores)
    }


def get_recent_recaps(num_days: int = 3) -> List[Dict]:
    """
    Get recaps for the most recent N game days.

    Args:
        num_days: Number of recent game days to retrieve

    Returns:
        List of recap dictionaries
    """
    player_scores = data_loader.load_player_game_scores()

    if player_scores is None or player_scores.empty:
        return []

    # Get unique game dates, sorted descending
    game_dates = sorted(player_scores['game_date'].unique(), reverse=True)

    recaps = []
    for game_date in game_dates[:num_days]:
        recap = generate_daily_recap(game_date)
        if recap:
            recaps.append(recap)

    return recaps
