# Excel Template for Stats Conversion

## Setup Instructions

### Step 1: Create Excel Template

Open Excel/Google Sheets and create these columns:

| Column | Header | Description | Formula? |
|--------|--------|-------------|----------|
| A | Player Name | Type from box score | Manual |
| B | Team | Rose/Mist/etc | Manual |
| C | FG_Made | From "FG: 10-21" (first number) | Manual |
| D | FG_Att | From "FG: 10-21" (second number) | Manual |
| E | 3PT_Made | From "3PT: 1-5" (first number) | Manual |
| F | 3PT_Att | From "3PT: 1-5" (second number) | Manual |
| G | FT_Made | From "FT: 0-0" (first number) | Manual |
| H | FT_Att | From "FT: 0-0" (second number) | Manual |
| I | REB | Total rebounds | Manual |
| J | AST | Assists | Manual |
| K | STL | Steals | Manual |
| L | BLK | Blocks | Manual |
| M | TO | Turnovers | Manual |
| N | PF | Personal fouls | Manual |
| O | Winner? | YES or NO | Manual |
| P | Dunks | Count (usually 0) | Manual |
| **Q** | **player_id** | **Look up from players.csv** | **Use VLOOKUP** |
| **R** | **1PT_MADE** | **=E2** | **Formula** |
| **S** | **2PT_MADE** | **=C2-E2** | **Formula** |
| **T** | **FT_MADE** | **=G2** | **Formula** |
| **U** | **REB** | **=I2** | **Formula** |
| **V** | **AST** | **=J2** | **Formula** |
| **W** | **STL** | **=K2** | **Formula** |
| **X** | **BLK** | **=L2** | **Formula** |
| **Y** | **TOV** | **=M2** | **Formula** |
| **Z** | **PF** | **=N2** | **Formula** |
| **AA** | **GAME_WINNER** | **=IF(O2="YES",1,0)** | **Formula** |
| **AB** | **DUNK** | **=P2** | **Formula** |

### Step 2: Add Formulas (Starting in Row 2)

**Cell Q2** (player_id lookup):
```excel
=VLOOKUP(A2,PlayerList!A:B,2,FALSE)
```

**Cell R2** (1PT_MADE):
```excel
=E2
```

**Cell S2** (2PT_MADE):
```excel
=C2-E2
```

**Cell T2** (FT_MADE):
```excel
=G2
```

**Cells U2-Z2** (Copy stats):
```excel
U2: =I2  (REB)
V2: =J2  (AST)
W2: =K2  (STL)
X2: =L2  (BLK)
Y2: =M2  (TOV)
Z2: =N2  (PF)
```

**Cell AA2** (GAME_WINNER):
```excel
=IF(O2="YES",1,0)
```

**Cell AB2** (DUNK):
```excel
=P2
```

### Step 3: Create Player Lookup Sheet

Create a second sheet named "PlayerList" with:
- Column A: Player names (copy from `data/handmade/players.csv`)
- Column B: Player IDs (1-48)

Example:
```
A                    B
Paige Bueckers       1
Rickea Jackson       2
Dominique Malonga    3
...
```

### Step 4: Usage Workflow

**For each game:**

1. Open Unrivaled box score in browser
2. Copy stats into Excel columns A-P (the manual columns)
3. Formulas in columns Q-AB calculate automatically
4. Add game_id column manually (set to 1 for first game, 2 for second, etc.)
5. Copy columns with these headers: `game_id,player_id,1PT_MADE,2PT_MADE,FT_MADE,REB,AST,STL,BLK,TOV,PF,GAME_WINNER,DUNK`
6. Paste into new CSV file
7. Upload to Admin Portal

## Multiple Games Same Day

**Option 1: Separate CSVs**
- Create one CSV per game
- Upload each one separately with different game numbers

**Option 2: Combined CSV** (Recommended)
- Combine all games from same day in one Excel file
- Change game_id for each game (game 1 = 1, game 2 = 2, etc.)
- Export entire sheet as one CSV
- Upload once with the game date

Example combined CSV:
```csv
game_id,player_id,1PT_MADE,2PT_MADE,FT_MADE,REB,AST,STL,BLK,TOV,PF,GAME_WINNER,DUNK
1,5,1,9,0,9,1,1,0,3,3,0,0
1,2,1,4,3,7,1,0,0,1,1,0,0
2,10,0,7,1,4,7,0,0,3,3,1,0
2,15,2,3,2,8,2,1,1,2,4,0,0
```

## Quick Copy Template

For Google Sheets users, here's a template you can copy:

```
=ARRAYFORMULA(IF(ROW(A:A)=1,"player_id",IF(A:A="","",VLOOKUP(A:A,PlayerList!A:B,2,0))))
```

This auto-fills the player_id column based on player names.

## Tips

1. **Save your template** - Keep it open and reuse for each game day
2. **Color code** - Make manual entry columns yellow, formula columns green
3. **Double-check** - Verify one player's math: 1PT×1 + 2PT×2 + FT×1 should equal their PTS
4. **Batch process** - Do all games for the week on Sunday night
5. **Use filters** - Excel filters help find specific players quickly

## Example Row

If box score shows:
- Kahleah Copper
- FG: 10-21
- 3PT: 1-5
- FT: 0-0
- REB: 9, AST: 1, STL: 1, BLK: 0, TO: 3, PF: 3

You enter in columns A-P:
```
A: Kahleah Copper
B: Rose
C: 10
D: 21
E: 1
F: 5
G: 0
H: 0
I: 9
J: 1
K: 1
L: 0
M: 3
N: 3
O: NO
P: 0
```

Excel calculates in columns Q-AB:
```
Q: 5 (her player_id)
R: 1 (1PT_MADE = 3PT made)
S: 9 (2PT_MADE = 10-1)
T: 0 (FT_MADE)
U-Z: 9,1,1,0,3,3 (stats copied)
AA: 0 (not game winner)
AB: 0 (no dunks)
```

Final CSV line:
```csv
1,5,1,9,0,9,1,1,0,3,3,0,0
```
