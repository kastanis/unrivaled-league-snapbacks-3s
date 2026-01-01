"""1-on-1 Tournament - Manager nominations and bracket."""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl import data_loader, draft_engine, standings_updater

st.set_page_config(page_title="Tournament", page_icon="🏆", layout="wide")

st.title("🏆 1-on-1 Tournament")

st.markdown("""
**Format:**
- Each manager nominates 1 player from their roster
- Seeding based on regular season standings (Rank #1 vs #8, #2 vs #7, etc.)
- Single elimination bracket
- **Head-to-head matchups:** Winner = player with most fantasy points in tournament round games
- Uses same scoring as regular season (points, rebounds, assists, steals, blocks, etc.)

*Note: Unrivaled 1-on-1 games track full stats, not just scoring - so fantasy points make sense!*
""")

st.divider()

# Load data
managers = data_loader.load_managers()
tournament_picks = data_loader.load_tournament_picks()

# Tabs
tab1, tab2, tab3 = st.tabs(["Make Nomination", "View Bracket", "Admin - Enter Results"])

with tab1:
    st.header("Nominate Your Player")

    # Manager selection
    manager_options = {
        f"{row['manager_name']} ({row['team_name']})": row['manager_id']
        for _, row in managers.iterrows()
    }

    selected_manager = st.selectbox(
        "Select Your Team:",
        options=["-- Select Manager --"] + list(manager_options.keys())
    )

    if selected_manager != "-- Select Manager --":
        manager_id = manager_options[selected_manager]

        # Check if already nominated
        if tournament_picks is not None:
            existing_pick = tournament_picks[tournament_picks['manager_id'] == manager_id]
        else:
            existing_pick = pd.DataFrame()

        if not existing_pick.empty:
            # Show current nomination
            player_id = existing_pick['player_id'].iloc[0]
            players = data_loader.load_players()
            player_result = players[players['player_id'] == player_id]['player_name']
            if player_result.empty:
                st.error(f"❌ Player ID {player_id} not found!")
                st.stop()

            player_name = player_result.iloc[0]
            st.success(f"✅ You have nominated: **{player_name}**")

            if st.button("Change Nomination"):
                # Remove existing pick
                if tournament_picks is not None:
                    updated_picks = tournament_picks[tournament_picks['manager_id'] != manager_id]
                    data_loader.save_tournament_picks(updated_picks)
                    st.success("Nomination cleared. Select a new player below.")
                    st.rerun()
        else:
            # Make nomination
            st.subheader("Select Player from Your Roster")

            roster = draft_engine.get_manager_roster(manager_id)

            if not roster.empty:
                player_options = {
                    f"{row['player_name']} ({row['team']})": row['player_id']
                    for _, row in roster.iterrows()
                }

                selected_player = st.selectbox(
                    "Choose Player:",
                    options=list(player_options.keys())
                )

                if st.button("Nominate This Player", type="primary"):
                    player_id = player_options[selected_player]

                    # Save nomination
                    if tournament_picks is None:
                        tournament_picks = pd.DataFrame()

                    new_pick = pd.DataFrame([{
                        'manager_id': manager_id,
                        'player_id': player_id,
                        'seed': 0  # Will be determined after all picks
                    }])

                    updated_picks = pd.concat([tournament_picks, new_pick], ignore_index=True)
                    data_loader.save_tournament_picks(updated_picks)

                    st.success(f"Player nominated! Seeding will be determined once all managers have picked.")
                    st.rerun()
            else:
                st.info("No roster found. Complete draft first.")

with tab2:
    st.header("Tournament Bracket")

    # Check if all nominations are in
    if tournament_picks is None or len(tournament_picks) < 8:
        remaining = 8 - (len(tournament_picks) if tournament_picks is not None else 0)
        st.info(f"Waiting for {remaining} more nomination(s)...")

        # Show who has picked
        if tournament_picks is not None and not tournament_picks.empty:
            st.subheader("Nominations Received:")
            picks_with_details = tournament_picks.merge(managers, on='manager_id')
            picks_with_details = picks_with_details.merge(
                data_loader.load_players()[['player_id', 'player_name']],
                on='player_id'
            )

            for _, row in picks_with_details.iterrows():
                st.write(f"✅ {row['team_name']}: {row['player_name']}")
    else:
        # All picks in - generate bracket
        st.success("All nominations received!")

        # Get standings for seeding
        standings = standings_updater.get_standings_with_details()

        if standings.empty or len(standings) < 8:
            st.warning("⚠️ Cannot generate bracket yet - standings not available or incomplete.")
            st.info("Standings will be available after the first game stats are uploaded.")
        else:
            # Assign seeds based on rank
            tournament_picks_with_seed = tournament_picks.copy()

            for _, row in tournament_picks_with_seed.iterrows():
                manager_id = row['manager_id']
                rank_result = standings[standings['manager_id'] == manager_id]['rank']
                if rank_result.empty:
                    st.error(f"❌ Manager ID {manager_id} not found in standings!")
                    st.stop()

                rank = rank_result.iloc[0]
                tournament_picks_with_seed.loc[
                    tournament_picks_with_seed['manager_id'] == manager_id,
                    'seed'
                ] = rank

            # Merge with player/manager names
            bracket = tournament_picks_with_seed.merge(managers, on='manager_id')
            bracket = bracket.merge(
                data_loader.load_players()[['player_id', 'player_name', 'team']],
                on='player_id'
            )

            bracket = bracket.sort_values('seed')

            # Verify we have all 8 seeds
            unique_seeds = bracket['seed'].unique()
            if len(unique_seeds) < 8 or not all(s in unique_seeds for s in range(1, 9)):
                st.error("⚠️ Bracket seeding error - not all seeds (1-8) are assigned.")
                st.info("This may happen if multiple managers have the same score. Upload more game stats to establish clear rankings.")
                st.dataframe(bracket[['seed', 'team_name', 'player_name']])
            else:
                st.subheader("Seeded Bracket")

                # Quarterfinals (8 teams)
                st.write("### Quarterfinals")
                st.caption("Winner = Player with highest fantasy points in Quarterfinal games (all stats count: points, rebounds, assists, steals, blocks, etc.)")

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Matchup 1**")
                    seed1_result = bracket[bracket['seed'] == 1]
                    seed8_result = bracket[bracket['seed'] == 8]
                    if seed1_result.empty or seed8_result.empty:
                        st.error("❌ Missing seed 1 or 8 in bracket!")
                    else:
                        seed1 = seed1_result.iloc[0]
                        seed8 = seed8_result.iloc[0]
                        st.write(f"(1) {seed1['team_name']} - {seed1['player_name']}")
                        st.write(f"(8) {seed8['team_name']} - {seed8['player_name']}")

                    st.write("**Matchup 2**")
                    seed4_result = bracket[bracket['seed'] == 4]
                    seed5_result = bracket[bracket['seed'] == 5]
                    if seed4_result.empty or seed5_result.empty:
                        st.error("❌ Missing seed 4 or 5 in bracket!")
                    else:
                        seed4 = seed4_result.iloc[0]
                        seed5 = seed5_result.iloc[0]
                        st.write(f"(4) {seed4['team_name']} - {seed4['player_name']}")
                        st.write(f"(5) {seed5['team_name']} - {seed5['player_name']}")

                with col2:
                    st.write("**Matchup 3**")
                    seed2_result = bracket[bracket['seed'] == 2]
                    seed7_result = bracket[bracket['seed'] == 7]
                    if seed2_result.empty or seed7_result.empty:
                        st.error("❌ Missing seed 2 or 7 in bracket!")
                    else:
                        seed2 = seed2_result.iloc[0]
                        seed7 = seed7_result.iloc[0]
                        st.write(f"(2) {seed2['team_name']} - {seed2['player_name']}")
                        st.write(f"(7) {seed7['team_name']} - {seed7['player_name']}")

                    st.write("**Matchup 4**")
                    seed3_result = bracket[bracket['seed'] == 3]
                    seed6_result = bracket[bracket['seed'] == 6]
                    if seed3_result.empty or seed6_result.empty:
                        st.error("❌ Missing seed 3 or 6 in bracket!")
                    else:
                        seed3 = seed3_result.iloc[0]
                        seed6 = seed6_result.iloc[0]
                        st.write(f"(3) {seed3['team_name']} - {seed3['player_name']}")
                        st.write(f"(6) {seed6['team_name']} - {seed6['player_name']}")

                st.divider()

                # Show full bracket table
                display_bracket = bracket[['seed', 'team_name', 'player_name']].copy()
                display_bracket.columns = ['Seed', 'Team', 'Player']

                st.dataframe(display_bracket, hide_index=True, use_container_width=True)

with tab3:
    st.header("Admin - Enter Tournament Results")

    st.markdown("""
    **How Tournament Works:**
    - Each round is head-to-head
    - Winner = Player who scores more fantasy points in that round's games
    - Example: In Quarterfinals, player with highest fantasy points in QF games wins and advances

    **Admin Instructions:**
    1. After each tournament round's games are complete
    2. Compare fantasy points for each matchup
    3. Record winners
    4. Winners advance to next round
    """)

    st.info("(Results tracking interface to be added - for now track manually)")
