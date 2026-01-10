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
