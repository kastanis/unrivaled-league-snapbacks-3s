"""Fantasy points calculation engine."""

import pandas as pd
from datetime import date
from typing import Optional
from etl import data_loader, lineup_manager


def calculate_player_fantasy_points(game_stats: pd.DataFrame, scoring_config: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Calculate fantasy points for players based on game stats.

    Args:
        game_stats: DataFrame with player stats (columns match scoring_config stat_category)
        scoring_config: Optional scoring config (loads from file if not provided)

    Returns:
        DataFrame with player_id, game_id, game_date, fantasy_points
    """
    if scoring_config is None:
        scoring_config = data_loader.load_scoring_config()

    # Create scoring dictionary
    scoring_dict = dict(zip(
        scoring_config['stat_category'],
        scoring_config['points_per_unit']
    ))

    # Calculate fantasy points
    game_stats = game_stats.copy()
    game_stats['fantasy_points'] = 0.0

    for stat_category, points_per_unit in scoring_dict.items():
        if stat_category in game_stats.columns:
            game_stats['fantasy_points'] += game_stats[stat_category].fillna(0) * points_per_unit

    # Return essential columns
    result_columns = ['game_id', 'player_id', 'fantasy_points']

    # Add game_date if available
    if 'game_date' in game_stats.columns:
        result_columns.insert(2, 'game_date')

    return game_stats[result_columns]


def calculate_manager_daily_scores(game_date: date) -> pd.DataFrame:
    """
    Calculate total fantasy points for each manager on a specific date.

    Args:
        game_date: Date to calculate scores for

    Returns:
        DataFrame with manager_id, game_date, total_points, active_players_count
    """
    # Load player game scores for this date
    player_scores = data_loader.load_player_game_scores()

    if player_scores is None or player_scores.empty:
        return pd.DataFrame()

    daily_scores = player_scores[player_scores['game_date'] == game_date]

    if daily_scores.empty:
        return pd.DataFrame()

    # Get all managers
    managers = data_loader.load_managers()

    # Calculate scores for each manager
    manager_daily_scores = []

    for _, manager in managers.iterrows():
        manager_id = manager['manager_id']

        # Get active players for this manager/date
        active_player_ids = lineup_manager.get_active_players_for_scoring(manager_id, game_date)

        if not active_player_ids:
            # No lineup set, score is 0
            manager_daily_scores.append({
                'manager_id': manager_id,
                'game_date': game_date,
                'total_points': 0.0,
                'active_players_count': 0
            })
            continue

        # Filter to active players who actually played
        manager_scores = daily_scores[daily_scores['player_id'].isin(active_player_ids)]

        total_points = manager_scores['fantasy_points'].sum()
        active_count = len(manager_scores)

        manager_daily_scores.append({
            'manager_id': manager_id,
            'game_date': game_date,
            'total_points': round(total_points, 2),
            'active_players_count': active_count
        })

    return pd.DataFrame(manager_daily_scores)


def update_scores_for_date(game_date: date) -> None:
    """
    Recalculate all scores for a specific date.

    Args:
        game_date: Date to update scores for
    """
    # Load game stats for this date
    game_stats = data_loader.load_game_stats(game_date)

    if game_stats.empty:
        print(f"No game stats found for {game_date}")
        return

    # Auto-create default lineups for managers who have never set one
    # This ensures all managers have a visible lineup and uses sticky logic for future days
    created_count = lineup_manager.auto_create_missing_lineups(game_date)
    if created_count > 0:
        print(f"Auto-created default lineups for {created_count} manager(s)")

    # Add game_date column if not present
    if 'game_date' not in game_stats.columns:
        game_stats['game_date'] = game_date

    # Calculate player fantasy points
    player_scores = calculate_player_fantasy_points(game_stats)

    # Load existing player scores
    all_player_scores = data_loader.load_player_game_scores()

    if all_player_scores is None:
        all_player_scores = pd.DataFrame()

    # Remove old scores for this date (only if data exists)
    if not all_player_scores.empty and 'game_date' in all_player_scores.columns:
        all_player_scores = all_player_scores[all_player_scores['game_date'] != game_date]

    # Add new scores
    updated_player_scores = pd.concat([all_player_scores, player_scores], ignore_index=True)
    data_loader.save_player_game_scores(updated_player_scores)

    # Calculate manager daily scores
    manager_scores = calculate_manager_daily_scores(game_date)

    # Load existing manager daily scores
    all_manager_scores = data_loader.load_manager_daily_scores()

    if all_manager_scores is None:
        all_manager_scores = pd.DataFrame()

    # Remove old scores for this date (only if data exists)
    if not all_manager_scores.empty and 'game_date' in all_manager_scores.columns:
        all_manager_scores = all_manager_scores[all_manager_scores['game_date'] != game_date]

    # Add new scores
    updated_manager_scores = pd.concat([all_manager_scores, manager_scores], ignore_index=True)
    data_loader.save_manager_daily_scores(updated_manager_scores)

    print(f"Scores updated for {game_date}")
    print(f"  - {len(player_scores)} player game scores calculated")
    print(f"  - {len(manager_scores)} manager daily scores calculated")


def update_all_scores() -> None:
    """
    Recalculate all scores from all game stats.

    Processes all games in /data/source/game_stats/ and recalculates:
    - player_game_scores.csv
    - manager_daily_scores.csv
    """
    # Load all game stats
    all_game_stats = data_loader.load_game_stats()

    if all_game_stats.empty:
        print("No game stats found")
        return

    # Get unique dates
    if 'game_date' not in all_game_stats.columns:
        print("Warning: game_date column missing from game stats")
        # Try to parse from game_id or filename
        # For now, just warn
        return

    game_dates = all_game_stats['game_date'].unique()

    print(f"Recalculating scores for {len(game_dates)} game dates...")

    # Clear existing scores
    data_loader.save_player_game_scores(pd.DataFrame())
    data_loader.save_manager_daily_scores(pd.DataFrame())

    # Recalculate for each date
    for game_date in sorted(game_dates):
        update_scores_for_date(game_date)

    print("All scores recalculated successfully")


def get_player_recent_scores(player_id: int, num_games: int = 5) -> pd.DataFrame:
    """
    Get recent fantasy scores for a player.

    Args:
        player_id: Player ID
        num_games: Number of recent games to return

    Returns:
        DataFrame with recent game scores
    """
    player_scores = data_loader.load_player_game_scores()

    if player_scores is None:
        return pd.DataFrame()

    player_recent = player_scores[player_scores['player_id'] == player_id]
    player_recent = player_recent.sort_values('game_date', ascending=False).head(num_games)

    return player_recent
