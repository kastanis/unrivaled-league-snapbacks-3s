# Test Suite - Unrivaled Fantasy League

## Season Simulation Tests

Run complete end-to-end tests that simulate a full fantasy season.

### Running Tests

```bash
# Run all tests
uv run python tests/test_season_simulation.py

# Or with pytest (if installed)
uv run pytest tests/test_season_simulation.py -v
```

### Test Coverage

The test suite includes:

1. **Draft Test** - Simulates complete snake draft (48 picks, 8 managers)
2. **Lineup Management** - Sets lineups for multiple dates
3. **Sticky Lineups** - Verifies lineups persist to next day
4. **Stats Upload & Scoring** - Uploads game stats and calculates fantasy points
5. **Standings** - Verifies standings calculation and ranking
6. **Lineup Locks** - Tests that past dates are locked
7. **Tournament** - Tests player nominations for tournament
8. **Validation** - Tests all error cases (too few players, duplicates, etc.)
9. **Full Season** - Complete end-to-end simulation

### Test Results

✅ **All 10 tests passing!**
1. Config constants ✓
2. Draft functionality ✓
3. Lineup management ✓
4. Sticky lineups ✓
5. Stats upload & scoring ✓
6. Standings calculation ✓
7. Lineup locks ✓
8. Tournament nominations ✓
9. Validation rules ✓
10. Full season simulation ✓

### Bugs Fixed

**Fixed in score_calculator.py:**
- Added empty DataFrame check before filtering by game_date (lines 134, 151)
- Prevents KeyError when processing first game stats

**Fixed in standings_updater.py:**
- Changed initial ranks from 0 to 1-8 when no scores exist (lines 18-30)
- Managers now show proper rankings even before first game

**Fixed in lineup_manager.py:**
- Added check to always lock past dates (line 44-46)
- Past dates now correctly show as locked regardless of game schedule

**Fixed in test_season_simulation.py:**
- Corrected test date logic to use actual past/future dates relative to test execution

### Warnings

The Streamlit cache warnings during tests are normal - tests run without the Streamlit runtime, which is expected.

---

## Tournament Tests

Run comprehensive tests for the 1-on-1 tournament feature.

### Running Tournament Tests

```bash
# Run tournament tests
uv run python tests/test_tournament.py
```

### Test Coverage

The tournament test suite includes:

1. **Tournament Nominations** - All 8 managers can nominate one player from their roster
2. **Bracket Generation** - Bracket is correctly seeded based on regular season standings
3. **Tournament Scoring** - Simulates quarterfinal games using full fantasy scoring
4. **Full Stats Tracking** - Verifies tournament uses all 11 stat categories (not just points)
5. **Standings Integration** - Regular season performance determines tournament seeding

### Test Results

✅ **All 5 tournament tests passing!**
1. Tournament nominations ✓
2. Bracket generation with seeding ✓
3. Tournament scoring simulation ✓
4. Full stats tracked ✓
5. Standings integration ✓

### Key Features Tested

**Tournament Format:**
- Each manager nominates 1 player from their roster
- Seeding based on regular season standings (rank 1 = seed 1)
- Classic tournament matchups: 1v8, 4v5, 2v7, 3v6
- Winners advance to semifinals

**Scoring:**
- Uses full fantasy point system (all 11 stat categories)
- Same scoring as regular season: 1PT=1, 2PT=2.5, REB=1.2, AST=1, STL=2, BLK=2, etc.
- Not just game score - rebounds, assists, steals, and blocks all count!

**Test Output Example:**
```
🏀 QUARTERFINALS:
  Matchup 1: (1) Court Crushers vs (8) Rebound Royalty
  Matchup 2: (4) Fast Break Kings vs (5) Slam Squad
  Matchup 3: (2) Hoop Dreams vs (7) Buckets Brigade
  Matchup 4: (3) Triple Threat vs (6) Net Ninjas
```
