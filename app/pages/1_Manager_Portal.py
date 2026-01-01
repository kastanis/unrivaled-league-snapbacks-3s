"""Manager Portal - View roster, set lineups, check scores."""

import streamlit as st
import sys
from pathlib import Path
from datetime import date, timedelta
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl import data_loader, draft_engine, lineup_manager, standings_updater, score_calculator
from etl.config import SEASON_START, SEASON_END, ACTIVE_PLAYERS_PER_DAY

st.set_page_config(page_title="Manager Portal", page_icon="👤", layout="wide")

st.title("👤 Manager Portal")

# Manager selection
managers = data_loader.load_managers()

if 'selected_manager_id' not in st.session_state:
    st.session_state.selected_manager_id = None

manager_options = {
    f"{row['manager_name']} ({row['team_name']})": row['manager_id']
    for _, row in managers.iterrows()
}

selected_option = st.selectbox(
    "Select Your Team:",
    options=["-- Select Manager --"] + list(manager_options.keys()),
    index=0 if st.session_state.selected_manager_id is None else
          list(manager_options.values()).index(st.session_state.selected_manager_id) + 1
)

if selected_option != "-- Select Manager --":
    manager_id = manager_options[selected_option]
    st.session_state.selected_manager_id = manager_id

    # Get manager details
    manager_result = managers[managers['manager_id'] == manager_id]
    if manager_result.empty:
        st.error(f"❌ Manager ID {manager_id} not found in system!")
        st.stop()

    manager_row = manager_result.iloc[0]
    st.subheader(f"Welcome, {manager_row['manager_name']}!")
    st.caption(f"Team: {manager_row['team_name']}")

    # Check if draft is complete
    if not draft_engine.validate_draft_complete():
        st.warning("⚠️ Draft not complete yet. Contact the admin to run the draft!")
        st.stop()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["My Roster", "Set Lineup", "My Scores", "Standings"])

    with tab1:
        st.header("My Roster")

        roster = draft_engine.get_manager_roster(manager_id)

        if not roster.empty:
            display_roster = roster[['player_name', 'team', 'status']].copy()
            display_roster.columns = ['Player', 'Unrivaled Team', 'Status']

            st.dataframe(display_roster, hide_index=True, use_container_width=True)
        else:
            st.info("No roster found. Contact admin.")

    with tab2:
        st.header("Set Daily Lineup")

        # Date selector (default to today or season start, whichever is later)
        default_date = max(date.today(), SEASON_START)

        lineup_date = st.date_input(
            "Select Date:",
            value=default_date,
            min_value=SEASON_START,
            max_value=SEASON_END
        )

        # Check if locked
        is_locked = lineup_manager.is_lineup_locked(lineup_date)

        if is_locked:
            st.error(f"🔒 Lineups are locked for {lineup_date}")
            lock_time = lineup_manager.get_lineup_lock_time(lineup_date)
            st.caption(f"Locked at: {lock_time.strftime('%I:%M %p')}")
        else:
            time_until = lineup_manager.get_time_until_lock(lineup_date)
            if time_until:
                hours = int(time_until.total_seconds() // 3600)
                minutes = int((time_until.total_seconds() % 3600) // 60)
                st.success(f"✅ Lineup unlocked. Locks in {hours}h {minutes}m")

        # Show games scheduled for this date
        schedule = data_loader.load_game_schedule()
        games_today = schedule[schedule['game_date'] == lineup_date]

        if not games_today.empty:
            st.subheader(f"📅 Games on {lineup_date.strftime('%B %d, %Y')}")

            # Create a nice display of games
            for _, game in games_today.iterrows():
                game_time = game['game_time']
                col1, col2, col3 = st.columns([2, 1, 2])
                with col1:
                    st.write(f"**{game['away_team']}**")
                with col2:
                    st.write(f"@ {game_time}")
                with col3:
                    st.write(f"**{game['home_team']}**")

            st.caption(f"💡 Tip: Players on these teams will score points today")
            st.divider()
        else:
            st.info(f"ℹ️ No games scheduled for {lineup_date}")
            st.divider()

        # Get current lineup
        current_lineup = lineup_manager.get_manager_lineup(manager_id, lineup_date)

        if not current_lineup.empty and 'status' in current_lineup.columns and 'player_id' in current_lineup.columns:
            active_ids = current_lineup[current_lineup['status'] == 'active']['player_id'].tolist()
            lineup_status = "custom"
        else:
            # No lineup set for this date - will use sticky lineup logic
            active_ids = lineup_manager.get_active_players_for_scoring(manager_id, lineup_date)

            # Determine if this is from previous day or default
            all_lineups = data_loader.load_lineups()
            if all_lineups is not None:
                past = all_lineups[(all_lineups['manager_id'] == manager_id) &
                                   (all_lineups['game_date'] < lineup_date)]
                lineup_status = "previous" if not past.empty else "default"
            else:
                lineup_status = "default"

        # Get roster
        roster = draft_engine.get_manager_roster(manager_id)

        if not roster.empty:
            # Show lineup status
            if lineup_status == "custom":
                st.info(f"✅ Lineup set for {lineup_date}")
            elif lineup_status == "previous":
                st.warning(f"📋 Using previous lineup (not yet set for {lineup_date})")
            elif lineup_status == "default":
                st.warning(f"⚠️ Using default lineup (first {ACTIVE_PLAYERS_PER_DAY} players) - set your lineup below!")

            st.subheader(f"Select {ACTIVE_PLAYERS_PER_DAY} Active Players:")

            selected_players = []

            for _, player in roster.iterrows():
                is_active = player['player_id'] in active_ids

                # Add status indicator (check status_injury from merged DataFrame)
                injury_status = player.get('status_injury', player.get('status', 'active'))
                status_emoji = "🔴" if injury_status == 'injured' else ""
                player_label = f"{player['player_name']} ({player['team']}) {status_emoji}".strip()

                checkbox = st.checkbox(
                    player_label,
                    value=is_active,
                    key=f"player_{player['player_id']}",
                    disabled=is_locked or injury_status == 'injured'
                )

                if checkbox:
                    selected_players.append(player['player_id'])

            # Show count
            st.caption(f"Selected: {len(selected_players)} / {ACTIVE_PLAYERS_PER_DAY}")

            # Save button
            if not is_locked:
                if len(selected_players) != ACTIVE_PLAYERS_PER_DAY:
                    st.warning(f"⚠️ Must select exactly {ACTIVE_PLAYERS_PER_DAY} players (currently: {len(selected_players)})")
                    st.button("Save Lineup", disabled=True)
                else:
                    if st.button("Save Lineup", type="primary"):
                        success, message = lineup_manager.save_lineup(
                            manager_id, lineup_date, selected_players
                        )

                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("No roster found")

    with tab3:
        st.header("My Scores")

        # Load scores
        all_scores = data_loader.load_manager_daily_scores()

        if all_scores is not None and not all_scores.empty:
            manager_scores = all_scores[all_scores['manager_id'] == manager_id]

            if not manager_scores.empty:
                # Season total
                total = manager_scores['total_points'].sum()
                games = len(manager_scores)
                avg = total / games if games > 0 else 0

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Season Total", f"{total:.1f}")
                with col2:
                    st.metric("Games", games)
                with col3:
                    st.metric("Avg/Game", f"{avg:.1f}")

                # Recent scores
                st.subheader("Recent Games")
                recent = manager_scores.sort_values('game_date', ascending=False).head(10)

                display_recent = recent[['game_date', 'total_points', 'active_players_count']].copy()
                display_recent.columns = ['Date', 'Points', 'Active Players']

                st.dataframe(display_recent, hide_index=True, use_container_width=True)

                # Simple bar chart
                st.subheader("Points by Game")
                chart_data = manager_scores.sort_values('game_date')
                st.bar_chart(
                    chart_data,
                    x='game_date',
                    y='total_points',
                    use_container_width=True
                )
            else:
                st.info("No scores yet. Set lineups to start scoring!")
        else:
            st.info("No scores available yet.")

    with tab4:
        st.header("League Standings")

        standings = standings_updater.get_standings_with_details()

        if not standings.empty:
            # Highlight this manager
            def highlight_row(row):
                if row['manager_id'] == manager_id:
                    return ['background-color: lightblue'] * len(row)
                return [''] * len(row)

            display_standings = standings[[
                'rank', 'team_name', 'total_points',
                'games_with_scores', 'avg_points_per_day'
            ]].copy()

            display_standings.columns = [
                'Rank', 'Team', 'Total Points',
                'Games', 'Avg/Day'
            ]

            st.dataframe(
                display_standings,
                hide_index=True,
                use_container_width=True
            )

            # Show your rank
            my_rank = standings_updater.get_manager_rank(manager_id)
            if my_rank > 0:
                st.info(f"Your Current Rank: #{my_rank}")
        else:
            st.info("Standings not available yet.")

else:
    st.info("Please select your manager from the dropdown above.")
