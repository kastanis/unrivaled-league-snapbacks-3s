"""Season Recap - End-of-season summary, awards, and stats."""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import altair as alt

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from etl import data_loader

st.set_page_config(page_title="Season Recap", page_icon="🏆", layout="wide")

st.title("🏆 Season Recap")
st.caption("Unrivaled Fantasy League — Season 2")

# ── Load data ────────────────────────────────────────────────────────────────
managers    = data_loader.load_managers()
players     = data_loader.load_players()
standings   = data_loader.load_standings()
player_scores = data_loader.load_player_game_scores()
manager_daily = data_loader.load_manager_daily_scores()
rosters     = data_loader.load_rosters()
draft       = data_loader.load_draft_results()
lineups_raw = data_loader.load_lineups()

# Lookup dicts
mgr_name  = dict(zip(managers['manager_id'], managers['manager_name']))
mgr_team  = dict(zip(managers['manager_id'], managers['team_name']))
plr_name  = dict(zip(players['player_id'], players['player_name']))
plr_team  = dict(zip(players['player_id'], players['team']))

# ── Guard ────────────────────────────────────────────────────────────────────
if standings is None or standings.empty or standings['total_points'].sum() == 0:
    st.warning("⚠️ Standings data not yet available. Upload the latest backup in the Admin Portal.")
    st.stop()

# Enrich standings
std = standings.copy()
std['manager_name'] = std['manager_id'].map(mgr_name)
std['team_name']    = std['manager_id'].map(mgr_team)
std = std.sort_values('total_points', ascending=False).reset_index(drop=True)
std['rank'] = range(1, len(std) + 1)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🥇 Final Standings",
    "🏅 Season Awards",
    "📈 Manager Trends",
    "🃏 Player Leaderboard",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1  –  FINAL STANDINGS
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Final Standings")

    # Podium ─────────────────────────────────────────────────────────────────
    if len(std) >= 3:
        c1, c2, c3 = st.columns(3)   # gold | silver | bronze layout
        for col, idx, emoji, label in [
            (c1, 0, "🥇", "Champion"),
            (c2, 1, "🥈", "2nd Place"),
            (c3, 2, "🥉", "3rd Place"),
        ]:
            row = std.iloc[idx]
            with col:
                with st.container(border=True):
                    st.markdown(f"### {emoji} {label}")
                    st.markdown(f"**{row['manager_name']}**")
                    st.caption(row['team_name'])
                    st.metric("Total FP", f"{row['total_points']:.1f}")

    st.divider()

    # Full table ──────────────────────────────────────────────────────────────
    rank_icon = {1: "🥇", 2: "🥈", 3: "🥉", len(std): "💀"}
    disp = std[['rank','manager_name','team_name','total_points','games_with_scores','avg_points_per_day']].copy()
    disp['rank'] = disp['rank'].map(lambda r: rank_icon.get(r, str(r)))
    disp.columns = ['Rank','Manager','Team','Total FP','Games','Avg / Day']
    disp['Total FP']  = disp['Total FP'].map('{:.1f}'.format)
    disp['Avg / Day'] = disp['Avg / Day'].map('{:.1f}'.format)
    st.dataframe(disp, hide_index=True, use_container_width=True)

    # Horizontal bar chart ────────────────────────────────────────────────────
    st.subheader("Points Gap")
    bar_df = std[['manager_name','total_points']].sort_values('total_points')
    max_fp = std['total_points'].max()
    chart = alt.Chart(bar_df).mark_bar().encode(
        x=alt.X('total_points:Q', title='Total Fantasy Points'),
        y=alt.Y('manager_name:N', sort='-x', title=''),
        color=alt.condition(
            alt.datum.total_points == max_fp,
            alt.value('#FFD700'), alt.value('#4C78A8')
        ),
        tooltip=['manager_name', alt.Tooltip('total_points:Q', format='.1f', title='Total FP')],
    ).properties(height=280)
    st.altair_chart(chart, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2  –  SEASON AWARDS
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("Season Awards")

    def award(col, emoji, title, winner, detail):
        with col:
            with st.container(border=True):
                st.markdown(f"### {emoji}")
                st.markdown(f"**{title}**")
                st.markdown(f"### {winner}")
                st.caption(detail)

    col1, col2 = st.columns(2)

    # 🏆 Champion
    champ = std.iloc[0]
    award(col1, "🏆", "Champion", champ['manager_name'],
          f"{champ['team_name']} · {champ['total_points']:.1f} FP")

    # 💀 Last Place
    last = std.iloc[-1]
    award(col2, "💀", "Last Place", last['manager_name'],
          f"{last['team_name']} · {last['total_points']:.1f} FP")

    # ── Awards that need manager_daily ────────────────────────────────────────
    if manager_daily is not None and not manager_daily.empty:
        daily = manager_daily.groupby(['manager_id','game_date'])['total_points'].sum().reset_index()

        col3, col4 = st.columns(2)

        # 🔥 Best Single Day
        best_idx = daily['total_points'].idxmax()
        bd = daily.loc[best_idx]
        award(col3, "🔥", "Best Single Day",
              mgr_name.get(bd['manager_id'], '?'),
              f"{bd['total_points']:.1f} FP on {bd['game_date']}")

        # 📈 Most Consistent (lowest std dev, min 10 scoring days)
        stats = daily.groupby('manager_id')['total_points'].agg(['std','mean','count']).reset_index()
        stats = stats[stats['count'] >= 10]
        if not stats.empty:
            best_con = stats.loc[stats['std'].idxmin()]
            award(col4, "📈", "Most Consistent",
                  mgr_name.get(best_con['manager_id'], '?'),
                  f"Avg {best_con['mean']:.1f} FP/day · σ = {best_con['std']:.1f}")

    # ── Awards that need draft + player_scores ────────────────────────────────
    if draft is not None and not draft.empty and player_scores is not None and not player_scores.empty:
        ps_played = player_scores[player_scores['status'] == 'played']
        plr_totals = ps_played.groupby('player_id')['fantasy_points'].sum().reset_index()
        plr_totals.columns = ['player_id', 'total_fp']

        draft_fp = draft.merge(plr_totals, on='player_id', how='left')
        draft_fp['total_fp']     = draft_fp['total_fp'].fillna(0)
        draft_fp['player_name']  = draft_fp['player_id'].map(plr_name)
        draft_fp['manager_name'] = draft_fp['manager_id'].map(mgr_name)

        col5, col6 = st.columns(2)

        # 🃏 Best Draft Steal – highest FP weighted by pick position (later pick = more impressive)
        max_pick = draft_fp['pick_number'].max()
        draft_fp['value_score'] = draft_fp['total_fp'] * (draft_fp['pick_number'] / max_pick)
        steal = draft_fp.loc[draft_fp['value_score'].idxmax()]
        award(col5, "🃏", "Best Draft Steal",
              steal['player_name'],
              f"Pick #{int(steal['pick_number'])} · {steal['total_fp']:.1f} FP · {steal['manager_name']}")

        # 💸 Biggest Bust – lowest FP among round 1 picks
        r1 = draft_fp[draft_fp['round'] == 1]
        if not r1.empty:
            bust = r1.loc[r1['total_fp'].idxmin()]
            award(col6, "💸", "Biggest Bust",
                  bust['player_name'],
                  f"Pick #{int(bust['pick_number'])} (Rd 1) · {bust['total_fp']:.1f} FP · {bust['manager_name']}")

    # ── Awards that need lineups + player_scores ──────────────────────────────
    if (lineups_raw is not None and not lineups_raw.empty
            and player_scores is not None and not player_scores.empty):

        ps = player_scores.copy()
        lu = lineups_raw.merge(
            ps[['player_id','game_date','fantasy_points','status']],
            on=['player_id','game_date'], how='left'
        )
        lu['fantasy_points'] = lu['fantasy_points'].fillna(0)

        active_lu = lu[lu['status_x'] == 'active']
        bench_lu  = lu[(lu['status_x'] == 'bench') & (lu['status_y'] == 'played')]

        bench_by_mgr  = bench_lu.groupby('manager_id')['fantasy_points'].sum().reset_index()
        bench_by_mgr.columns = ['manager_id', 'bench_fp']
        active_by_mgr = active_lu.groupby('manager_id')['fantasy_points'].sum().reset_index()
        active_by_mgr.columns = ['manager_id', 'active_fp']

        col7, col8 = st.columns(2)

        # 🪑 Biggest Bench Sitter
        if not bench_by_mgr.empty:
            blunder = bench_by_mgr.loc[bench_by_mgr['bench_fp'].idxmax()]
            award(col7, "🪑", "Biggest Bench Sitter",
                  mgr_name.get(blunder['manager_id'], '?'),
                  f"{blunder['bench_fp']:.1f} FP left on bench all season")

        # 🎯 Best Lineup Manager
        if not active_by_mgr.empty and not bench_by_mgr.empty:
            eff = active_by_mgr.merge(bench_by_mgr, on='manager_id', how='left')
            eff['bench_fp'] = eff['bench_fp'].fillna(0)
            eff['efficiency'] = eff['active_fp'] / (eff['active_fp'] + eff['bench_fp']).replace(0, 1)
            best_eff = eff.loc[eff['efficiency'].idxmax()]
            award(col8, "🎯", "Best Lineup Manager",
                  mgr_name.get(best_eff['manager_id'], '?'),
                  f"{best_eff['efficiency']*100:.1f}% of available FP activated")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3  –  MANAGER TRENDS
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("Manager Performance Over Time")

    if manager_daily is None or manager_daily.empty:
        st.info("Daily manager scores not available. Upload the latest backup in Admin Portal.")
    else:
        daily = manager_daily.groupby(['manager_id','game_date'])['total_points'].sum().reset_index()
        daily['manager_name'] = daily['manager_id'].map(mgr_name)
        daily['game_date'] = pd.to_datetime(daily['game_date'])
        daily = daily.sort_values(['manager_id','game_date'])
        daily['cumulative_fp'] = daily.groupby('manager_id')['total_points'].cumsum()

        # Cumulative line chart
        st.subheader("Season Progression — Cumulative FP")
        line = alt.Chart(daily).mark_line().encode(
            x=alt.X('game_date:T', title='Date'),
            y=alt.Y('cumulative_fp:Q', title='Cumulative FP'),
            color=alt.Color('manager_name:N', title='Manager'),
            tooltip=['manager_name',
                     alt.Tooltip('game_date:T', format='%b %d'),
                     alt.Tooltip('cumulative_fp:Q', format='.1f', title='Cumul. FP')],
        ).properties(height=380)
        st.altair_chart(line, use_container_width=True)

        st.divider()

        # Carry Me table
        st.subheader("🚗 Carry Me — Dependence on Top Player")
        if rosters is not None and not rosters.empty and player_scores is not None:
            ps_played = player_scores[player_scores['status'] == 'played']
            plr_totals = ps_played.groupby('player_id')['fantasy_points'].sum().reset_index()
            plr_totals.columns = ['player_id', 'total_fp']

            ros = rosters.merge(plr_totals, on='player_id', how='left')
            ros['total_fp']     = ros['total_fp'].fillna(0)
            ros['player_name']  = ros['player_id'].map(plr_name)
            ros['manager_name'] = ros['manager_id'].map(mgr_name)

            mgr_sums = ros.groupby('manager_id')['total_fp'].sum().rename('roster_total')
            ros = ros.join(mgr_sums, on='manager_id')
            ros['pct'] = ros['total_fp'] / ros['roster_total'].replace(0, 1) * 100

            top = (ros.sort_values('total_fp', ascending=False)
                      .groupby('manager_id').first().reset_index()
                      .sort_values('pct', ascending=False))

            carry_disp = top[['manager_name','player_name','total_fp','pct']].copy()
            carry_disp.columns = ['Manager', 'Top Player', 'Player FP', '% of Team']
            carry_disp['Player FP'] = carry_disp['Player FP'].map('{:.1f}'.format)
            carry_disp['% of Team'] = carry_disp['% of Team'].map('{:.1f}%'.format)
            st.dataframe(carry_disp, hide_index=True, use_container_width=True)

        st.divider()

        # Roster contribution — normalized stacked bar
        st.subheader("Roster Contribution — Each Player's Share")
        if rosters is not None and not rosters.empty and player_scores is not None:
            ps_played = player_scores[player_scores['status'] == 'played']
            plr_totals = ps_played.groupby('player_id')['fantasy_points'].sum().reset_index()
            plr_totals.columns = ['player_id', 'total_fp']

            ros2 = rosters.merge(plr_totals, on='player_id', how='left')
            ros2['total_fp']     = ros2['total_fp'].fillna(0)
            ros2['manager_name'] = ros2['manager_id'].map(mgr_name)
            ros2['player_name']  = ros2['player_id'].map(plr_name)
            ros2 = ros2[ros2['total_fp'] > 0]

            # Sort managers by their total
            mgr_order = (ros2.groupby('manager_name')['total_fp']
                             .sum().sort_values(ascending=False).index.tolist())

            stacked = alt.Chart(ros2).mark_bar().encode(
                x=alt.X('manager_name:N', title='Manager', sort=mgr_order),
                y=alt.Y('total_fp:Q', title='Fantasy Points', stack='normalize',
                        axis=alt.Axis(format='%')),
                color=alt.Color('player_name:N', legend=None),
                tooltip=['manager_name', 'player_name',
                         alt.Tooltip('total_fp:Q', format='.1f', title='FP')],
            ).properties(height=350)
            st.altair_chart(stacked, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4  –  PLAYER LEADERBOARD
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("Player Season Leaderboard")

    if player_scores is None or player_scores.empty:
        st.info("Player scores data not available.")
    else:
        ps_played = player_scores[player_scores['status'] == 'played'].copy()
        ps_played['player_name'] = ps_played['player_id'].map(plr_name)
        ps_played['team']        = ps_played['player_id'].map(plr_team)

        summary = (ps_played.groupby(['player_id','player_name','team'])
                             .agg(total_fp=('fantasy_points','sum'),
                                  gp=('fantasy_points','count'),
                                  avg_fp=('fantasy_points','mean'),
                                  best_game=('fantasy_points','max'))
                             .reset_index()
                             .sort_values('total_fp', ascending=False)
                             .reset_index(drop=True))
        summary['rank'] = range(1, len(summary) + 1)

        # Who drafted each player
        if rosters is not None and not rosters.empty:
            roster_mgr = rosters.merge(managers[['manager_id','manager_name']], on='manager_id')
            summary = summary.merge(roster_mgr[['player_id','manager_name']], on='player_id', how='left')
            summary['manager_name'] = summary['manager_name'].fillna('—')
        else:
            summary['manager_name'] = '—'

        disp = summary[['rank','player_name','team','manager_name','gp','total_fp','avg_fp','best_game']].copy()
        disp.columns = ['Rank','Player','Unrivaled Team','Drafted By','GP','Total FP','Avg FP','Best Game']
        for col in ['Total FP','Avg FP','Best Game']:
            disp[col] = disp[col].map('{:.1f}'.format)

        st.dataframe(disp, hide_index=True, use_container_width=True)

        st.divider()
        st.subheader("Top 15 Players by Total FP")
        top15 = summary.head(15)

        TEAM_COLORS = {
            'Breeze':      '#4c3971',
            'Hive':        '#ffc728',
            'Vinyl':       '#820234',
            'Rose':        '#dda493',
            'Lunar Owls':  '#40347d',
            'Laces':       '#74b29f',
            'Phantom':     '#2a2a2a',
            'Mist':        '#a3d3e7',
        }
        domain = list(TEAM_COLORS.keys())
        range_ = list(TEAM_COLORS.values())

        bar = alt.Chart(top15).mark_bar().encode(
            x=alt.X('total_fp:Q', title='Total Fantasy Points'),
            y=alt.Y('player_name:N', sort='-x', title=''),
            color=alt.Color('team:N', title='Team',
                            scale=alt.Scale(domain=domain, range=range_)),
            tooltip=['player_name','team',
                     alt.Tooltip('total_fp:Q', format='.1f', title='Total FP'),
                     alt.Tooltip('avg_fp:Q', format='.1f', title='Avg FP'),
                     'gp'],
        ).properties(height=420)
        st.altair_chart(bar, use_container_width=True)
