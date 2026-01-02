"""Snake draft engine for fantasy league."""

import pandas as pd
from datetime import datetime, date
from typing import List, Tuple
from etl import data_loader
from etl.config import DRAFT_ROUNDS, TOTAL_DRAFT_PICKS


def create_snake_order(manager_ids: List[int], num_rounds: int = 9) -> List[Tuple[int, int, int]]:
    """
    Generate snake draft order.

    Args:
        manager_ids: List of manager IDs in initial draft order
        num_rounds: Number of draft rounds (default: 9 for 9-player rosters)

    Returns:
        List of (pick_number, round, manager_id) tuples
    """
    draft_order = []
    pick_number = 1

    for round_num in range(1, num_rounds + 1):
        if round_num % 2 == 1:  # Odd rounds: normal order
            round_picks = manager_ids
        else:  # Even rounds: reversed order (snake)
            round_picks = list(reversed(manager_ids))

        for manager_id in round_picks:
            draft_order.append((pick_number, round_num, manager_id))
            pick_number += 1

    return draft_order


def execute_draft(draft_picks: List[Tuple[int, int]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Execute draft and create results.

    Args:
        draft_picks: List of (pick_number, player_id) tuples in order

    Returns:
        (draft_results_df, rosters_df)
    """
    managers = data_loader.load_managers()
    manager_ids = managers['manager_id'].tolist()

    # Generate snake order
    snake_order = create_snake_order(manager_ids, num_rounds=DRAFT_ROUNDS)

    # Build draft results
    draft_results = []
    for i, (pick_num, player_id) in enumerate(draft_picks):
        if i < len(snake_order):
            _, round_num, manager_id = snake_order[i]
            draft_results.append({
                'pick_number': pick_num,
                'round': round_num,
                'manager_id': manager_id,
                'player_id': player_id,
                'timestamp': datetime.now().isoformat()
            })

    draft_df = pd.DataFrame(draft_results)

    # Build rosters from draft
    rosters = []
    for _, row in draft_df.iterrows():
        rosters.append({
            'manager_id': row['manager_id'],
            'player_id': row['player_id'],
            'acquisition_type': 'draft',
            'acquisition_date': date.today()
        })

    rosters_df = pd.DataFrame(rosters)

    return draft_df, rosters_df


def save_draft(draft_df: pd.DataFrame, rosters_df: pd.DataFrame) -> None:
    """Save draft results and rosters."""
    data_loader.save_draft_results(draft_df)
    data_loader.save_rosters(rosters_df)


def get_available_players() -> pd.DataFrame:
    """Get players not yet drafted and not injured."""
    players = data_loader.load_players()

    # Filter out injured players
    if 'status' in players.columns:
        players = players[players['status'] != 'injured']

    rosters = data_loader.load_rosters()

    if rosters is None or rosters.empty:
        return players

    drafted_player_ids = rosters['player_id'].unique()
    available = players[~players['player_id'].isin(drafted_player_ids)]

    return available.sort_values('player_id')


def get_manager_roster(manager_id: int) -> pd.DataFrame:
    """Get roster for a specific manager with player details."""
    rosters = data_loader.load_rosters()

    if rosters is None:
        return pd.DataFrame()

    players = data_loader.load_players()

    manager_roster = rosters[rosters['manager_id'] == manager_id]
    roster_with_details = manager_roster.merge(players, on='player_id', how='left')

    return roster_with_details


def validate_draft_complete() -> bool:
    """Check if draft is complete."""
    draft_results = data_loader.load_draft_results()

    if draft_results is None:
        return False

    return len(draft_results) == TOTAL_DRAFT_PICKS
