"""League standings calculation for season-long total points format."""

import pandas as pd
from datetime import datetime
from etl import data_loader


def calculate_standings() -> pd.DataFrame:
    """
    Calculate league standings based on season-long total points.

    Returns:
        DataFrame with manager_id, total_points, games_with_scores, avg_points_per_day, rank, last_updated
    """
    # Load manager daily scores
    manager_scores = data_loader.load_manager_daily_scores()

    if manager_scores is None or manager_scores.empty:
        # No scores yet, return standings with all managers tied at rank 1-N
        managers = data_loader.load_managers()
        standings_df = pd.DataFrame({
            'manager_id': managers['manager_id'],
            'total_points': 0.0,
            'games_with_scores': 0,
            'avg_points_per_day': 0.0,
            'last_updated': datetime.now()
        })
        # Assign ranks 1 through N (all tied at 0 points)
        standings_df['rank'] = range(1, len(standings_df) + 1)
        return standings_df

    # Group by manager and aggregate
    standings = manager_scores.groupby('manager_id').agg({
        'total_points': 'sum',
        'game_date': 'count'  # Number of days with scores
    }).reset_index()

    standings.columns = ['manager_id', 'total_points', 'games_with_scores']

    # Calculate average points per day
    standings['avg_points_per_day'] = (
        standings['total_points'] / standings['games_with_scores']
    ).fillna(0).round(2)

    # Round total points
    standings['total_points'] = standings['total_points'].round(2)

    # Rank by total points (descending)
    standings = standings.sort_values('total_points', ascending=False)
    standings['rank'] = range(1, len(standings) + 1)

    # Add timestamp
    standings['last_updated'] = datetime.now()

    # Ensure all managers are included (even with 0 scores)
    all_managers = data_loader.load_managers()

    for manager_id in all_managers['manager_id']:
        if manager_id not in standings['manager_id'].values:
            # Add manager with 0 scores
            new_row = pd.DataFrame([{
                'manager_id': manager_id,
                'total_points': 0.0,
                'games_with_scores': 0,
                'avg_points_per_day': 0.0,
                'rank': len(standings) + 1,
                'last_updated': datetime.now()
            }])
            standings = pd.concat([standings, new_row], ignore_index=True)

    # Re-sort and re-rank
    standings = standings.sort_values('total_points', ascending=False).reset_index(drop=True)
    standings['rank'] = range(1, len(standings) + 1)

    return standings


def update_standings() -> pd.DataFrame:
    """
    Calculate and save updated standings.

    Returns:
        Updated standings DataFrame
    """
    standings = calculate_standings()
    data_loader.save_standings(standings)

    return standings


def get_standings_with_details() -> pd.DataFrame:
    """
    Get standings with manager names and team names.

    Returns:
        DataFrame with standings merged with manager details
    """
    standings = data_loader.load_standings()

    if standings is None:
        # Calculate if not exists
        standings = update_standings()

    managers = data_loader.load_managers()

    # Merge with manager details
    standings_with_details = standings.merge(
        managers[['manager_id', 'manager_name', 'team_name']],
        on='manager_id',
        how='left'
    )

    # Reorder columns
    columns_order = [
        'rank',
        'manager_id',
        'manager_name',
        'team_name',
        'total_points',
        'games_with_scores',
        'avg_points_per_day',
        'last_updated'
    ]

    return standings_with_details[columns_order].sort_values('rank')


def get_manager_rank(manager_id: int) -> int:
    """
    Get current rank for a specific manager.

    Args:
        manager_id: Manager ID

    Returns:
        Current rank (1-8)
    """
    standings = data_loader.load_standings()

    if standings is None:
        return 0

    manager_standing = standings[standings['manager_id'] == manager_id]

    if manager_standing.empty:
        return 0

    return int(manager_standing['rank'].iloc[0])


def get_top_scorers(limit: int = 5) -> pd.DataFrame:
    """
    Get top scoring managers.

    Args:
        limit: Number of top managers to return

    Returns:
        DataFrame with top managers
    """
    standings = get_standings_with_details()

    return standings.head(limit)
