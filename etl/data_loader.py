"""Data loading and saving utilities for CSV files."""

import pandas as pd
from pathlib import Path
from datetime import date
from typing import Optional
import streamlit as st

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HANDMADE_DIR = DATA_DIR / "handmade"
SOURCE_DIR = DATA_DIR / "source"
PROCESSED_DIR = DATA_DIR / "processed"
GAME_STATS_DIR = SOURCE_DIR / "game_stats"


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_players() -> pd.DataFrame:
    """Load player master list."""
    return pd.read_csv(HANDMADE_DIR / "players.csv")


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_managers() -> pd.DataFrame:
    """Load managers/fantasy teams."""
    return pd.read_csv(HANDMADE_DIR / "managers.csv")


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_scoring_config() -> pd.DataFrame:
    """Load fantasy scoring configuration."""
    return pd.read_csv(HANDMADE_DIR / "scoring_config.csv")


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_game_schedule() -> pd.DataFrame:
    """Load game schedule with times."""
    df = pd.read_csv(HANDMADE_DIR / "game_schedule.csv")
    df['game_date'] = pd.to_datetime(df['game_date']).dt.date
    df['game_time'] = pd.to_datetime(df['game_time'], format='%H:%M').dt.time
    return df


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_game_id_mapping() -> pd.DataFrame:
    """Load mapping between player_game_scores game_ids and schedule game_ids."""
    df = pd.read_csv(HANDMADE_DIR / "game_id_mapping.csv")
    df['game_date'] = pd.to_datetime(df['game_date']).dt.date
    return df


def load_draft_results() -> Optional[pd.DataFrame]:
    """Load draft results if exists."""
    path = PROCESSED_DIR / "draft_results.csv"
    if path.exists():
        return pd.read_csv(path)
    return None


def load_rosters() -> Optional[pd.DataFrame]:
    """Load current rosters if exists."""
    path = PROCESSED_DIR / "rosters.csv"
    if path.exists():
        df = pd.read_csv(path)
        df['acquisition_date'] = pd.to_datetime(df['acquisition_date']).dt.date
        return df
    return None


def load_lineups(game_date: Optional[date] = None) -> Optional[pd.DataFrame]:
    """Load lineups, optionally filtered by date."""
    path = PROCESSED_DIR / "lineups.csv"
    if not path.exists():
        return None

    df = pd.read_csv(path)

    # Handle empty file
    if df.empty:
        return None

    df['game_date'] = pd.to_datetime(df['game_date']).dt.date
    df['locked_at'] = pd.to_datetime(df['locked_at'], errors='coerce')

    if game_date:
        df = df[df['game_date'] == game_date]

    return df


def load_game_stats(game_date: Optional[date] = None) -> pd.DataFrame:
    """Load game stats, optionally filtered by date."""
    all_stats = []

    if game_date:
        # Load specific date's games
        pattern = f"{game_date}_game*.csv"
        files = list(GAME_STATS_DIR.glob(pattern))
    else:
        # Load all game stats
        files = list(GAME_STATS_DIR.glob("*_game*.csv"))

    for file in sorted(files):
        df = pd.read_csv(file)
        all_stats.append(df)

    if all_stats:
        return pd.concat(all_stats, ignore_index=True)
    return pd.DataFrame()


def load_player_game_scores() -> Optional[pd.DataFrame]:
    """Load calculated player fantasy points per game."""
    path = PROCESSED_DIR / "player_game_scores.csv"
    if path.exists():
        # Check if file is empty
        if path.stat().st_size == 0:
            return None
        try:
            df = pd.read_csv(path)
            if df.empty:
                return None
            df['game_date'] = pd.to_datetime(df['game_date']).dt.date
            return df
        except Exception:
            return None
    return None


def load_manager_daily_scores() -> Optional[pd.DataFrame]:
    """Load manager daily scores."""
    path = PROCESSED_DIR / "manager_daily_scores.csv"
    if path.exists():
        df = pd.read_csv(path)
        df['game_date'] = pd.to_datetime(df['game_date']).dt.date
        return df
    return None


def load_standings() -> Optional[pd.DataFrame]:
    """Load league standings."""
    path = PROCESSED_DIR / "standings.csv"
    if path.exists():
        df = pd.read_csv(path)
        df['last_updated'] = pd.to_datetime(df['last_updated'])
        return df
    return None


def load_tournament_picks() -> Optional[pd.DataFrame]:
    """Load tournament player selections."""
    path = PROCESSED_DIR / "tournament_picks.csv"
    if path.exists():
        return pd.read_csv(path)
    return None


def load_csv(file_path: Path) -> Optional[pd.DataFrame]:
    """Load CSV file with error handling for missing/empty files."""
    if not file_path.exists():
        return None

    try:
        # Check if file is empty
        if file_path.stat().st_size == 0:
            return None
        return pd.read_csv(file_path)
    except Exception:
        return None


def save_csv(df: pd.DataFrame, file_path: Path, index: bool = False) -> None:
    """Save dataframe to CSV with consistent formatting."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=index)


def save_draft_results(df: pd.DataFrame) -> None:
    """Save draft results."""
    save_csv(df, PROCESSED_DIR / "draft_results.csv")


def save_rosters(df: pd.DataFrame) -> None:
    """Save rosters."""
    save_csv(df, PROCESSED_DIR / "rosters.csv")


def save_lineups(df: pd.DataFrame) -> None:
    """Save lineups."""
    save_csv(df, PROCESSED_DIR / "lineups.csv")


def save_player_game_scores(df: pd.DataFrame) -> None:
    """Save player game scores."""
    save_csv(df, PROCESSED_DIR / "player_game_scores.csv")


def save_manager_daily_scores(df: pd.DataFrame) -> None:
    """Save manager daily scores."""
    save_csv(df, PROCESSED_DIR / "manager_daily_scores.csv")


def save_standings(df: pd.DataFrame) -> None:
    """Save standings."""
    save_csv(df, PROCESSED_DIR / "standings.csv")


def save_tournament_picks(df: pd.DataFrame) -> None:
    """Save tournament picks."""
    save_csv(df, PROCESSED_DIR / "tournament_picks.csv")


def save_game_stats(df: pd.DataFrame, game_date: date, game_num: int) -> None:
    """Save game stats to source directory."""
    filename = f"{game_date}_game{game_num}.csv"
    save_csv(df, GAME_STATS_DIR / filename)


def load_transaction_log() -> Optional[pd.DataFrame]:
    """Load transaction history log."""
    return load_csv(PROCESSED_DIR / "transaction_log.csv")


def save_transaction_log(df: pd.DataFrame) -> None:
    """Save transaction history log."""
    save_csv(df, PROCESSED_DIR / "transaction_log.csv")
