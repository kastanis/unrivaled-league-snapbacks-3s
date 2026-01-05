"""Admin Portal - Run draft, upload stats, manage league."""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import date
import pandas as pd
import io
import zipfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl import data_loader, draft_engine, score_calculator, standings_updater
from etl.config import DRAFT_ROUNDS, TOTAL_DRAFT_PICKS

st.set_page_config(page_title="Admin Portal", page_icon="⚙️")

st.title("⚙️ Admin Portal")

# Backup/Restore section at the top
st.info("💾 **Data Backup:** Download all data before pushing code changes to prevent data loss on redeploy")

col1, col2 = st.columns(2)

with col1:
    if st.button("📦 Download All Data (Zip)", type="primary", use_container_width=True):
        # Create zip file in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Define all files to backup
            processed_dir = Path(__file__).parent.parent.parent / "data/processed"
            source_dir = Path(__file__).parent.parent.parent / "data/source"

            # Add all processed CSVs
            for csv_file in processed_dir.glob("*.csv"):
                if csv_file.exists() and csv_file.stat().st_size > 0:
                    zip_file.write(csv_file, f"processed/{csv_file.name}")

            # Add game stats
            game_stats_dir = source_dir / "game_stats"
            if game_stats_dir.exists():
                for stats_file in game_stats_dir.glob("*.csv"):
                    if stats_file.exists() and stats_file.stat().st_size > 0:
                        zip_file.write(stats_file, f"source/game_stats/{stats_file.name}")

        zip_buffer.seek(0)

        st.download_button(
            label="⬇️ Click to Download",
            data=zip_buffer,
            file_name=f"fantasy_league_backup_{date.today()}.zip",
            mime="application/zip"
        )

with col2:
    uploaded_zip = st.file_uploader("📤 Upload Backup Zip", type="zip", key="backup_zip")

    if uploaded_zip is not None:
        if st.button("Restore Data from Zip", use_container_width=True):
            try:
                with zipfile.ZipFile(uploaded_zip, 'r') as zip_file:
                    base_dir = Path(__file__).parent.parent.parent / "data"

                    # Extract all files
                    for file_info in zip_file.filelist:
                        # Get the relative path
                        relative_path = file_info.filename
                        target_path = base_dir / relative_path

                        # Create parent directories if needed
                        target_path.parent.mkdir(parents=True, exist_ok=True)

                        # Extract file
                        with zip_file.open(file_info) as source, open(target_path, 'wb') as target:
                            target.write(source.read())

                st.success("✅ All data restored successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error restoring data: {e}")

st.divider()

# Tabs for admin functions
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Run Draft", "Upload Stats", "View All Rosters", "Recalculate Scores", "Injury Report", "Manage Lineups"])

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
            temp_file = Path(__file__).parent.parent.parent / "data/processed/draft_temp.json"

            if draft_file.exists():
                os.remove(draft_file)
            if roster_file.exists():
                os.remove(roster_file)
            if temp_file.exists():
                os.remove(temp_file)

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
            # Try to load from temp file (recover from interruption)
            temp_file = Path(__file__).parent.parent.parent / "data/processed/draft_temp.json"
            if temp_file.exists():
                import json
                try:
                    with open(temp_file, 'r') as f:
                        saved_draft = json.load(f)
                        st.session_state.draft_picks = [tuple(pick) for pick in saved_draft['picks']]
                        st.session_state.draft_order = saved_draft['order']
                        st.info(f"📥 Recovered draft progress: {len(st.session_state.draft_picks)} picks")
                except Exception:
                    st.session_state.draft_picks = []
                    st.session_state.draft_order = managers['manager_id'].tolist()
            else:
                st.session_state.draft_picks = []
                st.session_state.draft_order = managers['manager_id'].tolist()

        # Show current draft order with randomize option
        current_pick_num = len(st.session_state.draft_picks) + 1

        if current_pick_num == 1:
            # Show draft order and randomize button before first pick
            st.info("**Draft Order:**")
            order_display = []
            for idx, mgr_id in enumerate(st.session_state.draft_order, 1):
                mgr_name = managers[managers['manager_id'] == mgr_id]['manager_name'].iloc[0]
                order_display.append(f"{idx}. {mgr_name}")
            st.write(" → ".join(order_display))

            if st.button("🎲 Randomize Draft Order"):
                import random
                st.session_state.draft_order = random.sample(managers['manager_id'].tolist(), len(managers))
                st.rerun()

            st.divider()

        # Generate snake order
        snake_order = draft_engine.create_snake_order(st.session_state.draft_order, num_rounds=DRAFT_ROUNDS)

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

            # Filter out injured players
            if 'status' in available.columns:
                available = available[available['status'] != 'injured']

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

                # Auto-save draft progress (recover from interruption)
                import json
                temp_file = Path(__file__).parent.parent.parent / "data/processed/draft_temp.json"
                with open(temp_file, 'w') as f:
                    json.dump({
                        'picks': st.session_state.draft_picks,
                        'order': st.session_state.draft_order
                    }, f)

                st.rerun()

            # Show draft progress
            st.progress(current_pick_num / 48, text=f"{current_pick_num} / 48 picks")

        else:
            # Draft complete!
            st.success("Draft complete! Save results below.")

            if st.button("Save Draft Results"):
                draft_df, rosters_df = draft_engine.execute_draft(
                    st.session_state.draft_picks,
                    st.session_state.draft_order
                )
                draft_engine.save_draft(draft_df, rosters_df)

                # Delete temp file
                temp_file = Path(__file__).parent.parent.parent / "data/processed/draft_temp.json"
                if temp_file.exists():
                    os.remove(temp_file)

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
                required_cols = ['game_id', 'player_id', 'PTS',
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
                        stat_cols = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'PF', 'DUNK']
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
    - `PTS` - Total points scored
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
        'PTS': 19,
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

with tab5:
    st.header("Injury Report")

    st.info("View player injury status. To update injury status, edit data/handmade/players.csv directly. Injured players cannot be drafted or set in lineups.")

    # Load players
    players = data_loader.load_players()
    rosters = data_loader.load_rosters()
    managers = data_loader.load_managers()

    if not players.empty:
        # Create tabs for different views
        injury_tab1, injury_tab2 = st.tabs(["All Players", "Currently Injured"])

        with injury_tab1:
            st.subheader("All Players Status")

            # Add search/filter
            search = st.text_input("🔍 Search player name:", "")

            filtered_players = players.copy()
            if search:
                filtered_players = filtered_players[
                    filtered_players['player_name'].str.contains(search, case=False, na=False)
                ]

            # Display players (read-only)
            for idx, player in filtered_players.iterrows():
                col1, col2, col3 = st.columns([4, 3, 3])

                with col1:
                    st.write(f"**{player['player_name']}**")

                with col2:
                    st.caption(player['team'])

                with col3:
                    current_status = player['status']
                    status_emoji = "✅" if current_status == 'active' else "🔴"
                    st.write(f"{status_emoji} {current_status.title()}")

        with injury_tab2:
            st.subheader("Currently Injured Players")

            injured = players[players['status'] == 'injured']

            if not injured.empty:
                # Show which managers are affected
                for _, player in injured.iterrows():
                    col1, col2, col3 = st.columns([4, 3, 3])

                    with col1:
                        st.write(f"**🔴 {player['player_name']}**")

                    with col2:
                        st.caption(player['team'])

                    with col3:
                        # Check if player is on a roster
                        if rosters is not None:
                            player_roster = rosters[rosters['player_id'] == player['player_id']]

                            if not player_roster.empty:
                                manager_id = player_roster['manager_id'].iloc[0]
                                manager = managers[managers['manager_id'] == manager_id]

                                if not manager.empty:
                                    st.caption(f"Owned by: {manager['team_name'].iloc[0]}")
                            else:
                                st.caption("Not drafted")
                        else:
                            st.caption("Draft incomplete")
            else:
                st.success("✅ No injured players! Everyone is healthy.")

    else:
        st.error("No players found. Check data/handmade/players.csv")

with tab6:
    st.header("Manage Lineups")

    st.warning("⚠️ **Important:** Before pushing any code changes, download lineups to preserve them across redeploys!")

    # Load lineups
    lineups = data_loader.load_lineups()

    if lineups is not None and not lineups.empty:
        st.success(f"Found {len(lineups)} lineup entries")

        # Download button
        csv = lineups.to_csv(index=False)
        st.download_button(
            label="📥 Download lineups.csv",
            data=csv,
            file_name="lineups.csv",
            mime="text/csv",
            help="Download current lineups before pushing code to prevent data loss"
        )

        st.divider()

        # Show lineups by manager
        st.subheader("Current Lineups")

        managers = data_loader.load_managers()
        players = data_loader.load_players()

        # Get unique dates
        unique_dates = sorted(lineups['game_date'].unique(), reverse=True)

        for game_date in unique_dates:
            with st.expander(f"📅 Lineups for {game_date}"):
                date_lineups = lineups[lineups['game_date'] == game_date]

                for _, manager in managers.iterrows():
                    manager_lineup = date_lineups[date_lineups['manager_id'] == manager['manager_id']]

                    if not manager_lineup.empty:
                        st.write(f"**{manager['team_name']}** ({manager['manager_name']})")

                        # Merge with player details (use suffixes to avoid column name conflicts)
                        # lineups 'status' = active/bench, players 'status' = active/injured
                        lineup_with_players = manager_lineup.merge(
                            players,
                            on='player_id',
                            how='left',
                            suffixes=('_lineup', '_injury')
                        )

                        # Show active players
                        active = lineup_with_players[lineup_with_players['status_lineup'] == 'active']
                        if not active.empty:
                            st.caption("Active:")
                            for _, p in active.iterrows():
                                st.write(f"  ✅ {p['player_name']} ({p['team']})")

                        # Show bench players
                        bench = lineup_with_players[lineup_with_players['status_lineup'] == 'bench']
                        if not bench.empty:
                            with st.expander("View Bench"):
                                for _, p in bench.iterrows():
                                    st.caption(f"  {p['player_name']} ({p['team']})")

                        st.divider()
    else:
        st.info("No lineups set yet. Managers can set lineups in the Manager Portal.")

    st.divider()

    st.subheader("Upload Lineups")
    st.caption("Use this to restore lineups after downloading them before a code push")

    uploaded_lineups = st.file_uploader("Upload lineups.csv", type="csv", key="lineups_upload")

    if uploaded_lineups is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_lineups)

            st.write("Preview:")
            st.dataframe(uploaded_df.head(), use_container_width=True)

            if st.button("Save Uploaded Lineups"):
                # Validate columns
                required_cols = ['lineup_id', 'manager_id', 'game_date', 'player_id', 'status', 'locked_at']
                missing_cols = [col for col in required_cols if col not in uploaded_df.columns]

                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                else:
                    # Convert game_date to proper format
                    uploaded_df['game_date'] = pd.to_datetime(uploaded_df['game_date']).dt.date

                    # Save
                    data_loader.save_lineups(uploaded_df)
                    st.success("✅ Lineups uploaded successfully!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {e}")
