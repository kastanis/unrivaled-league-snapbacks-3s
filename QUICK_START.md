# Quick Start Guide

## Your Fantasy League is Ready! 🏀

This document summarizes what's done and what you need to do before launching.

---

## ✅ What's Already Built

### Core Features
- ✅ Snake draft system (6 players per team, 8 managers)
- ✅ Daily lineup management (3 active, 3 bench)
- ✅ Lineup locks at first game time each day
- ✅ Sticky lineups (remembers your previous lineup)
- ✅ Fantasy points calculation with your custom scoring
- ✅ Season-long standings (total points)
- ✅ 1-on-1 tournament feature
- ✅ Admin portal for stat uploads
- ✅ Manager portal for lineup management

### Data
- ✅ All 48 Unrivaled Season 2 players
- ✅ 56 regular season games scheduled (Jan 5 - Feb 27, 2026)
- ✅ Scoring system configured (1PT=1, 2PT=2.5, FT=1, REB=1.2, AST=1, STL=2, BLK=2, TOV=-1, PF=-0.5, Game Winner=1.5, Dunk=0.5)
- ✅ Injury support (mark players as injured with 🔴 indicator)

### Documentation
- ✅ README.md - Full setup guide
- ✅ DEPLOYMENT.md - Streamlit Cloud deployment guide
- ✅ ISSUES_AND_AUTOMATION.md - Known issues and automation options
- ✅ PRE_LAUNCH_CHECKLIST.md - What to test before launch

---

## ⚠️ What You Need to Do Before Launch

### 1. Update Manager Information (REQUIRED)

Edit **[data/handmade/managers.csv](data/handmade/managers.csv)** with your actual 8 league managers:

**Current state:**
```csv
manager_id,manager_name,team_name
1,Manager 1,Team 1
2,Manager 2,Team 2
...
```

**Change to:**
```csv
manager_id,manager_name,team_name
1,John Smith,Court Crushers
2,Sarah Johnson,Hoop Dreams
3,Mike Williams,The Ballers
4,Emily Davis,Triple Threat
5,Chris Lee,Fast Break
6,Jessica Brown,Slam Squad
7,David Wilson,Net Ninjas
8,Amanda Garcia,Buckets Brigade
```

- `manager_name` = Real person's name
- `team_name` = Their fantasy team name (whatever they want)

### 2. Mark Injured Players (OPTIONAL)

If Napheesa Collier or others are out, update **[data/handmade/players.csv](data/handmade/players.csv)**:

Find the player (e.g., player_id 43) and change:
```csv
43,Napheesa Collier,Mist,active
```
To:
```csv
43,Napheesa Collier,Mist,injured
```

This will:
- Show 🔴 next to her name in lineups
- Prevent managers from selecting her
- Keep her on rosters (she doesn't disappear)

### 3. Test Locally (RECOMMENDED)

Before deploying to the cloud, test everything works:

```bash
cd unrivaled
uv run streamlit run app/streamlit_app.py
```

**Test these workflows:**
- [ ] Run a complete draft (48 picks)
- [ ] Set lineups for 2-3 managers
- [ ] Upload sample game stats
- [ ] Verify scores calculate correctly
- [ ] Check standings display properly

### 4. Deploy to Streamlit Cloud (FOR REMOTE ACCESS)

If you want managers to access from anywhere (not just your WiFi):

**Follow the complete guide in [DEPLOYMENT.md](DEPLOYMENT.md)**

Quick version:
```bash
# Create requirements files (already done!)
# Initialize git
git init
git add .
git commit -m "Initial commit"
git branch -M main

# Push to GitHub (create repo first at github.com/new)
git remote add origin https://github.com/YOUR_USERNAME/unrivaled-fantasy-league.git
git push -u origin main

# Then deploy at share.streamlit.io
```

---

## 📅 Season Timeline

### Before January 5, 2026
- [ ] Update managers.csv with real names
- [ ] Test the app locally
- [ ] Deploy to Streamlit Cloud (optional but recommended)
- [ ] Share app URL with all 8 managers
- [ ] Run the draft together

### January 5 - First Game
- [ ] Managers set their initial lineups
- [ ] Lineups lock at first game time (see game_schedule.csv for exact times)

### After Each Game Day
- [ ] Admin collects game stats
- [ ] Admin uploads via Admin Portal → Upload Stats
- [ ] Scores calculate automatically
- [ ] Standings update automatically
- [ ] Managers see their points in Manager Portal

### Mid-Season (Tournament Setup)
- [ ] Each manager nominates 1 player for 1-on-1 tournament
- [ ] Tournament bracket auto-generates based on standings

### February 27 - Last Regular Season Game
- [ ] Final standings determine league champion
- [ ] Highest total points wins!

---

## 🎯 How to Use

### For Managers

**Access the app:**
- Local: `http://localhost:8501` (same WiFi only)
- Cloud: Your Streamlit Cloud URL (from anywhere)

**Set daily lineups:**
1. Go to Manager Portal
2. Select your name from dropdown
3. Click "Set Lineup" tab
4. Check 3 players to be active
5. Click "Save Lineup" (before lock time!)

**View your scores:**
1. Go to Manager Portal
2. Select your name
3. Click "My Scores" tab
4. See season total, recent games, and chart

### For Admin (You)

**Run the draft:**
1. Go to Admin Portal
2. Click "Run Draft" tab
3. Pick players one by one (48 total picks)
4. Click "Save Draft Results" when complete

**Upload game stats:**
1. Create CSV with game stats (see format in Admin Portal)
2. Go to Admin Portal → "Upload Stats" tab
3. Upload CSV file
4. Select game date
5. Click "Save Stats and Calculate Scores"
6. Done! Scores update automatically

**View all rosters:**
1. Go to Admin Portal
2. Click "View All Rosters" tab
3. See all 8 teams expanded

---

## 📊 Required CSV Format for Game Stats

When uploading stats, your CSV must have these columns:

```csv
game_id,player_id,1PT_MADE,2PT_MADE,FT_MADE,REB,AST,STL,BLK,TOV,PF,GAME_WINNER,DUNK
1,43,2,6,3,8,4,2,1,2,2,0,1
1,12,1,4,2,5,3,1,0,1,1,1,0
...
```

- `game_id`: From game schedule (1-56)
- `player_id`: From players.csv (1-48)
- All stats should be whole numbers (except game_winner which is 0 or 1)

**Download example CSV** from Admin Portal → Upload Stats tab.

---

## 🔧 Helpful Commands

### Run app locally
```bash
cd unrivaled
uv run streamlit run app/streamlit_app.py
```

### Update packages
```bash
uv sync
```

### View dependencies
```bash
uv pip list
```

### Backup your data
```bash
cp -r data/ data_backup_$(date +%Y%m%d)/
```

---

## 🆘 Common Issues

### "No rosters found - complete draft first"
- You need to run the draft in Admin Portal first
- Draft must complete all 48 picks

### "Lineup locked"
- Lineups lock at first game time of each day
- Check game schedule for lock times
- Can't change lineup after lock

### "Must select exactly 3 players"
- Count your checkboxes - need exactly 3
- Injured players (🔴) can't be selected

### Scores not calculating
- Check CSV format matches required columns
- Verify player_id values are valid (1-48)
- Try "Recalculate All Scores" in Admin Portal

---

## 📚 Additional Documentation

- **[README.md](README.md)** - Complete setup and usage guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deploy to Streamlit Cloud
- **[ISSUES_AND_AUTOMATION.md](ISSUES_AND_AUTOMATION.md)** - Known issues and automation options
- **[PRE_LAUNCH_CHECKLIST.md](PRE_LAUNCH_CHECKLIST.md)** - Testing checklist

---

## 🎉 You're Ready!

Your fantasy league system is production-ready. Just:
1. Update managers.csv
2. Test locally
3. Deploy (optional)
4. Run the draft
5. Play!

Good luck with your Unrivaled Fantasy League Season 2! 🏀
