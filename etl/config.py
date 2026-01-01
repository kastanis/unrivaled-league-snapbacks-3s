"""League configuration constants."""

from datetime import date


class LeagueConfig:
    """Central configuration for league-wide constants."""

    # League Size
    NUM_MANAGERS = 8
    NUM_PLAYERS = 48  # Total Unrivaled Season 2 players
    PLAYERS_PER_MANAGER = 6  # 48 / 8

    # Draft
    DRAFT_ROUNDS = 6  # Each manager drafts 6 players
    TOTAL_DRAFT_PICKS = 48  # 8 managers × 6 rounds

    # Lineups
    ACTIVE_PLAYERS_PER_DAY = 3
    BENCH_PLAYERS_PER_MANAGER = 3  # 6 - 3

    # Season Dates
    SEASON_START = date(2026, 1, 5)
    SEASON_END = date(2026, 2, 27)

    # Tournament
    TOURNAMENT_BRACKET_SIZE = 8  # One player per manager


# For backward compatibility, create module-level constants
NUM_MANAGERS = LeagueConfig.NUM_MANAGERS
NUM_PLAYERS = LeagueConfig.NUM_PLAYERS
PLAYERS_PER_MANAGER = LeagueConfig.PLAYERS_PER_MANAGER
DRAFT_ROUNDS = LeagueConfig.DRAFT_ROUNDS
TOTAL_DRAFT_PICKS = LeagueConfig.TOTAL_DRAFT_PICKS
ACTIVE_PLAYERS_PER_DAY = LeagueConfig.ACTIVE_PLAYERS_PER_DAY
SEASON_START = LeagueConfig.SEASON_START
SEASON_END = LeagueConfig.SEASON_END
