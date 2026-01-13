"""Unrivaled Fantasy Basketball League - Main App."""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl import data_loader, standings_updater, weekly_recap
from etl.config import NUM_MANAGERS, NUM_PLAYERS

# Page config
st.set_page_config(
    page_title="Unrivaled Fantasy League",
    page_icon="🏀",
    initial_sidebar_state="expanded"
)

# Title
st.title("🏀 Unrivaled Fantasy Basketball League")
st.markdown("### Season 2 | Jan 5 - Feb 27, 2026")

# Sidebar
st.sidebar.title("Navigation")
st.sidebar.markdown("""
- **Manager Portal** - Set lineups, view scores
- **Admin Portal** - Run draft, upload stats
- **Tournament** - 1-on-1 tournament picks
""")

# Main page content
st.header("Welcome to the League!")

# Display current standings
st.subheader("Current Standings")

try:
    standings = standings_updater.get_standings_with_details()

    if not standings.empty:
        # Format standings table
        display_standings = standings[[
            'rank', 'team_name', 'total_points',
            'games_with_scores', 'avg_points_per_day'
        ]].copy()

        display_standings.columns = [
            'Rank', 'Team', 'Total Points',
            'Games Played', 'Avg/Game'
        ]

        st.dataframe(
            display_standings,
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No scores yet. Complete the draft and set lineups to get started!")
except Exception as e:
    st.warning("Standings not available yet. Complete the draft to begin!")

# League info
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Teams", NUM_MANAGERS)

with col2:
    st.metric("Players", NUM_PLAYERS)

with col3:
    # Count total games that have uploaded stats
    try:
        daily_scores = data_loader.load_manager_daily_scores()
        if daily_scores is not None and not daily_scores.empty:
            # Count unique (game_date, game_id) combinations
            games_count = len(daily_scores[['game_date', 'game_id']].drop_duplicates())
        else:
            games_count = 0
    except Exception:
        games_count = 0

    st.metric("Games Played", games_count)

# Weekly Recap
st.divider()
st.subheader("Recent Game Day Highlights")

try:
    recaps = weekly_recap.get_recent_recaps(num_days=3)

    if recaps:
        for idx, recap in enumerate(recaps):
            game_date = recap['game_date']

            # Keep the latest (first) date expanded
            with st.expander(f"📅 {game_date.strftime('%B %d, %Y')}", expanded=(idx == 0)):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**🏆 Top Scorer**")
                    if recap['top_scorer']:
                        st.write(f"{recap['top_scorer']['player_name']}")
                        st.caption(f"{recap['top_scorer']['team']}")
                        st.metric("Points", f"{recap['top_scorer']['fantasy_points']:.1f}")

                with col2:
                    st.markdown("**⭐ Manager of the Day**")
                    if recap['manager_of_day']:
                        st.write(f"{recap['manager_of_day']['manager_name']}")
                        st.caption(f"{recap['manager_of_day']['team_name']}")
                        st.metric("Points", f"{recap['manager_of_day']['total_points']:.1f}")

                with col3:
                    st.markdown("**😅 Biggest Bench Mistake**")
                    if recap['biggest_bench_mistake']:
                        st.write(f"{recap['biggest_bench_mistake']['manager_name']}")
                        st.caption(f"Benched: {recap['biggest_bench_mistake']['player_name']}")
                        st.metric("Missed Points", f"{recap['biggest_bench_mistake']['fantasy_points']:.1f}")
                    else:
                        st.info("No bench mistakes!")
    else:
        st.info("Game highlights will appear here after games are played!")
except Exception as e:
    st.info("Game highlights will appear after the first games are played.")

# How it works
st.divider()
st.subheader("How It Works")

st.markdown("""
1. **Draft** - 8 managers snake draft 6 players each (48 total picks)
2. **Set Lineups** - Each day, set 3 active players (lineup locks at first game)
3. **Score Points** - Active players earn fantasy points based on game stats
4. **Season-Long Competition** - Total points at end of season determines the winner!

**Scoring System:**
- Points Scored = 1.0 points
- Rebound = 1.2 points
- Assist = 1.0 points
- Steal = 2.0 points
- Block = 2.0 points
- Turnover = -1.0 points
- Personal Foul = -0.5 points
- Game Winner = 1.5 points
- Dunk = 0.5 points
""")

# Quick start guide
st.divider()
st.subheader("Quick Start")

st.markdown("""
**For Managers:**
1. Go to **Manager Portal** (see pages in sidebar)
2. Select your name from dropdown
3. View your roster, set daily lineups, check scores

**For Admin:**
1. Go to **Admin Portal**
2. Run the draft (or upload draft results)
3. Upload game stats after each game day
4. Standings update automatically
""")

# Footer
st.divider()
st.caption("Unrivaled Fantasy Basketball League | Season 2 (2026)")
