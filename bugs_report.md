# Bugs Report

## Bug #1: Games Played Count on Main Page

### Description
The "Games Played" metric on the main page should show the count of games that have uploaded stats.

### Status
✅ **FIXED** in [app/streamlit_app.py:74-86](app/streamlit_app.py#L74-L86)

### Fix Applied
Counts unique `game_id` values from `manager_daily_scores` (games with uploaded stats):

```python
# Count total games that have uploaded stats
try:
    daily_scores = data_loader.load_manager_daily_scores()
    if daily_scores is not None and not daily_scores.empty:
        # Count unique game_ids in the scores data
        games_count = daily_scores['game_id'].nunique()
    else:
        games_count = 0
except Exception:
    games_count = 0
```

**Result**: Shows the actual number of games with uploaded stats. Since game_id is sequential and unique across the entire season (games 1-4 on Jan 5, games 5-6 on Jan 9, etc.), counting unique game_ids gives the total games played.

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
When a lineup is locked and saved for a specific date, the Manager Portal does not display the saved lineup when the page refreshes or when navigating back to that date from another date. Instead, it shows incorrect checkboxes even though the correct lineup is saved in the database.

### Status
✅ **FIXED** in [app/pages/1_Manager_Portal.py:169](app/pages/1_Manager_Portal.py#L169)

### Steps to Reproduce (Original Bug)
1. Set a lineup for a specific date (e.g., 2026-01-09)
2. Press "Save Lineup" button
3. Lineup is successfully saved (confirmed in `lineups.csv`)
4. Date becomes locked
5. Refresh the page OR navigate to a different date and come back
6. **Bug**: The checkboxes show different players than the saved lineup

### Root Cause (Discovered via Debug Output)

**The lineup data was loading correctly**, but the checkbox UI state was being cached incorrectly by Streamlit.

Debug output revealed:
- Lineup loaded correctly: ✅
- `active_ids` extracted correctly: `[1, 50, 29]` ✅
- But checkboxes showed: Burton (46), Hayes (50), Sykes (32) ❌

**Root Cause**: Streamlit checkbox keys were not date-specific:
```python
# OLD CODE (buggy):
key=f"player_{player['player_id']}"  # Same key for all dates!
```

When navigating between dates, Streamlit's session state would preserve checkbox state from previous dates because the keys were identical across all dates. For example, if player 46 was checked on Jan 8, the checkbox with key `player_46` would remain checked when switching to Jan 9, even if the lineup data said player 46 should be benched.

### Fix Applied

Changed checkbox keys to include the date, making each date's checkboxes independent:

```python
# NEW CODE (fixed):
key=f"player_{player['player_id']}_{lineup_date}"  # Unique key per date!
```

**Result**: Each date now has its own checkbox state. When you load Jan 9, the checkboxes reflect Jan 9's saved lineup. When you load Jan 10, the checkboxes reflect Jan 10's lineup. No more cross-contamination.

### Impact
- ✅ Saved lineups now display correctly after page refresh
- ✅ Navigating between dates shows correct lineup for each date
- ✅ No impact on CSV data, transaction logs, or scoring (they were already working)
- ✅ No breaking changes to existing saved lineups

---

## Notes
- Transaction logs are working correctly
- Scoring calculations use the correct saved lineups
- This is purely a display issue in the Manager Portal
- Related to player 50 (Tiffany Hayes) replacement - if player didn't exist in cache when lineup was loaded, merge could fail

---

## Feature #1: Bench Points Visualization

### Description
Added a stacked bar chart to the Manager Portal's "Points by Game" section that shows:
- **Orange bars (bottom)**: Points left on the bench from players who actually played (status='played')
- **Blue bars (top)**: Active points earned by starting lineup

This helps managers visualize missed opportunities where they benched players who scored points.

### Status
✅ **COMPLETED** in commits 29c001c, c5adc8b, 97b8df0

### Files Modified

#### 1. [data/handmade/game_id_mapping.csv](data/handmade/game_id_mapping.csv)
**Purpose**: Maps between two incompatible game_id systems
- `player_game_id`: Resets to 1,2 for each date (used in player_game_scores)
- `schedule_game_id`: Sequential 1-56 for entire season (used in game_schedule)

**Why needed**:
- Schedule uses consecutive game_ids (1-56)
- player_game_scores uses resetting game_ids (1,2 per date)
- manager_daily_scores inherits player_game_scores game_ids
- Chart needs to match games correctly to calculate bench points

**Auto-update**: File regenerates automatically when new game stats are added via Admin Portal

#### 2. [etl/data_loader.py](etl/data_loader.py)
**Changes**:
- Added `load_game_id_mapping()` (lines 45-50): Loads the mapping CSV with caching
- Added `update_game_id_mapping()` (lines 53-88): Regenerates entire mapping from current data
  - Reads player_game_scores and game_schedule
  - Matches games by date and order
  - Saves complete mapping with matchup info

#### 3. [app/pages/1_Manager_Portal.py](app/pages/1_Manager_Portal.py)
**Changes**:
- Added `import altair as alt` (line 6): For stacked bar chart
- Replaced simple bar chart with stacked bar implementation (lines ~319-425):
  - Loads game_id_mapping, lineups, player_game_scores
  - Identifies benched players by team matchup
  - Filters for status='played' (excludes DNP)
  - Calculates bench points per game
  - Creates Altair stacked bar chart with proper color ordering

#### 4. [app/pages/2_Admin_Portal.py](app/pages/2_Admin_Portal.py)
**Changes**:
- Added auto-update call after saving game stats (lines 333-335):
  ```python
  # Update game_id mapping
  data_loader.update_game_id_mapping()
  st.cache_data.clear()  # Clear cache to reload mapping
  ```
- Ensures mapping stays in sync with new game data

### How to Rollback (If Feature Breaks)

**Option 1: Remove just the auto-update (keeps feature but requires manual mapping updates)**
```bash
# Remove lines 333-335 from app/pages/2_Admin_Portal.py
# Keep everything else
```

**Option 2: Completely remove bench points feature**
```bash
# Revert to commit before bench points:
git revert 97b8df0  # Remove altair import fix
git revert c5adc8b  # Remove auto-update
git revert 29c001c  # Remove bench points chart

# Or hard reset (if no other changes):
git reset --hard <commit-before-29c001c>
```

**Option 3: Fix specific issues**
- If mapping is wrong: Delete `data/handmade/game_id_mapping.csv` and re-add game stats to regenerate
- If colors reversed: Swap domain order in Manager Portal chart code (lines 418-419)
- If DNPs counted: Check status filter in bench points calculation (line ~382)
- If cache issues: Clear browser cache or add `st.cache_data.clear()` calls

### Key Design Decisions
1. **Used mapping table** instead of fixing underlying data structure (cleaner, less invasive)
2. **Mapping auto-updates** when adding game stats (Option 2 from user choice)
3. **Only counts played games** for bench points (status='played'), not DNPs
4. **Orange (bench) on bottom, blue (active) on top** - visual hierarchy shows active first
5. **Matches by team** - only counts bench points from players whose team played in that game

### Common Issues
- **"NameError: alt is not defined"**: Missing `import altair as alt` (fixed in 97b8df0)
- **Wrong bench points**: Check game_id_mapping is up to date, run update_game_id_mapping()
- **Cache not clearing**: Ensure `st.cache_data.clear()` is called after mapping updates
- **Feature not showing**: Check if lineups exist for the selected manager/date
