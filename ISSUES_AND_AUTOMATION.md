# Issues, Inconsistencies & Automation Guide

## Known Issues & Quick Fixes

### 1. ✅ **Sticky Lineups** (FIXED)

**Problem:** If a manager forgets to set a lineup, they score 0 points for that day.

**Status:** FIXED - Implemented "sticky lineup" logic:
- **First time:** Uses first 3 players by ID (default)
- **After that:** Keeps using your previous lineup until you change it
- **UI shows:** "Using previous lineup" or "Using default lineup" warning

**Implemented in:** `etl/lineup_manager.py` (get_active_players_for_scoring function)

Logic:
1. Check if lineup exists for game_date → use it
2. If not, find most recent previous lineup → use same 3 active players
3. If no previous lineup, default to first 3 players by ID

Manager Portal shows which lineup is being used with color-coded messages.

---

### 2. ✅ **Game ID Mapping Confusion** (FIXED)

**Problem:** Admins need to know which game_id to use in stats CSV.

**Status:** FIXED - Added game schedule reference in Upload Stats tab.

---

### 3. ⚠️ **No Player Validation** (LOW PRIORITY)

**Problem:** If you upload stats for `player_id: 999` (doesn't exist), it will process without error.

**Fix:** Add validation in `etl/score_calculator.py`:

```python
# In calculate_player_fantasy_points(), add at start:
valid_player_ids = data_loader.load_players()['player_id'].tolist()
invalid = game_stats[~game_stats['player_id'].isin(valid_player_ids)]

if not invalid.empty:
    raise ValueError(f"Invalid player IDs found: {invalid['player_id'].unique()}")
```

---

### 4. ⚠️ **Tournament Assumes 8 Picks** (MEDIUM PRIORITY)

**Problem:** Bracket page crashes if fewer than 8 managers nominate players.

**Fix:** Already has check - shows "Waiting for X more nominations" message. But should handle edge case where season ends before all 8 pick.

**Quick Fix in `app/pages/3_Tournament.py`:**

```python
# Line ~90, change:
if tournament_picks is None or len(tournament_picks) < 8:

# TO:
if tournament_picks is None or len(tournament_picks) == 0:
    st.info("No nominations yet. Managers can nominate players in the 'Make Nomination' tab.")
elif len(tournament_picks) < 8:
    remaining = 8 - len(tournament_picks)
    st.warning(f"⚠️ Waiting for {remaining} more nomination(s)...")
    # ... show who picked so far ...
```

---

### 5. ⚠️ **Timezone Issues** (MEDIUM PRIORITY)

**Problem:** Lineup locks use `datetime.now()` which is server local time. If you're in EST but server is PST, locks will be off by 3 hours.

**Fix:** Add timezone handling in `etl/lineup_manager.py`:

```python
# At top of file:
from datetime import datetime, date, time, timedelta
import pytz

# Define league timezone
LEAGUE_TZ = pytz.timezone('US/Eastern')  # Unrivaled games are in Miami (EST)

# In is_lineup_locked():
return datetime.now(LEAGUE_TZ) >= lock_time.replace(tzinfo=LEAGUE_TZ)
```

**For now:** Just make sure you run the app from a machine in Eastern time, or manually adjust game times in `game_schedule.csv`.

---

### 6. ⚠️ **Empty Game Schedule** (LOW PRIORITY)

**Problem:** Only 4 sample games in `game_schedule.csv`. Need full season.

**Fix:** Add all Unrivaled Season 2 games. Options:
1. Manually add from Unrivaled website
2. Use automation (see below)

---

### 7. ⚠️ **Concurrent Lineup Edits** (LOW PRIORITY)

**Problem:** If two managers edit lineups simultaneously, one could overwrite the other's changes.

**Why it's unlikely:** Small league (8 people), CSV saves are fast, Streamlit Cloud handles basic file locking.

**Fix if needed:** Move to SQLite instead of CSV (future enhancement).

---

### 8. ⚠️ **Draft Interruption** (LOW PRIORITY)

**Problem:** If browser closes mid-draft, progress is lost (`st.session_state` is not persistent).

**Fix:** Save draft progress after each pick:

```python
# In Admin Portal, after line 90:
st.session_state.draft_picks.append((current_pick_num, player_id))

# Add:
# Save progress to temp file
import json
with open('data/processed/draft_temp.json', 'w') as f:
    json.dump(st.session_state.draft_picks, f)

st.rerun()
```

Then load from temp file on page load if it exists.

---

## Stat Scraping & Automation

### Option 1: **Manual CSV Upload** (CURRENT APPROACH)
**Pros:**
- Simple, works today
- No dependencies on external sites
- Full control over data quality

**Cons:**
- Time consuming
- Risk of human error

**Best for:** Leagues where 1 person is committed to being admin

---

### Option 2: **Scrape Unrivaled Website**

**Feasibility:** Medium - Unrivaled likely has box scores on their site

**Implementation:**

```python
# Create: etl/scraper.py

import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_unrivaled_game(game_url: str) -> pd.DataFrame:
    """
    Scrape box score from Unrivaled game page.

    Args:
        game_url: URL to game box score

    Returns:
        DataFrame with player stats
    """
    response = requests.get(game_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # TODO: Parse box score table
    # Structure will depend on Unrivaled's website HTML
    # Look for <table> with player stats

    stats = []
    # ... parsing logic ...

    return pd.DataFrame(stats)

def scrape_latest_games() -> list[pd.DataFrame]:
    """Get stats from all recent games."""
    # TODO: Get list of game URLs from schedule page
    # TODO: Scrape each game
    pass
```

**Challenges:**
- Website structure changes break scraper
- Need to map player names → player_ids
- Site might block scrapers
- Stats format might not match your categories (1PT vs 2PT)

**Time to implement:** 4-8 hours

---

### Option 3: **ESPN/Yahoo Sports APIs**

**Feasibility:** Low - No official Unrivaled coverage yet on major platforms

Once Unrivaled gets bigger, ESPN or Yahoo might add coverage. Then you could use their APIs.

---

### Option 4: **Google Sheets Integration**

**Best middle ground** - Easy stats entry, auto-import:

```python
# Install: pip install gspread oauth2client

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def import_from_google_sheets(sheet_url: str) -> pd.DataFrame:
    """
    Import game stats from Google Sheet.

    Setup:
    1. Create Google Sheet with columns matching your CSV format
    2. Share sheet with service account
    3. Admin enters stats in sheet
    4. Click "Import from Google Sheets" button in app
    """
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_url(sheet_url).sheet1
    data = sheet.get_all_records()

    return pd.DataFrame(data)
```

**Pros:**
- Easier than manual CSV creation
- Multiple people can enter stats
- Mobile-friendly
- Live collaboration

**Cons:**
- Requires Google API setup
- Still manual data entry

**Time to implement:** 1-2 hours

---

### Option 5: **Twitter/Social Media Monitoring**

**Idea:** Unrivaled might post box scores on Twitter. Auto-scrape from there.

**Feasibility:** Very low - Twitter API is expensive, parsing tweets is unreliable.

---

## Recommended Automation Approach

### Phase 1: **Stay Manual** (For Now)
- Use CSV upload for Season 2
- Takes ~5 min per game day
- Most reliable

### Phase 2: **Google Sheets** (Mid-Season)
If manual CSV gets annoying:
1. Create Google Sheet template
2. Add import button to Admin Portal
3. Enter stats in Google Sheets (easier than CSV)
4. Import with one click

### Phase 3: **Web Scraping** (Next Season)
If you run this again for Season 3:
1. Analyze Unrivaled's website structure
2. Build scraper during off-season
3. Test thoroughly before season starts
4. Keep manual CSV as backup

---

## Quick Scraping POC

If you want to test scraping feasibility, try this:

```python
# quick_scrape_test.py
import requests
from bs4 import BeautifulSoup

# Example: Scrape from Unrivaled stats page
url = "https://www.unrivaled.basketball/stats"  # Or specific game URL

response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Print page structure
print(soup.prettify()[:1000])

# Look for tables
tables = soup.find_all('table')
print(f"Found {len(tables)} tables")

for i, table in enumerate(tables):
    print(f"\nTable {i}:")
    rows = table.find_all('tr')
    for row in rows[:3]:  # First 3 rows
        cells = [cell.get_text().strip() for cell in row.find_all(['th', 'td'])]
        print(cells)
```

Run this to see if Unrivaled's stats pages are scrapeable.

---

## Data Quality Checks to Add

### Validation in `score_calculator.py`:

```python
def validate_game_stats(df: pd.DataFrame) -> tuple[bool, str]:
    """
    Validate uploaded game stats before processing.

    Returns:
        (is_valid, error_message)
    """
    required_cols = ['game_id', 'player_id', '1PT_MADE', '2PT_MADE', 'FT_MADE',
                     'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'GAME_WINNER', 'DUNK']

    # Check columns exist
    missing = set(required_cols) - set(df.columns)
    if missing:
        return False, f"Missing columns: {missing}"

    # Check player IDs valid
    valid_players = data_loader.load_players()['player_id'].tolist()
    invalid = df[~df['player_id'].isin(valid_players)]
    if not invalid.empty:
        return False, f"Invalid player IDs: {invalid['player_id'].unique()}"

    # Check no negative stats (except TOV which can be negative in scoring)
    for col in ['1PT_MADE', '2PT_MADE', 'FT_MADE', 'REB', 'AST', 'STL', 'BLK', 'PF', 'DUNK']:
        if (df[col] < 0).any():
            return False, f"Negative values found in {col}"

    # Check GAME_WINNER is 0 or 1
    if not df['GAME_WINNER'].isin([0, 1]).all():
        return False, "GAME_WINNER must be 0 or 1"

    return True, ""
```

Add this check in Admin Portal before saving stats.

---

## Summary

**Critical Issues:** None - system works as-is

**Fixed:**
1. ✅ Sticky lineups - remembers your previous lineup
2. ✅ Game schedule reference in Admin Portal

**Optional Improvements:**
1. Add stats validation (prevents bad data)
2. Handle timezone edge cases

**Automation:**
- Start with manual CSV
- Move to Google Sheets if it gets tedious
- Consider web scraping only if running multiple seasons

**Bottom Line:** The system is production-ready. The "issues" are all edge cases that might never happen in an 8-person league. Focus on running Season 2, then improve based on what actually goes wrong.
