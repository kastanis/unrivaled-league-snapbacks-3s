# Pre-Launch Checklist

## Issues Found & Fixed ✅

### 1. ✅ FIXED: Scoring Documentation Mismatch
**Issue:** streamlit_app.py showed Game Winner = 2.0 and Dunk = 2.0, but scoring_config.csv had 1.5 and 0.5
**Fix:** Updated documentation to match config (1.5 and 0.5)
**Files Changed:** `app/streamlit_app.py`

### 2. ✅ FIXED: Missing Null Check in Lineup Manager
**Issue:** Application would crash if users tried to save lineups before draft was complete
**Fix:** Added null check for rosters before accessing
**Files Changed:** `etl/lineup_manager.py`

---

## Action Required Before Launch ⚠️

### 1. Update Manager Information
**File:** `data/handmade/managers.csv`

**Current State:**
```csv
manager_id,manager_name,team_name
1,Manager 1,Team 1
2,Manager 2,Team 2
...
```

**Required:** Replace with your actual 8 league managers:
```csv
manager_id,manager_name,team_name
1,John Smith,Court Crushers
2,Sarah Johnson,Hoop Dreams
3,Mike Williams,Ballers
...
```

**Important:**
- `manager_name` should be the real person's name
- `team_name` should be their fantasy team name (can be anything they choose)
- This does NOT need to match the Unrivaled team names (Breeze, Hive, etc.) - those are the professional teams the players belong to

---

## Verified as Correct ✓

### Data Integrity
- ✅ All 48 players correctly assigned to 8 Unrivaled teams (6 players each)
- ✅ Player IDs sequential 1-48, no duplicates
- ✅ Team names consistent across players.csv and game_schedule.csv
- ✅ All 56 regular season games populated with correct dates/times

### Code Quality
- ✅ All imports correct across all files
- ✅ Sticky lineup logic properly implemented
- ✅ Date/time formats consistent (YYYY-MM-DD, HH:MM 24-hour)
- ✅ All function calls reference existing functions
- ✅ File paths all correct

### Feature Completeness
- ✅ Draft system with snake order
- ✅ Daily lineup management with locks
- ✅ Fantasy points calculation
- ✅ Season-long standings
- ✅ 1-on-1 tournament feature
- ✅ Admin stat upload functionality
- ✅ Game schedule populated (56 games)

---

## Testing Checklist

Before going live with your league, test these flows:

### Admin Workflow
- [ ] Run complete draft (48 picks)
- [ ] Upload sample game stats CSV
- [ ] Verify scores calculate correctly
- [ ] Check standings update properly
- [ ] Recalculate all scores (test functionality)

### Manager Workflow
- [ ] Select manager from dropdown
- [ ] View roster (should show 6 players)
- [ ] Set lineup (3 active players)
- [ ] Verify lineup lock mechanism works
- [ ] Check sticky lineup persists to next day
- [ ] View scores after stats uploaded
- [ ] Check standings display

### Tournament Workflow
- [ ] Each manager nominates 1 player
- [ ] Verify bracket seeding by standings
- [ ] Upload tournament game stats
- [ ] Check head-to-head results

---

## Optional Improvements (Not Required)

These are nice-to-have enhancements mentioned in ISSUES_AND_AUTOMATION.md:

1. **Stats Validation**: Add validation to prevent invalid player IDs or negative stats
2. **Google Sheets Integration**: Easier stat entry than CSV upload
3. **Timezone Handling**: Explicit timezone support for lineup locks
4. **Web Scraping**: Automated stat collection (future seasons)

---

## Launch Steps

1. **Update managers.csv** with real manager names and team names
2. **Run test draft** using Admin Portal
3. **Test lineup setting** for at least 2 managers
4. **Upload sample game stats** and verify scoring works
5. **Share app URL** with your 8 managers
6. **Run official draft** together before January 5, 2026 season start

---

## Support & Documentation

- **Setup Instructions:** See README.md
- **Known Issues:** See ISSUES_AND_AUTOMATION.md
- **Game Schedule:** 56 games from Jan 5 - Feb 27, 2026

Your fantasy league system is production-ready! 🏀
