"""Lineup management, validation, and locking logic."""

import pandas as pd
from datetime import datetime, date, time, timedelta
from typing import List, Optional
from etl import data_loader
from etl.config import ACTIVE_PLAYERS_PER_DAY


def get_lineup_lock_time(game_date: date) -> Optional[datetime]:
    """
    Get the lineup lock time for a given date (first game of the day).

    Args:
        game_date: Date to check

    Returns:
        datetime when lineups lock, or None if no games scheduled
    """
    schedule = data_loader.load_game_schedule()

    games_today = schedule[schedule['game_date'] == game_date]

    if games_today.empty:
        # No games scheduled, lock at end of day
        return datetime.combine(game_date, time(23, 59, 59))

    # Find earliest game time
    first_game_time = games_today['game_time'].min()

    return datetime.combine(game_date, first_game_time)


def is_lineup_locked(game_date: date) -> bool:
    """
    Check if lineups are locked for a given date.

    Args:
        game_date: Date to check

    Returns:
        True if locked (past lock time), False otherwise
    """
    # Past dates are always locked
    if game_date < date.today():
        return True

    lock_time = get_lineup_lock_time(game_date)

    if lock_time is None:
        return False

    return datetime.now() >= lock_time


def get_time_until_lock(game_date: date) -> Optional[timedelta]:
    """
    Get time remaining until lineup locks.

    Args:
        game_date: Date to check

    Returns:
        timedelta until lock, or None if already locked
    """
    if is_lineup_locked(game_date):
        return None

    lock_time = get_lineup_lock_time(game_date)

    if lock_time is None:
        return None

    return lock_time - datetime.now()


def validate_lineup(manager_id: int, active_player_ids: List[int]) -> tuple[bool, str]:
    """
    Validate a lineup meets requirements.

    Args:
        manager_id: Manager setting lineup
        active_player_ids: List of player IDs to set as active

    Returns:
        (is_valid, error_message)
    """
    # Check exactly required number of active players
    if len(active_player_ids) != ACTIVE_PLAYERS_PER_DAY:
        return False, f"Must select exactly {ACTIVE_PLAYERS_PER_DAY} active players (selected: {len(active_player_ids)})"

    # Check for duplicates
    if len(active_player_ids) != len(set(active_player_ids)):
        return False, "Duplicate players in lineup"

    # Check all players are on manager's roster
    rosters = data_loader.load_rosters()

    if rosters is None:
        return False, "No rosters found - complete draft first"

    manager_roster = rosters[rosters['manager_id'] == manager_id]
    roster_player_ids = manager_roster['player_id'].tolist()

    for player_id in active_player_ids:
        if player_id not in roster_player_ids:
            return False, f"Player {player_id} not on your roster"

    return True, ""


def get_manager_lineup(manager_id: int, game_date: date) -> pd.DataFrame:
    """
    Get a manager's lineup for a specific date.

    Args:
        manager_id: Manager ID
        game_date: Date to get lineup for

    Returns:
        DataFrame with lineup (empty if not set)
    """
    lineups = data_loader.load_lineups(game_date)

    if lineups is None or lineups.empty:
        return pd.DataFrame()

    manager_lineup = lineups[lineups['manager_id'] == manager_id]

    # Merge with player details (use suffixes to avoid column conflicts)
    # lineups has 'status' = active/bench, players has 'status' = active/injured
    if not manager_lineup.empty:
        players = data_loader.load_players()
        manager_lineup = manager_lineup.merge(
            players,
            on='player_id',
            how='left',
            suffixes=('', '_injury')  # Keep lineup status as 'status', rename player status
        )

    return manager_lineup


def save_lineup(manager_id: int, game_date: date, active_player_ids: List[int]) -> tuple[bool, str]:
    """
    Save a manager's lineup for a date.

    Args:
        manager_id: Manager setting lineup
        game_date: Date lineup applies to
        active_player_ids: List of 3 player IDs to set as active

    Returns:
        (success, message)
    """
    # Check if locked
    if is_lineup_locked(game_date):
        return False, f"Lineups locked for {game_date}"

    # Validate lineup
    is_valid, error_msg = validate_lineup(manager_id, active_player_ids)
    if not is_valid:
        return False, error_msg

    # Get manager's full roster
    rosters = data_loader.load_rosters()

    if rosters is None or rosters.empty:
        return False, "No rosters found - complete draft first"

    manager_roster = rosters[rosters['manager_id'] == manager_id]
    roster_player_ids = manager_roster['player_id'].tolist()

    # Load existing lineups
    all_lineups = data_loader.load_lineups()

    if all_lineups is None or all_lineups.empty:
        all_lineups = pd.DataFrame()
    else:
        # Remove this manager's lineup for this date (only if data exists)
        all_lineups = all_lineups[
            ~((all_lineups['manager_id'] == manager_id) &
              (all_lineups['game_date'] == game_date))
        ]

    # Build new lineup entries
    new_lineup_entries = []
    lineup_id_start = all_lineups['lineup_id'].max() + 1 if not all_lineups.empty else 1

    for i, player_id in enumerate(roster_player_ids):
        status = 'active' if player_id in active_player_ids else 'bench'
        new_lineup_entries.append({
            'lineup_id': lineup_id_start + i,
            'manager_id': manager_id,
            'game_date': game_date,
            'player_id': player_id,
            'status': status,
            'locked_at': datetime.now().isoformat()
        })

    new_lineup_df = pd.DataFrame(new_lineup_entries)

    # Combine and save
    updated_lineups = pd.concat([all_lineups, new_lineup_df], ignore_index=True)
    data_loader.save_lineups(updated_lineups)

    return True, f"Lineup saved for {game_date}"


def get_active_players_for_scoring(manager_id: int, game_date: date) -> List[int]:
    """
    Get list of active player IDs for a manager on a date.

    Uses "sticky lineup" logic:
    - If lineup exists for this date, use it
    - Otherwise, use previous day's lineup (if exists)
    - Otherwise, default to first 3 players by ID

    Args:
        manager_id: Manager ID
        game_date: Date to check

    Returns:
        List of player IDs set as active
    """
    lineup = get_manager_lineup(manager_id, game_date)

    if not lineup.empty and 'status' in lineup.columns and 'player_id' in lineup.columns:
        # Lineup exists for this date
        active = lineup[lineup['status'] == 'active']
        return active['player_id'].tolist()

    # No lineup for today - look for most recent previous lineup
    all_lineups = data_loader.load_lineups()

    if all_lineups is not None and not all_lineups.empty and 'manager_id' in all_lineups.columns:
        manager_lineups = all_lineups[all_lineups['manager_id'] == manager_id]

        if 'game_date' in all_lineups.columns:
            past_lineups = manager_lineups[manager_lineups['game_date'] < game_date]

            if not past_lineups.empty:
                # Get most recent previous date
                most_recent_date = past_lineups['game_date'].max()

                # Get active players from that date
                if 'status' in all_lineups.columns and 'player_id' in all_lineups.columns:
                    recent_lineup = all_lineups[
                        (all_lineups['manager_id'] == manager_id) &
                        (all_lineups['game_date'] == most_recent_date) &
                        (all_lineups['status'] == 'active')
                    ]

                    if not recent_lineup.empty:
                        return recent_lineup['player_id'].tolist()

    # No previous lineup - default to first N players by ID
    from etl import draft_engine
    roster = draft_engine.get_manager_roster(manager_id)

    if not roster.empty:
        return roster.sort_values('player_id')['player_id'].head(ACTIVE_PLAYERS_PER_DAY).tolist()

    return []
