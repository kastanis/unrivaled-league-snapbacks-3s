# Bugs Report

## Bug #1: Games Played Count Mismatch on Main Page

### Description
The "Games Played" metric on the main page was counting games with uploaded scores instead of total games that have occurred according to the schedule.

### Status
✅ **FIXED** in [app/streamlit_app.py:74-89](app/streamlit_app.py#L74-L89)

### Fix Applied
Changed from counting unique `game_id` values in `manager_daily_scores` to counting games from the schedule where `game_date <= today`:

```python
# Count games from schedule that have been played (date has passed or is today)
try:
    from datetime import date
    schedule = data_loader.load_game_schedule()
    if schedule is not None and not schedule.empty:
        today = date.today()
        # Count games where date <= today
        games_played = schedule[schedule['game_date'] <= today]
        games_count = len(games_played)
    else:
        games_count = 0
except Exception:
    games_count = 0
```

**Result**: If 6 games have occurred (based on schedule dates), metric now shows 6 instead of 4.

---

## Enhancement #1: Recent Game Day Highlights UI Improvements

### Description
Requested improvements to the game highlights section on the main page:
1. Change title from "Recent Game Highlights" to "Recent Game Day Highlights"
2. Keep the latest date always expanded (unfurled) by default

### Status
✅ **COMPLETED** in [app/streamlit_app.py:93,99-103](app/streamlit_app.py#L93)

### Changes Applied

**Title Change** (line 93):
```python
st.subheader("Recent Game Day Highlights")  # Was: "Recent Game Highlights"
```

**Expansion Logic** (lines 99-103):
```python
# Before: expanded=len(recaps) == 1 (only when exactly 1 recap exists)
# After: expanded=(idx == 0) (always expand the first/latest date)
for idx, recap in enumerate(recaps):
    game_date = recap['game_date']
    with st.expander(f"📅 {game_date.strftime('%B %d, %Y')}", expanded=(idx == 0)):
```

**Result**: The most recent game day is now always shown expanded, making it easier to see the latest results immediately.

---

## Bug #2: Locked Lineup Not Displaying Correctly After Page Refresh

### Description
When a lineup is locked and saved for a specific date, the Manager Portal does not display the saved lineup when the page refreshes or when navigating back to that date from another date. Instead, it shows a default lineup (first 3 players) even though the correct lineup is saved in the database.

### Steps to Reproduce
1. Set a lineup for a specific date (e.g., 2026-01-05)
2. Press "Save Lineup" button
3. Lineup is successfully saved (confirmed in `data/processed/lineups.csv`)
4. Date becomes locked
5. Refresh the page OR navigate to a different date and come back
6. **Bug**: The lineup displayed shows default players instead of the saved lineup

### Expected Behavior
The saved lineup should be displayed with the correct active/benched players that were selected and locked.

### Actual Behavior
The UI shows a default lineup (first 3 players alphabetically by player_id) instead of the saved lineup.

### Observed Evidence
- The lineup IS correctly saved in `lineups.csv` with proper `status` (active/bench) values
- Transaction logs correctly capture the lineup changes
- Manager scores are calculated correctly using the saved active players
- The issue is only with the **display** of the lineup in the Manager Portal

### Root Cause Analysis

The bug is in the lineup loading logic in [app/pages/1_Manager_Portal.py:124-140](app/pages/1_Manager_Portal.py#L124-L140):

```python
# Get current lineup
current_lineup = lineup_manager.get_manager_lineup(manager_id, lineup_date)

if not current_lineup.empty and 'status' in current_lineup.columns and 'player_id' in current_lineup.columns:
    active_ids = current_lineup[current_lineup['status'] == 'active']['player_id'].tolist()
    lineup_status = "custom"
else:
    # No lineup set for this date - will use sticky lineup logic
    active_ids = lineup_manager.get_active_players_for_scoring(manager_id, lineup_date)
    # ... falls back to previous or default lineup
```

**The condition on line 126 is failing silently**, causing the code to fall into the `else` block and use fallback logic instead of the saved lineup.

### Possible Causes

1. **Player Merge Issue**: The `get_manager_lineup()` function ([etl/lineup_manager.py:123-152](etl/lineup_manager.py#L123-L152)) merges lineup data with player data:
   ```python
   manager_lineup = manager_lineup.merge(
       players,
       on='player_id',
       how='left',
       suffixes=('', '_injury')
   )
   ```
   If a player in the lineup doesn't exist in `players.csv` at the time of loading (e.g., player 50 wasn't in players.csv when code deployed), the merge could produce unexpected results.

2. **Streamlit Caching**: The `data_loader.load_players()` function is cached with `@st.cache_data(ttl=3600)`. If players.csv was updated but the cache hasn't expired, the merge might fail for newly added players.

3. **DataFrame Structure After Merge**: The merge operation might be changing the DataFrame structure in a way that makes the condition fail (e.g., renaming columns, changing dtypes).

### Proposed Fix

**Option 1: Add Debug Logging**
Add debug output to understand why the condition fails:
```python
# DEBUG: Log lineup loading
if not current_lineup.empty:
    st.write(f"DEBUG - Columns: {list(current_lineup.columns)}")
    st.write(f"DEBUG - Has status: {'status' in current_lineup.columns}")
    st.write(f"DEBUG - Has player_id: {'player_id' in current_lineup.columns}")
```

**Option 2: Load Lineup More Defensively**
Instead of relying on the merged DataFrame, load the raw lineup data directly:
```python
# Get current lineup (raw from CSV, no merge)
raw_lineups = data_loader.load_lineups(lineup_date)
if raw_lineups is not None and not raw_lineups.empty:
    manager_lineup = raw_lineups[raw_lineups['manager_id'] == manager_id]
    if not manager_lineup.empty:
        active_ids = manager_lineup[manager_lineup['status'] == 'active']['player_id'].tolist()
        lineup_status = "custom"
    else:
        # Use fallback logic
        active_ids = lineup_manager.get_active_players_for_scoring(manager_id, lineup_date)
else:
    # Use fallback logic
    active_ids = lineup_manager.get_active_players_for_scoring(manager_id, lineup_date)
```

**Option 3: Fix the Merge**
Ensure the merge preserves the critical columns by being more explicit:
```python
def get_manager_lineup(manager_id: int, game_date: date) -> pd.DataFrame:
    lineups = data_loader.load_lineups(game_date)

    if lineups is None or lineups.empty:
        return pd.DataFrame()

    manager_lineup = lineups[lineups['manager_id'] == manager_id].copy()

    if not manager_lineup.empty:
        players = data_loader.load_players()
        # Preserve essential columns before merge
        essential_cols = ['lineup_id', 'manager_id', 'game_date', 'player_id', 'status', 'locked_at']
        manager_lineup = manager_lineup.merge(
            players,
            on='player_id',
            how='left',
            suffixes=('', '_injury')
        )
        # Ensure essential columns are still present
        for col in essential_cols:
            if col not in manager_lineup.columns:
                raise ValueError(f"Critical column '{col}' lost during merge")

    return manager_lineup
```

### Priority
**Medium** - The lineup is being saved and used for scoring correctly, but the user experience is poor when they can't see their locked lineup.

### Workaround
None currently. Users must trust that their saved lineup is locked even though the UI shows default players.

---

## Notes
- Transaction logs are working correctly
- Scoring calculations use the correct saved lineups
- This is purely a display issue in the Manager Portal
- Related to player 50 (Tiffany Hayes) replacement - if player didn't exist in cache when lineup was loaded, merge could fail
