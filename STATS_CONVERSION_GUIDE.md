# Converting Unrivaled Box Scores to CSV

## Quick Reference Guide

### From Unrivaled Box Score → Your CSV Format

| Unrivaled Column | How to Get Your CSV Value | Example |
|-----------------|---------------------------|---------|
| **3PT** (e.g., 1-5) | **1PT_MADE** = first number | 1 |
| **FG** (e.g., 10-21) | **2PT_MADE** = FG made - 3PT made | 10 - 1 = 9 |
| **FT** (e.g., 0-0) | **FT_MADE** = first number | 0 |
| **REB** | **REB** = same value | 9 |
| **AST** | **AST** = same value | 1 |
| **STL** | **STL** = same value | 1 |
| **BLK** | **BLK** = same value | 0 |
| **TO** | **TOV** = same value | 3 |
| **PF** | **PF** = same value | 3 |
| Special notes | **GAME_WINNER** = 1 if noted, else 0 | Check "Game Winner" section |
| Play-by-play | **DUNK** = count from video/notes | Usually 0-2 per player |

## Step-by-Step Process

### Example: Kahleah Copper's Line
**Box Score Shows:**
- MIN: 14
- FG: **10-21** (10 made, 21 attempted)
- 3PT: **1-5** (1 made, 5 attempted)
- FT: **0-0** (0 made, 0 attempted)
- REB: 9, AST: 1, STL: 1, BLK: 0, TO: 3, PF: 3
- PTS: 21

**Your CSV Entry:**
```
1PT_MADE = 1       (from 3PT: 1-5)
2PT_MADE = 9       (FG made - 3PT made = 10 - 1)
FT_MADE = 0        (from FT: 0-0)
REB = 9
AST = 1
STL = 1
BLK = 0
TOV = 3
PF = 3
GAME_WINNER = 0    (game winner was Azurá Stevens, not Copper)
DUNK = 0           (check video if unsure)
```

## Finding Player IDs

Use the [data/handmade/players.csv](data/handmade/players.csv) file to match player names to IDs:

```csv
player_id,player_name,team,status
5,Kahleah Copper,Rose,active
2,Rickea Jackson,Mist,active
...
```

## Game Winner Detection

Look for the "Game Winner" note in the box score:
- Example: "Azurá Stevens—Two point shot"
- Give that player `GAME_WINNER = 1`
- All others get `GAME_WINNER = 0`

## Dunk Tracking

Dunks are NOT in the standard box score. You'll need to:
1. Watch the game highlights
2. Check the play-by-play if available
3. Or just set to 0 if you're not tracking dunks

Most games will have 0-3 total dunks across all players.

## Common Mistakes to Avoid

❌ **Wrong:** Using 3PT attempts instead of 3PT made
```
3PT: 1-5  →  1PT_MADE = 5  ❌ NO!
```

✅ **Right:** Use the FIRST number (made shots)
```
3PT: 1-5  →  1PT_MADE = 1  ✓ YES!
```

❌ **Wrong:** Using total FG for 2PT_MADE
```
FG: 10-21  →  2PT_MADE = 10  ❌ NO!
```

✅ **Right:** Subtract 3PT made from FG made
```
FG: 10-21, 3PT: 1-5  →  2PT_MADE = 10 - 1 = 9  ✓ YES!
```

## Template CSV

```csv
game_id,player_id,1PT_MADE,2PT_MADE,FT_MADE,REB,AST,STL,BLK,TOV,PF,GAME_WINNER,DUNK
1,5,1,9,0,9,1,1,0,3,3,0,0
```

## Time-Saving Tips

1. **Copy box score to spreadsheet** - Makes calculations easier
2. **Use Excel formula** for 2PT_MADE: `=FG_MADE - 3PT_MADE`
3. **Batch process** - Do all players from one team, then the other
4. **Double-check totals** - Your points should match the box score
   - Fantasy Points ≠ Game Points (your scoring is different)
   - But verify player game points: `1PT×1 + 2PT×2 + FT×1 = PTS`

## Verification

After creating CSV, verify one player manually:

**Kahleah Copper:**
- Game Points: 1PT×1 + 2PT×2 + FT×1 = 1 + 18 + 0 = **21** ✓
- Fantasy Points: 1×1 + 9×2.5 + 0×1 + 9×1.2 + 1×1 + 1×2 + 0×2 + 3×(-1) + 3×(-0.5) = **29.8 pts**

Game points should match box score (21 = 21 ✓)
