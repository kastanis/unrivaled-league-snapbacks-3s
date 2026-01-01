"""Admin Portal - Run draft, upload stats, manage league."""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import date
import pandas as pd
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl import data_loader, draft_engine, score_calculator, standings_updater
from etl.config import DRAFT_ROUNDS, TOTAL_DRAFT_PICKS

st.set_page_config(page_title="Admin Portal", page_icon="⚙️", layout="wide")

st.title("⚙️ Admin Portal")

# Tabs for admin functions
tab1, tab2, tab3, tab4 = st.tabs(["Run Draft", "Upload Stats", "View All Rosters", "Recalculate Scores"])

with tab1:
    st.header("Run Draft")

    # Check if draft already complete
    if draft_engine.validate_draft_complete():
        st.success("✅ Draft is complete!")

        draft_results = data_loader.load_draft_results()
        if draft_results is not None:
            st.subheader("Draft Results")
            st.dataframe(draft_results, hide_index=True, use_container_width=True)

        if st.button("Clear Draft and Start Over"):
            # Clear draft files
            draft_file = Path(__file__).parent.parent.parent / "data/processed/draft_results.csv"
            roster_file = Path(__file__).parent.parent.parent / "data/processed/rosters.csv"

            if draft_file.exists():
                os.remove(draft_file)
            if roster_file.exists():
                os.remove(roster_file)

            st.success("Draft cleared! Refresh to start new draft.")
            st.rerun()
    else:
        st.info("Draft not started. Use the simple draft interface below.")

        st.subheader("Simple Draft Interface")

        # Load managers and players
        managers = data_loader.load_managers()
        players = data_loader.load_players()

        # Initialize draft state
        if 'draft_picks' not in st.session_state:
            st.session_state.draft_picks = []
            st.session_state.draft_order = managers['manager_id'].tolist()

        # Generate snake order
        snake_order = draft_engine.create_snake_order(st.session_state.draft_order, num_rounds=DRAFT_ROUNDS)

        current_pick_num = len(st.session_state.draft_picks) + 1

        if current_pick_num <= TOTAL_DRAFT_PICKS:
            # Get current pick info
            _, round_num, manager_id = snake_order[current_pick_num - 1]
            manager_result = managers[managers['manager_id'] == manager_id]['manager_name']
            if manager_result.empty:
                st.error(f"❌ Manager ID {manager_id} not found!")
                st.stop()

            manager_name = manager_result.iloc[0]
            st.write(f"**Pick #{current_pick_num}** - Round {round_num} - {manager_name}")

            # Get available players
            drafted_ids = [pid for _, pid in st.session_state.draft_picks]
            available = players[~players['player_id'].isin(drafted_ids)]

            # Player selection
            player_options = {
                f"{row['player_name']} ({row['team']})": row['player_id']
                for _, row in available.iterrows()
            }

            selected_player = st.selectbox(
                "Select Player:",
                options=list(player_options.keys())
            )

            if st.button("Make Pick"):
                player_id = player_options[selected_player]
                st.session_state.draft_picks.append((current_pick_num, player_id))
                st.rerun()

            # Show draft progress
            st.progress(current_pick_num / 48, text=f"{current_pick_num} / 48 picks")

        else:
            # Draft complete!
            st.success("Draft complete! Save results below.")

            if st.button("Save Draft Results"):
                draft_df, rosters_df = draft_engine.execute_draft(st.session_state.draft_picks)
                draft_engine.save_draft(draft_df, rosters_df)
                st.success("Draft saved!")
                st.session_state.draft_picks = []
                st.rerun()

with tab2:
    st.header("Upload Game Stats")

    # Show game schedule for reference
    with st.expander("📅 View Game Schedule (for game_id reference)"):
        schedule = data_loader.load_game_schedule()
        if not schedule.empty:
            st.dataframe(schedule, hide_index=True, use_container_width=True)
        else:
            st.info("No games in schedule yet. Add games to data/handmade/game_schedule.csv")

    st.subheader("Upload CSV File")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            st.write("Preview:")
            st.dataframe(df.head(), use_container_width=True)

            # Get game info
            game_date = st.date_input(
                "Game Date:",
                value=date.today()
            )

            game_num = st.number_input("Game Number (for this date):", min_value=1, value=1)

            if st.button("Save Stats and Calculate Scores"):
                # Validate required columns
                required_cols = ['game_id', 'player_id', '1PT_MADE', '2PT_MADE', 'FT_MADE',
                                 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'GAME_WINNER', 'DUNK']
                missing_cols = [col for col in required_cols if col not in df.columns]

                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                    st.info("Check the required CSV format below.")
                else:
                    # Validate player IDs
                    players = data_loader.load_players()
                    valid_player_ids = set(players['player_id'].tolist())
                    invalid_ids = set(df['player_id'].unique()) - valid_player_ids

                    if invalid_ids:
                        st.error(f"❌ Invalid player IDs found: {invalid_ids}")
                        st.info("Player IDs must be between 1-48. Check data/handmade/players.csv")
                    else:
                        # Validate no negative stats (except TOV which has negative scoring)
                        stat_cols = ['1PT_MADE', '2PT_MADE', 'FT_MADE', 'REB', 'AST', 'STL', 'BLK', 'PF', 'DUNK']
                        for col in stat_cols:
                            if (df[col] < 0).any():
                                st.warning(f"⚠️ Warning: Negative values found in {col} column")

                        # Add game_date column if not present
                        if 'game_date' not in df.columns:
                            df['game_date'] = game_date

                        # Save game stats
                        data_loader.save_game_stats(df, game_date, game_num)

                        # Calculate scores
                        score_calculator.update_scores_for_date(game_date)

                        # Update standings
                        standings_updater.update_standings()

                        st.success(f"✅ Stats saved and scores updated for {game_date}!")

        except Exception as e:
            st.error(f"Error reading file: {e}")

    st.divider()

    st.subheader("Required CSV Format")
    st.markdown("""
    Your CSV must have these columns:
    - `game_id` - Unique game identifier
    - `player_id` - Player ID (1-48)
    - `1PT_MADE` - One-point field goals made
    - `2PT_MADE` - Two-point field goals made
    - `FT_MADE` - Free throws made
    - `REB` - Total rebounds
    - `AST` - Assists
    - `STL` - Steals
    - `BLK` - Blocks
    - `TOV` - Turnovers
    - `PF` - Personal fouls
    - `GAME_WINNER` - 1 if scored game winner, 0 otherwise
    - `DUNK` - Number of dunks

    **Optional:** `game_date` (will be added automatically if missing)
    """)

    # Example CSV download
    example_df = pd.DataFrame([{
        'game_id': 1,
        'player_id': 43,
        '1PT_MADE': 2,
        '2PT_MADE': 6,
        'FT_MADE': 3,
        'REB': 8,
        'AST': 4,
        'STL': 2,
        'BLK': 1,
        'TOV': 2,
        'PF': 2,
        'GAME_WINNER': 0,
        'DUNK': 1
    }])

    csv = example_df.to_csv(index=False)
    st.download_button(
        label="Download Example CSV",
        data=csv,
        file_name="example_game_stats.csv",
        mime="text/csv"
    )

with tab3:
    st.header("View All Rosters")

    rosters = data_loader.load_rosters()
    managers = data_loader.load_managers()
    players = data_loader.load_players()

    if rosters is not None and not rosters.empty:
        for _, manager in managers.iterrows():
            with st.expander(f"{manager['team_name']} ({manager['manager_name']})"):
                manager_roster = draft_engine.get_manager_roster(manager['manager_id'])

                if not manager_roster.empty:
                    display = manager_roster[['player_name', 'team']].copy()
                    display.columns = ['Player', 'Unrivaled Team']
                    st.dataframe(display, hide_index=True, use_container_width=True)
    else:
        st.info("No rosters found. Complete draft first.")

with tab4:
    st.header("Recalculate Scores")

    st.warning("This will recalculate ALL scores from scratch. Use this if you need to fix errors or update scoring config.")

    if st.button("Recalculate All Scores", type="primary"):
        with st.spinner("Recalculating scores..."):
            score_calculator.update_all_scores()
            standings_updater.update_standings()

        st.success("All scores recalculated and standings updated!")

    st.divider()

    st.subheader("Calculate Scores for Specific Date")

    calc_date = st.date_input("Select Date:", value=date.today())

    if st.button("Calculate for This Date"):
        with st.spinner(f"Calculating scores for {calc_date}..."):
            score_calculator.update_scores_for_date(calc_date)
            standings_updater.update_standings()

        st.success(f"Scores updated for {calc_date}!")
