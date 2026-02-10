"""1-on-1 Tournament - Manager picks and leaderboard."""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl import data_loader, score_calculator

st.set_page_config(page_title="Tournament", page_icon="🏆")

st.title("🏆 1-on-1 Tournament")

st.markdown("""
**Format:**
- Each manager picked 1 player for the Unrivaled 1-on-1 Tournament
- Scoring: Same as regular season **minus assists** (no AST points)
- **Winner:** Manager whose pick has the highest total fantasy points across all tournament rounds
""")

st.divider()

# Load data
managers = data_loader.load_managers()
players = data_loader.load_players()
tournament_picks = data_loader.load_tournament_picks()

# Tabs
tab1, tab2, tab3 = st.tabs(["Manager Picks", "Leaderboard", "Admin - Enter Stats"])

with tab1:
    st.header("Manager Picks")

    if tournament_picks is None or tournament_picks.empty:
        st.warning("No tournament picks have been recorded yet.")
    else:
        # Build display table
        picks_display = tournament_picks.merge(managers, on='manager_id')
        picks_display = picks_display.merge(
            players[['player_id', 'player_name', 'team']],
            on='player_id'
        )

        # Format for display
        display_df = picks_display[['team_name', 'player_name', 'team']].copy()
        display_df.columns = ['Fantasy Team', 'Player Pick', 'Unrivaled Team']

        st.dataframe(display_df, hide_index=True, use_container_width=True)

        st.info(f"**{len(tournament_picks)}** managers have made their picks.")

with tab2:
    st.header("Tournament Leaderboard")

    # Get leaderboard with error handling
    try:
        leaderboard = score_calculator.get_tournament_leaderboard()
    except Exception as e:
        st.error(f"Error loading leaderboard: {e}")
        leaderboard = pd.DataFrame()

    if leaderboard.empty:
        st.warning("No tournament picks or scores available yet.")
    else:
        # Check if any scores exist
        has_scores = 'total_fp' in leaderboard.columns and leaderboard['total_fp'].sum() > 0

        if not has_scores:
            st.info("Waiting for tournament stats to be uploaded...")

        # Build display columns
        display_cols = ['rank', 'team_name', 'player_name', 'team']

        # Add round columns if they exist
        round_cols = [c for c in leaderboard.columns if c.startswith('round_') and c.endswith('_fp')]
        round_cols_sorted = sorted(round_cols, key=lambda x: int(x.split('_')[1]))
        display_cols.extend(round_cols_sorted)

        display_cols.append('total_fp')

        # Filter to existing columns
        display_cols = [c for c in display_cols if c in leaderboard.columns]

        display_df = leaderboard[display_cols].copy()

        # Rename columns for display
        rename_map = {
            'rank': 'Rank',
            'team_name': 'Fantasy Team',
            'player_name': 'Player',
            'team': 'Unrivaled Team',
            'total_fp': 'Total FP'
        }
        # Add round renames
        for col in round_cols_sorted:
            round_num = col.split('_')[1]
            rename_map[col] = f'R{round_num}'

        display_df = display_df.rename(columns=rename_map)

        # Style the dataframe - highlight leader
        def highlight_leader(row):
            if row['Rank'] == 1 and has_scores:
                return ['background-color: #ffd700'] * len(row)
            return [''] * len(row)

        styled_df = display_df.style.apply(highlight_leader, axis=1)

        st.dataframe(styled_df, hide_index=True, use_container_width=True)

        if has_scores:
            leader = leaderboard.iloc[0]
            st.success(f"**Current Leader:** {leader['player_name']} ({leader['team_name']}) - {leader['total_fp']:.1f} FP")

with tab3:
    st.header("Admin - Enter Tournament Stats")

    st.markdown("""
    Upload stats for each tournament round. Stats should be in CSV format with columns:
    - `player_id` - Player ID (required)
    - `PTS` - Points scored
    - `REB` - Rebounds
    - `STL` - Steals
    - `BLK` - Blocks
    - `TOV` - Turnovers
    - `PF` - Personal fouls
    - `DUNK` - Dunks (optional)
    - `GAME_WINNER` - Game winner bonus (optional)

    **Note:** Assists (AST) are NOT counted in tournament scoring.
    """)

    # Round selection
    round_num = st.selectbox(
        "Select Round:",
        options=[1, 2, 3, 4, 5],
        format_func=lambda x: f"Round {x}"
    )

    # File upload
    uploaded_file = st.file_uploader(
        f"Upload Round {round_num} Stats (CSV)",
        type=['csv'],
        key=f"round_{round_num}_upload"
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            st.subheader("Preview")
            st.dataframe(df.head(10), use_container_width=True)

            # Validate required columns
            if 'player_id' not in df.columns:
                st.error("Missing required column: player_id")
            else:
                # Validate player IDs
                valid_player_ids = set(players['player_id'].tolist())
                uploaded_ids = set(df['player_id'].tolist())
                invalid_ids = uploaded_ids - valid_player_ids

                if invalid_ids:
                    st.error(f"Invalid player IDs: {invalid_ids}")
                else:
                    # Calculate fantasy points preview
                    df_with_round = df.copy()
                    df_with_round['round'] = round_num

                    scores = score_calculator.calculate_tournament_fantasy_points(df_with_round)

                    # Merge with player names for display
                    scores_display = scores.merge(
                        players[['player_id', 'player_name']],
                        on='player_id'
                    )
                    scores_display = scores_display[['player_name', 'fantasy_points']].sort_values(
                        'fantasy_points', ascending=False
                    )
                    scores_display.columns = ['Player', 'Fantasy Points']

                    st.subheader(f"Calculated Fantasy Points (Round {round_num})")
                    st.dataframe(scores_display, hide_index=True, use_container_width=True)

                    # Save button
                    if st.button(f"Save Round {round_num} Stats", type="primary"):
                        # Save the stats
                        data_loader.save_tournament_game_stats(df_with_round, round_num)

                        # Recalculate all tournament scores
                        score_calculator.update_tournament_scores()

                        st.success(f"Round {round_num} stats saved and scores updated!")
                        st.rerun()

        except Exception as e:
            st.error(f"Error reading file: {e}")

    # Show existing stats
    st.divider()
    st.subheader("Uploaded Rounds")

    existing_stats = data_loader.load_tournament_game_stats()

    if existing_stats.empty:
        st.info("No tournament stats uploaded yet.")
    else:
        rounds_uploaded = sorted(existing_stats['round'].unique())
        st.write(f"**Rounds with stats:** {', '.join([f'Round {r}' for r in rounds_uploaded])}")

        # Show summary per round
        for r in rounds_uploaded:
            round_stats = existing_stats[existing_stats['round'] == r]
            st.caption(f"Round {r}: {len(round_stats)} player entries")
