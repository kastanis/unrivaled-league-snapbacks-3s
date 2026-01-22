"""Manager Portal - View roster, set lineups, check scores."""

import streamlit as st
import sys
from pathlib import Path
from datetime import date, timedelta
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl import data_loader, draft_engine, lineup_manager, standings_updater, score_calculator, player_stats
from etl.config import SEASON_START, SEASON_END, ACTIVE_PLAYERS_PER_DAY

st.set_page_config(page_title="Manager Portal", page_icon="👤")

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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["My Roster", "Set Lineup", "My Scores", "Standings", "Player Stats", "Transaction Log"])

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
            st.caption(f"Locked at: {lock_time.strftime('%I:%M %p')} ET")
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
                    st.write(f"@ {game_time} ET")
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
                    key=f"player_{player['player_id']}_{lineup_date}",
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
                games = len(manager_scores)  # Each row is now one game
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

                # Sort by date then game_id for proper order
                if 'game_id' in manager_scores.columns:
                    recent = manager_scores.sort_values(['game_date', 'game_id'], ascending=False).head(10).copy()

                    # Convert game_id to int
                    recent['game_id'] = recent['game_id'].astype(int)

                    # Get game schedule to show matchups
                    schedule = data_loader.load_game_schedule()

                    # Create game number within each date for matching
                    # This handles case where uploaded game_id resets per day (1,2,3,4)
                    # but schedule has sequential game_ids (1-56)
                    recent['game_num'] = recent.groupby('game_date')['game_id'].rank(method='dense').astype(int)
                    schedule_copy = schedule.copy()
                    schedule_copy['game_num'] = schedule_copy.groupby('game_date')['game_id'].rank(method='dense').astype(int)

                    recent = recent.merge(
                        schedule_copy[['game_date', 'game_num', 'home_team', 'away_team']],
                        on=['game_date', 'game_num'],
                        how='left'
                    )

                    # Create matchup column
                    recent['matchup'] = recent['home_team'] + ' v ' + recent['away_team']

                    # Calculate benched players who actually played
                    # For each game, count roster players who played but were benched
                    lineups = data_loader.load_lineups()
                    player_scores = data_loader.load_player_game_scores()
                    roster = draft_engine.get_manager_roster(manager_id)
                    roster_player_ids = roster['player_id'].tolist() if not roster.empty else []

                    benched_counts = []
                    for _, row in recent.iterrows():
                        game_date = row['game_date']
                        game_id = row['game_id']

                        # Get lineup for this manager/date
                        my_lineup = lineups[
                            (lineups['manager_id'] == manager_id) &
                            (lineups['game_date'] == game_date)
                        ]

                        # Get benched players from lineup
                        benched_player_ids = my_lineup[my_lineup['status'] == 'bench']['player_id'].tolist()

                        # Get players who actually played in this game
                        game_player_scores = player_scores[player_scores['game_id'] == game_id]
                        players_who_played = game_player_scores['player_id'].tolist()

                        # Count benched players who are on roster AND played in this game
                        benched_who_played = [
                            p for p in benched_player_ids
                            if p in players_who_played and p in roster_player_ids
                        ]
                        benched_counts.append(len(benched_who_played))

                    recent['benched_players'] = benched_counts

                    display_recent = recent[['game_date', 'matchup', 'total_points', 'active_players_count']].copy()
                    display_recent.columns = ['Date', 'Matchup', 'Points', 'Active Players']
                else:
                    recent = manager_scores.sort_values('game_date', ascending=False).head(10)
                    display_recent = recent[['game_date', 'total_points', 'active_players_count']].copy()
                    display_recent.columns = ['Date', 'Points', 'Active Players']

                st.dataframe(display_recent, hide_index=True, use_container_width=True)

                # Bar chart - one bar per game
                st.subheader("Points by Game")

                # Create a label for each game
                chart_data = manager_scores.sort_values(['game_date', 'game_id'] if 'game_id' in manager_scores.columns else 'game_date').copy()
                if 'game_id' in chart_data.columns:
                    # Convert game_id to int
                    chart_data['game_id'] = chart_data['game_id'].astype(int)

                    # Get game schedule to show matchups
                    schedule = data_loader.load_game_schedule()

                    # Create game number within each date for matching
                    chart_data['game_num'] = chart_data.groupby('game_date')['game_id'].rank(method='dense').astype(int)
                    schedule_copy = schedule.copy()
                    schedule_copy['game_num'] = schedule_copy.groupby('game_date')['game_id'].rank(method='dense').astype(int)

                    chart_data = chart_data.merge(
                        schedule_copy[['game_date', 'game_num', 'home_team', 'away_team']],
                        on=['game_date', 'game_num'],
                        how='left'
                    )

                    # Sort by game_date and game_id to ensure chronological order
                    chart_data = chart_data.sort_values(['game_date', 'game_id']).reset_index(drop=True)

                    # Create user-friendly labels: "1/5 Hive v Mist"
                    chart_data['game_label'] = (
                        pd.to_datetime(chart_data['game_date']).dt.strftime('%-m/%-d') + ' ' +
                        chart_data['home_team'] + ' v ' + chart_data['away_team']
                    )

                    # Calculate bench points using game_id mapping
                    lineups_all = data_loader.load_lineups()
                    player_game_scores = data_loader.load_player_game_scores()
                    players = data_loader.load_players()
                    game_id_mapping = data_loader.load_game_id_mapping()

                    if lineups_all is not None and player_game_scores is not None and players is not None:
                        # Get benched players for this manager
                        manager_lineups = lineups_all[lineups_all['manager_id'] == manager_id]
                        benched = manager_lineups[manager_lineups['status'] == 'bench']

                        # Calculate bench points per game
                        bench_points_by_game = []
                        for _, game_row in chart_data.iterrows():
                            player_game_id = game_row['game_id']  # This is from manager_scores (1, 2 per date)
                            game_date = game_row['game_date']
                            home_team = game_row['home_team']
                            away_team = game_row['away_team']

                            # Get benched players for this date
                            benched_date = benched[benched['game_date'] == game_date]['player_id'].tolist()

                            # Filter benched players whose team is playing in this game
                            benched_in_game = []
                            for player_id in benched_date:
                                player_info = players[players['player_id'] == player_id]
                                if not player_info.empty:
                                    player_team = player_info['team'].iloc[0]
                                    if player_team == home_team or player_team == away_team:
                                        benched_in_game.append(player_id)

                            # Get scores for benched players who played in this game
                            # Match using game_date and player_game_id from player_game_scores
                            benched_scores = player_game_scores[
                                (player_game_scores['game_date'] == game_date) &
                                (player_game_scores['game_id'] == player_game_id) &
                                (player_game_scores['player_id'].isin(benched_in_game)) &
                                (player_game_scores['status'] == 'played')
                            ]

                            bench_total = benched_scores['fantasy_points'].sum() if not benched_scores.empty else 0.0
                            bench_points_by_game.append({
                                'game_id': player_game_id,
                                'game_date': game_date,
                                'bench_points': bench_total
                            })

                        bench_df = pd.DataFrame(bench_points_by_game)

                        # Merge bench points with chart data
                        chart_data = chart_data.merge(
                            bench_df,
                            on=['game_id', 'game_date'],
                            how='left'
                        )
                        chart_data['bench_points'] = chart_data['bench_points'].fillna(0)
                    else:
                        chart_data['bench_points'] = 0

                    # Rename total_points to active_points for clarity
                    chart_data['active_points'] = chart_data['total_points']

                    # Create stacked data for visualization
                    chart_long = pd.DataFrame([])
                    for _, row in chart_data.iterrows():
                        chart_long = pd.concat([
                            chart_long,
                            pd.DataFrame([{
                                'game_label': row['game_label'],
                                'point_type': 'Bench Points',
                                'points': row['bench_points']
                            }]),
                            pd.DataFrame([{
                                'game_label': row['game_label'],
                                'point_type': 'Active Points',
                                'points': row['active_points']
                            }])
                        ], ignore_index=True)

                    # Convert game_label to ordered categorical to preserve sort order
                    unique_labels = chart_data['game_label'].unique().tolist()
                    chart_long['game_label'] = pd.Categorical(
                        chart_long['game_label'],
                        categories=unique_labels,
                        ordered=True
                    )

                    # Create Altair stacked bar chart
                    chart = alt.Chart(chart_long).mark_bar().encode(
                        x=alt.X('game_label:N', title='Game', sort=None),
                        y=alt.Y('points:Q', title='Fantasy Points'),
                        color=alt.Color('point_type:N',
                                      scale=alt.Scale(
                                          domain=['Bench Points', 'Active Points'],
                                          range=['#FFB366', '#1f77b4']  # Orange for bench (bottom), blue for active (top)
                                      ),
                                      legend=alt.Legend(title='Point Type')),
                        order=alt.Order('point_type:N', sort='ascending')  # Bench on bottom, active on top
                    ).properties(
                        height=400
                    )

                    st.altair_chart(chart, use_container_width=True)
                else:
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
                'Games', 'Avg/Game'
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

    with tab5:
        st.header("Player Stats Dashboard")

        # Get all player stats
        all_stats = player_stats.get_all_player_stats()

        if not all_stats.empty:
            # Show my roster players first
            roster = draft_engine.get_manager_roster(manager_id)
            my_player_ids = roster['player_id'].tolist() if not roster.empty else []

            # Filter to my players
            my_players = all_stats[all_stats['player_id'].isin(my_player_ids)]

            if not my_players.empty:
                st.subheader("Your Roster Performance")

                # Add trend emoji
                my_players['trend_emoji'] = my_players['trend'].map({
                    'hot': '🔥',
                    'cold': '🥶',
                    'neutral': '-'
                })

                display_my = my_players[[
                    'player_name', 'team', 'games_played',
                    'season_avg', 'last_game_points', 'last_5_avg', 'total_points', 'trend_emoji'
                ]].copy()

                display_my.columns = [
                    'Player', 'Team', 'GP',
                    'Season Avg', 'Last Game', 'Last 5 Avg', 'Total Pts', 'Trend'
                ]

                st.dataframe(
                    display_my,
                    hide_index=True,
                    use_container_width=True
                )

            st.divider()
            st.subheader("All Players")

            # Add trend emoji
            all_stats['trend_emoji'] = all_stats['trend'].map({
                'hot': '🔥',
                'cold': '🥶',
                'neutral': '-'
            })

            display_all = all_stats[[
                'player_name', 'team', 'games_played',
                'season_avg', 'last_game_points', 'last_5_avg', 'total_points', 'trend_emoji'
            ]].copy()

            display_all.columns = [
                'Player', 'Team', 'GP',
                'Season Avg', 'Last Game', 'Last 5 Avg', 'Total Pts', 'Trend'
            ]

            st.dataframe(
                display_all,
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No player stats available yet. Stats will appear after game data is uploaded.")

    with tab6:
        st.header("Transaction Log")

        # Load transaction log
        transactions = data_loader.load_transaction_log()

        if transactions is not None and not transactions.empty:
            # Filter to this manager's transactions
            my_transactions = transactions[transactions['manager_id'] == manager_id]

            if not my_transactions.empty:
                # Sort by timestamp descending
                my_transactions = my_transactions.sort_values('timestamp', ascending=False)

                st.subheader("Your Recent Lineup Changes")

                # Display transaction log
                display_transactions = my_transactions[[
                    'timestamp', 'game_date', 'active_players'
                ]].copy()

                display_transactions.columns = ['Timestamp', 'Game Date', 'Active Players']

                # Format timestamp
                display_transactions['Timestamp'] = pd.to_datetime(display_transactions['Timestamp']).dt.strftime('%Y-%m-%d %H:%M')

                st.dataframe(
                    display_transactions,
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No lineup changes recorded yet.")

            # Show all transactions (optional)
            if st.checkbox("Show all managers' transactions"):
                st.subheader("All Lineup Changes")

                # Merge with manager names
                all_trans_display = transactions.merge(
                    managers[['manager_id', 'team_name']],
                    on='manager_id',
                    how='left'
                )

                all_trans_display = all_trans_display.sort_values('timestamp', ascending=False)

                display_all_trans = all_trans_display[[
                    'timestamp', 'team_name', 'game_date', 'active_players'
                ]].copy()

                display_all_trans.columns = ['Timestamp', 'Team', 'Game Date', 'Active Players']
                display_all_trans['Timestamp'] = pd.to_datetime(display_all_trans['Timestamp']).dt.strftime('%Y-%m-%d %H:%M')

                st.dataframe(
                    display_all_trans,
                    hide_index=True,
                    use_container_width=True
                )
        else:
            st.info("No transactions recorded yet.")

else:
    st.info("Please select your manager from the dropdown above.")
