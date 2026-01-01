# Test Data Summary

## ✅ Documentation Fixes Applied

### HIGH Priority Issues Fixed:

1. **README.md Features Section Updated**
   - Added "Sticky Lineups" feature
   - Added "Injury Management" feature
   - These were implemented but not documented

2. **Hardcoded Lock Time Removed**
   - Changed "1:00 PM EST (first game)" to generic "see game_schedule.csv for exact times"
   - File: QUICK_START.md line 135
   - Prevents confusion when games aren't at 1:00 PM

---

## 🎯 Test Data Created

### Test Managers ([data/handmade/managers.csv](data/handmade/managers.csv))

| ID | Manager Name | Fantasy Team Name |
|----|--------------|-------------------|
| 1 | Alex Rivera | Court Crushers |
| 2 | Jordan Chen | Hoop Dreams |
| 3 | Taylor Martinez | Triple Threat |
| 4 | Sam Johnson | Fast Break Kings |
| 5 | Morgan Davis | Slam Squad |
| 6 | Casey Williams | Net Ninjas |
| 7 | Riley Brown | Buckets Brigade |
| 8 | Avery Smith | Rebound Royalty |

### Mock Draft Completed

- **File Created:** `data/processed/draft_results.csv`
- **File Created:** `data/processed/rosters.csv`
- **Draft Type:** Snake draft (6 rounds)
- **Total Picks:** 48 (all available Unrivaled players)
- **Players per Team:** 6

**Each roster includes players from multiple Unrivaled teams** (Breeze, Hive, Rose, Lunar Owls, Vinyl, Laces, Phantom, Mist)

---

## ⚠️ IMPORTANT: Roster Size Adjustment

### Original Plan vs Reality

**Your Original Specification:**
- 9 players per roster (3 active + 6 bench)
- 8 managers × 9 players = 72 players needed

**Unrivaled Season 2 Reality:**
- Only 48 total players exist (6 per team × 8 teams)
- 8 managers × 6 players = 48 players exactly

### Resolution

**Test data uses 6-player rosters:**
- **3 active + 3 bench** (instead of 3 active + 6 bench)
- Every Unrivaled player is on exactly one fantasy team
- No duplicates, no players left out

### Your Options

1. **Keep 6-player rosters** (3 active + 3 bench)
   - Uses all real Unrivaled players
   - More competitive (less depth)
   - No changes needed

2. **Add 24 fictional players** to reach 72 total
   - Allows 9-player rosters as originally planned
   - Would need to create fake player names/stats
   - Not recommended (confusing for managers)

3. **Have fewer managers** (e.g., 6 managers with 8 players each = 48)
   - Not ideal if you already have 8 people

**Recommendation:** **Stick with 6-player rosters**. The system works perfectly with this setup, and having less bench depth makes lineup decisions more strategic.

---

## 🧪 Testing the Interface

### Start the App

```bash
cd unrivaled
uv run streamlit run app/streamlit_app.py
```

### Test These Features

#### Manager Portal
1. **Select different managers** from dropdown (try "Alex Rivera" or "Jordan Chen")
2. **View Roster** - See 6 players per team
3. **Set Lineup** - Check 3 players to set as active
4. **Save Lineup** - Should work without errors
5. **Check sticky lineup** - Change date to tomorrow, see previous lineup persists

#### Admin Portal
6. **View All Rosters** - Expand each team to see their 6 players
7. **Draft Results** - Verify 48 picks shown
8. **Upload Stats** - Try with the example CSV (don't need real data to test UI)

#### Standings
9. **Check standings** - Should show all 8 teams with 0 points initially
10. **Verify draft completion** - No "Draft not complete" warnings

---

## 🗑️ Deleting Test Data

When you're ready to replace test data with your real league:

### Delete Test Draft
```bash
rm data/processed/draft_results.csv
rm data/processed/rosters.csv
```

### Update Real Managers
Edit `data/handmade/managers.csv` with your actual 8 managers:
```csv
manager_id,manager_name,team_name
1,John Doe,Real Team Name 1
2,Jane Smith,Real Team Name 2
...
```

### Run Real Draft
1. Start app
2. Go to Admin Portal → Run Draft
3. Pick 48 players (6 per manager)
4. Save results

---

## 📊 Test Lineups Created

To fully test scoring, you can also create test lineups:

```bash
python3 -c "
import pandas as pd
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from etl import lineup_manager

# Create sample lineup for manager 1 on Jan 5
# (First 3 players from their roster: IDs 1, 16, 17)
success, msg = lineup_manager.save_lineup(
    manager_id=1,
    game_date=date(2026, 1, 5),
    active_player_ids=[1, 16, 17]
)
print(msg)
"
```

This creates a lineup for Alex Rivera (Court Crushers) on Jan 5, 2026.

---

## 🎉 You're Ready to Test!

Everything is set up. Run the app and explore:
- ✅ 8 test managers with fun team names
- ✅ Complete draft (48 picks, 6 per team)
- ✅ All rosters populated
- ✅ Ready for lineup management
- ✅ Ready for stat uploads

**After testing**, delete the test data files above and run your real draft with your actual league members.

---

## Summary of Files Modified

### Data Files (Test Data)
- `data/handmade/managers.csv` - Test managers added
- `data/processed/draft_results.csv` - Mock draft created
- `data/processed/rosters.csv` - Mock rosters created

### Documentation (Fixed)
- `README.md` - Added injury & sticky lineup features
- `QUICK_START.md` - Removed hardcoded lock time

### To Restore Placeholder Data
```bash
# Reset managers to placeholders
cat > data/handmade/managers.csv << 'EOF'
manager_id,manager_name,team_name
1,Manager 1,Team 1
2,Manager 2,Team 2
3,Manager 3,Team 3
4,Manager 4,Team 4
5,Manager 5,Team 5
6,Manager 6,Team 6
7,Manager 7,Team 7
8,Manager 8,Team 8
EOF

# Delete draft/roster files
rm -f data/processed/draft_results.csv
rm -f data/processed/rosters.csv
```
