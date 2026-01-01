# Unrivaled Fantasy Basketball League

A Streamlit-based fantasy basketball league system for Unrivaled Season 2 (Jan 5 - Feb 27, 2026).

## Features

- **8-Manager League** with 6-player rosters (3 active + 3 bench)
- **Snake Draft** before season starts
- **Daily Lineup Management** - Set 3 active players each day (locks at first game)
- **Sticky Lineups** - Your previous lineup persists until you change it (no more forgetting!)
- **Injury Management** - Mark players as injured; they show 🔴 and can't be selected
- **Automated Scoring** - Fantasy points calculated from game stats
- **Season-Long Standings** - Total points format (not weekly head-to-head)
- **1-on-1 Tournament** - Single elimination bracket with player nominations

## Scoring System

- 1PT Made = 1.0 points
- 2PT Made = 2.5 points
- FT Made = 1.0 points
- Rebound = 1.2 points
- Assist = 1.0 points
- Steal = 2.0 points
- Block = 2.0 points
- Turnover = -1.0 points
- Personal Foul = -0.5 points
- Game Winner = 1.5 points
- Dunk = 0.5 points

## Quick Start

### Installation

```bash
cd unrivaled
uv sync
```

### Run the App

```bash
uv run streamlit run app/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

### Accessing from Phone/Other Devices

When you run the app, Streamlit shows a Network URL (e.g., `http://192.168.1.66:8501`). Other devices on the same WiFi network can access the league using this URL.

## For Managers

### 1. View Your Roster

1. Go to **Manager Portal** (sidebar)
2. Select your name from dropdown
3. Click "My Roster" tab to see your 6 players

### 2. Set Daily Lineups

1. Go to "Set Lineup" tab
2. Select the date
3. Check exactly 3 players to set as active
4. Click "Save Lineup"

**Important:** Lineups lock at the first game time each day. You cannot change your lineup after it locks!

### 3. Check Scores

- **My Scores** tab shows your daily scores and season total
- **Standings** tab shows league rankings (your rank is highlighted)

### 4. Tournament

1. Go to **Tournament** page (sidebar)
2. Select your team
3. Nominate 1 player from your roster for the 1-on-1 tournament
4. Seeding is based on regular season standings
5. Head-to-head matchups decided by fantasy points scored in that round

## For Admin

### 1. Run the Draft

1. Go to **Admin Portal** → "Run Draft" tab
2. Use the simple draft interface:
   - Shows current pick number, round, and manager
   - Select player from available list
   - Click "Make Pick"
   - Repeat for all 48 picks (8 managers × 6 players)
3. After all picks, click "Save Draft Results"

### 2. Upload Game Stats

After each game or game day:

1. Go to **Admin Portal** → "Upload Stats" tab
2. Prepare a CSV file with these columns:
   - `game_id`, `player_id`, `1PT_MADE`, `2PT_MADE`, `FT_MADE`
   - `REB`, `AST`, `STL`, `BLK`, `TOV`, `PF`
   - `GAME_WINNER` (1 or 0), `DUNK` (count)
3. Upload the CSV
4. Select game date and game number
5. Click "Save Stats and Calculate Scores"
6. Scores and standings update automatically!

**Tip:** Download the example CSV from the Admin Portal to see the format.

### 3. View All Rosters

Go to "View All Rosters" tab to see every manager's team.

### 4. Recalculate Scores

If you need to fix errors or update scoring:

1. Go to "Recalculate Scores" tab
2. Click "Recalculate All Scores" to rebuild everything from scratch
3. Or calculate for a specific date only

## Data Files

### Configuration Files (`data/handmade/`)

These files are pre-populated and can be edited:

- `players.csv` - All 48 Unrivaled Season 2 players
- `managers.csv` - 8 fantasy managers (edit names/team names here)
- `scoring_config.csv` - Fantasy point values (can modify scoring system)
- `game_schedule.csv` - Unrivaled game schedule (for lineup locks)

### Generated Files (`data/processed/`)

These are created automatically:

- `draft_results.csv` - Complete draft history
- `rosters.csv` - Current team rosters
- `lineups.csv` - Daily lineup decisions
- `player_game_scores.csv` - Fantasy points per player per game
- `manager_daily_scores.csv` - Team totals per day
- `standings.csv` - League standings
- `tournament_picks.csv` - Tournament player nominations

### Game Stats (`data/source/game_stats/`)

Upload game stats CSVs here (admin uploads via UI).

## Customization

### Change Manager Names

Edit `data/handmade/managers.csv`:

```csv
manager_id,manager_name,team_name
1,Alice,The Dominators
2,Bob,Hoop Dreams
...
```

### Modify Scoring System

Edit `data/handmade/scoring_config.csv` to change point values.

### Update Game Schedule

Edit `data/handmade/game_schedule.csv` to add/modify games and times (for lineup locks).

## Project Structure

```
unrivaled/
├── app/
│   ├── streamlit_app.py        # Main entry point
│   └── pages/
│       ├── 1_Manager_Portal.py  # Manager interface
│       ├── 2_Admin_Portal.py    # Admin tools
│       └── 3_Tournament.py      # 1-on-1 tournament
├── etl/
│   ├── data_loader.py          # CSV read/write utilities
│   ├── draft_engine.py         # Snake draft logic
│   ├── lineup_manager.py       # Lineup validation & locking
│   ├── score_calculator.py     # Fantasy points calculation
│   └── standings_updater.py    # Rankings & totals
└── data/
    ├── handmade/               # Manual configs
    ├── source/                 # Raw game stats
    └── processed/              # Generated results
```

## Remote Deployment

Want your managers to access the league from anywhere, not just your WiFi?

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for a complete guide to deploying on Streamlit Cloud (FREE).

**Quick steps:**
1. Push code to GitHub
2. Deploy to [share.streamlit.io](https://share.streamlit.io)
3. Share your app URL with all 8 managers
4. They can access from any device, anywhere

All data (lineups, scores, stats) persists automatically!

---

## Troubleshooting

### App won't start

Make sure you've installed dependencies:
```bash
uv sync
```

### Can't access from phone

1. Make sure your phone is on the same WiFi network
2. Use the Network URL shown when you start the app (not `localhost`)
3. If it doesn't work, try the External URL instead

### Scores not calculating

1. Check that game stats CSV has all required columns
2. Verify `player_id` values match those in `players.csv` (1-48)
3. Try "Recalculate All Scores" in Admin Portal

### Lineup won't save

- Make sure you selected exactly 3 players
- Check that lineup isn't locked (past first game time)
- Verify the draft is complete

## Season Workflow

1. **Pre-Season:** Run the draft
2. **During Season:**
   - Managers set daily lineups (before first game)
   - Admin uploads game stats after games
   - Standings update automatically
3. **Mid-Season:** Managers nominate players for tournament
4. **Tournament:** Head-to-head elimination based on fantasy points per round
5. **End of Season:** Highest total points wins the league!

## Support

Issues? Questions? Check:
- Manager Portal for your personal stats
- Admin Portal → "View All Rosters" to verify draft results
- Game schedule CSV for lineup lock times

## Sources

- Unrivaled Season 2 rosters from [Unrivaled Basketball](https://www.unrivaled.basketball/)
- Scoring system customizable via `scoring_config.csv`
