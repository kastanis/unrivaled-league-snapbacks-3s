"""Integration tests that simulate a complete fantasy season."""

import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl import data_loader, draft_engine, lineup_manager, score_calculator, standings_updater
from etl.config import (
    NUM_MANAGERS, PLAYERS_PER_MANAGER, TOTAL_DRAFT_PICKS,
    ACTIVE_PLAYERS_PER_DAY, SEASON_START
)

# Try to import pytest, but don't require it
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Mock pytest.fixture decorator for standalone mode
    class MockPytest:
        @staticmethod
        def fixture(autouse=True):
            def decorator(func):
                return func
            return decorator
    pytest = MockPytest()


class TestSeasonSimulation:
    """Test complete season workflow."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Store original processed files
        self.backup_files = {}
        processed_dir = Path(__file__).parent.parent / "data" / "processed"

        for file in processed_dir.glob("*.csv"):
            self.backup_files[file.name] = file.read_text() if file.exists() else None

        yield

        # Restore original files
        for filename, content in self.backup_files.items():
            file_path = processed_dir / filename
            if content is not None:
                file_path.write_text(content)
            elif file_path.exists():
                file_path.unlink()

    def test_01_draft_complete_season(self):
        """Test running a complete draft."""
        print("\n=== TEST 1: Running Draft ===")

        # Load players and managers
        players = data_loader.load_players()
        managers = data_loader.load_managers()

        assert len(managers) == NUM_MANAGERS, f"Expected {NUM_MANAGERS} managers"
        assert len(players) == TOTAL_DRAFT_PICKS, f"Expected {TOTAL_DRAFT_PICKS} players"

        # Create mock draft picks (all players in order)
        draft_picks = [(i + 1, player_id) for i, player_id in enumerate(players['player_id'].tolist())]

        # Execute draft
        draft_df, rosters_df = draft_engine.execute_draft(draft_picks)

        # Verify draft results
        assert len(draft_df) == TOTAL_DRAFT_PICKS, f"Expected {TOTAL_DRAFT_PICKS} draft picks"
        assert len(rosters_df) == TOTAL_DRAFT_PICKS, f"Expected {TOTAL_DRAFT_PICKS} roster entries"

        # Verify each manager got correct number of players
        for manager_id in managers['manager_id']:
            manager_picks = rosters_df[rosters_df['manager_id'] == manager_id]
            assert len(manager_picks) == PLAYERS_PER_MANAGER, \
                f"Manager {manager_id} should have {PLAYERS_PER_MANAGER} players"

        # Save draft
        draft_engine.save_draft(draft_df, rosters_df)

        # Verify draft is complete
        assert draft_engine.validate_draft_complete(), "Draft should be marked complete"

        print(f"✅ Draft complete: {TOTAL_DRAFT_PICKS} picks, {NUM_MANAGERS} managers")

    def test_02_set_lineups_multiple_dates(self):
        """Test setting lineups for multiple game dates."""
        print("\n=== TEST 2: Setting Lineups ===")

        # Ensure draft is complete
        if not draft_engine.validate_draft_complete():
            self.test_01_draft_complete_season()

        managers = data_loader.load_managers()

        # Set lineups for first 3 game dates
        game_dates = [
            SEASON_START,
            SEASON_START + timedelta(days=1),
            SEASON_START + timedelta(days=2)
        ]

        for game_date in game_dates:
            for manager_id in managers['manager_id']:
                # Get manager's roster
                roster = draft_engine.get_manager_roster(manager_id)

                # Select first 3 players as active
                active_players = roster.sort_values('player_id')['player_id'].head(ACTIVE_PLAYERS_PER_DAY).tolist()

                # Save lineup
                success, message = lineup_manager.save_lineup(manager_id, game_date, active_players)

                assert success, f"Failed to save lineup for manager {manager_id} on {game_date}: {message}"

        # Verify lineups were saved
        lineups = data_loader.load_lineups()
        assert lineups is not None and not lineups.empty, "Lineups should be saved"

        # Should have NUM_MANAGERS * len(game_dates) * PLAYERS_PER_MANAGER entries
        expected_entries = NUM_MANAGERS * len(game_dates) * PLAYERS_PER_MANAGER
        assert len(lineups) == expected_entries, \
            f"Expected {expected_entries} lineup entries, got {len(lineups)}"

        print(f"✅ Lineups set for {len(game_dates)} dates, {NUM_MANAGERS} managers each")

    def test_03_sticky_lineup_functionality(self):
        """Test that lineups persist to next day (sticky lineup)."""
        print("\n=== TEST 3: Testing Sticky Lineups ===")

        # Ensure draft and initial lineups exist
        if not draft_engine.validate_draft_complete():
            self.test_01_draft_complete_season()

        manager_id = 1
        date1 = SEASON_START
        date2 = SEASON_START + timedelta(days=7)  # A week later

        # Get roster
        roster = draft_engine.get_manager_roster(manager_id)
        active_players = roster.sort_values('player_id')['player_id'].head(ACTIVE_PLAYERS_PER_DAY).tolist()

        # Set lineup for date1
        success, _ = lineup_manager.save_lineup(manager_id, date1, active_players)
        assert success, "Should save lineup for date1"

        # Get active players for date2 (without setting lineup)
        # Should return the same players from date1 (sticky)
        sticky_players = lineup_manager.get_active_players_for_scoring(manager_id, date2)

        assert len(sticky_players) == ACTIVE_PLAYERS_PER_DAY, \
            f"Should have {ACTIVE_PLAYERS_PER_DAY} active players from sticky lineup"
        assert sticky_players == active_players, "Sticky lineup should match original lineup"

        print(f"✅ Sticky lineup works: {sticky_players}")

    def test_04_upload_game_stats_and_calculate_scores(self):
        """Test uploading game stats and calculating fantasy scores."""
        print("\n=== TEST 4: Uploading Stats & Calculating Scores ===")

        # Ensure draft and lineups exist
        if not draft_engine.validate_draft_complete():
            self.test_01_draft_complete_season()
            self.test_02_set_lineups_multiple_dates()

        game_date = SEASON_START

        # Create mock game stats for first game
        # Get 6 players (3 from each of 2 teams to make a game)
        players = data_loader.load_players()
        sample_players = players.head(6)['player_id'].tolist()

        game_stats = pd.DataFrame([
            {
                'game_id': 1,
                'player_id': sample_players[0],
                '1PT_MADE': 2,
                '2PT_MADE': 5,
                'FT_MADE': 3,
                'REB': 8,
                'AST': 4,
                'STL': 2,
                'BLK': 1,
                'TOV': 2,
                'PF': 3,
                'GAME_WINNER': 1,
                'DUNK': 0
            },
            {
                'game_id': 1,
                'player_id': sample_players[1],
                '1PT_MADE': 1,
                '2PT_MADE': 6,
                'FT_MADE': 2,
                'REB': 5,
                'AST': 3,
                'STL': 1,
                'BLK': 0,
                'TOV': 1,
                'PF': 2,
                'GAME_WINNER': 0,
                'DUNK': 1
            },
            {
                'game_id': 1,
                'player_id': sample_players[2],
                '1PT_MADE': 0,
                '2PT_MADE': 4,
                'FT_MADE': 1,
                'REB': 6,
                'AST': 2,
                'STL': 0,
                'BLK': 2,
                'TOV': 0,
                'PF': 1,
                'GAME_WINNER': 0,
                'DUNK': 0
            }
        ])

        # Save game stats
        data_loader.save_game_stats(game_stats, game_date, game_num=1)

        # Calculate scores
        score_calculator.update_scores_for_date(game_date)

        # Verify player scores were calculated
        player_scores = data_loader.load_player_game_scores()
        assert player_scores is not None and not player_scores.empty, "Player scores should be calculated"

        # Verify scoring formula (spot check first player)
        first_player_stats = game_stats.iloc[0]
        expected_score = (
            first_player_stats['1PT_MADE'] * 1.0 +
            first_player_stats['2PT_MADE'] * 2.5 +
            first_player_stats['FT_MADE'] * 1.0 +
            first_player_stats['REB'] * 1.2 +
            first_player_stats['AST'] * 1.0 +
            first_player_stats['STL'] * 2.0 +
            first_player_stats['BLK'] * 2.0 +
            first_player_stats['TOV'] * -1.0 +
            first_player_stats['PF'] * -0.5 +
            first_player_stats['GAME_WINNER'] * 1.5 +
            first_player_stats['DUNK'] * 0.5
        )

        player1_score = player_scores[
            (player_scores['player_id'] == sample_players[0]) &
            (player_scores['game_date'] == game_date)
        ]['fantasy_points'].iloc[0]

        assert abs(player1_score - expected_score) < 0.01, \
            f"Expected score {expected_score}, got {player1_score}"

        print(f"✅ Stats uploaded and scored: Player 1 scored {player1_score:.2f} points")

    def test_05_standings_calculation(self):
        """Test that standings are calculated correctly."""
        print("\n=== TEST 5: Calculating Standings ===")

        # Ensure previous tests ran
        if not draft_engine.validate_draft_complete():
            self.test_01_draft_complete_season()
            self.test_02_set_lineups_multiple_dates()
            self.test_04_upload_game_stats_and_calculate_scores()

        # Update standings
        standings_updater.update_standings()

        # Load standings
        standings = data_loader.load_standings()

        assert standings is not None and not standings.empty, "Standings should exist"
        assert len(standings) == NUM_MANAGERS, f"Should have {NUM_MANAGERS} teams in standings"

        # Verify standings have required columns
        required_cols = ['manager_id', 'total_points', 'rank']
        for col in required_cols:
            assert col in standings.columns, f"Standings missing column: {col}"

        # Verify ranks are 1 through NUM_MANAGERS
        ranks = sorted(standings['rank'].tolist())
        expected_ranks = list(range(1, NUM_MANAGERS + 1))
        assert ranks == expected_ranks, f"Ranks should be {expected_ranks}, got {ranks}"

        # Verify standings are sorted by total_points descending
        assert standings['total_points'].is_monotonic_decreasing or \
               standings['total_points'].nunique() == 1, \
               "Standings should be sorted by total_points descending"

        top_team = standings.iloc[0]
        print(f"✅ Standings calculated: Leader has {top_team['total_points']:.2f} points")

    def test_06_lineup_lock_functionality(self):
        """Test that lineup locking works correctly."""
        print("\n=== TEST 6: Testing Lineup Locks ===")

        # Test dates: one in past, one in future
        past_date = date.today() - timedelta(days=1)  # Yesterday (definitely in past)
        future_date = date(2026, 2, 15)  # Mid-season (in future)

        # Past date should be locked
        is_past_locked = lineup_manager.is_lineup_locked(past_date)
        assert is_past_locked, f"Past dates should be locked (checking {past_date} vs today {date.today()})"

        # Future date should not be locked
        is_future_locked = lineup_manager.is_lineup_locked(future_date)
        assert not is_future_locked, "Future dates should not be locked"

        print(f"✅ Lineup locks working: Past={is_past_locked}, Future={is_future_locked}")

    def test_07_tournament_nominations(self):
        """Test tournament player nominations."""
        print("\n=== TEST 7: Tournament Nominations ===")

        # Ensure draft complete
        if not draft_engine.validate_draft_complete():
            self.test_01_draft_complete_season()

        managers = data_loader.load_managers()

        # Each manager nominates their first player
        tournament_picks = []
        for manager_id in managers['manager_id']:
            roster = draft_engine.get_manager_roster(manager_id)
            nominated_player = roster.sort_values('player_id').iloc[0]['player_id']

            tournament_picks.append({
                'manager_id': manager_id,
                'player_id': nominated_player,
                'seed': 0  # Will be assigned later
            })

        picks_df = pd.DataFrame(tournament_picks)
        data_loader.save_tournament_picks(picks_df)

        # Verify tournament picks saved
        loaded_picks = data_loader.load_tournament_picks()
        assert loaded_picks is not None and not loaded_picks.empty, "Tournament picks should be saved"
        assert len(loaded_picks) == NUM_MANAGERS, f"Should have {NUM_MANAGERS} tournament picks"

        print(f"✅ Tournament nominations complete: {NUM_MANAGERS} players nominated")

    def test_08_validation_errors(self):
        """Test that validation catches errors correctly."""
        print("\n=== TEST 8: Testing Validation ===")

        # Ensure draft complete
        if not draft_engine.validate_draft_complete():
            self.test_01_draft_complete_season()

        manager_id = 1
        game_date = SEASON_START + timedelta(days=10)
        roster = draft_engine.get_manager_roster(manager_id)

        # Test 1: Too few players
        too_few = roster['player_id'].head(2).tolist()
        success, message = lineup_manager.save_lineup(manager_id, game_date, too_few)
        assert not success, "Should reject lineup with too few players"
        assert "exactly" in message.lower(), "Error message should mention exact count"

        # Test 2: Too many players
        too_many = roster['player_id'].head(5).tolist()
        success, message = lineup_manager.save_lineup(manager_id, game_date, too_many)
        assert not success, "Should reject lineup with too many players"

        # Test 3: Duplicate players
        valid_count = roster['player_id'].head(ACTIVE_PLAYERS_PER_DAY - 1).tolist()
        duplicates = valid_count + [valid_count[0]]  # Duplicate first player
        success, message = lineup_manager.save_lineup(manager_id, game_date, duplicates)
        assert not success, "Should reject lineup with duplicates"
        assert "duplicate" in message.lower(), "Error message should mention duplicates"

        # Test 4: Player not on roster
        all_players = data_loader.load_players()
        other_team_player = all_players[~all_players['player_id'].isin(roster['player_id'])].iloc[0]['player_id']
        invalid_roster = roster['player_id'].head(ACTIVE_PLAYERS_PER_DAY - 1).tolist() + [other_team_player]
        success, message = lineup_manager.save_lineup(manager_id, game_date, invalid_roster)
        assert not success, "Should reject player not on roster"
        assert "roster" in message.lower(), "Error message should mention roster"

        print("✅ All validation tests passed")

    def test_09_end_to_end_season(self):
        """Complete end-to-end test: Draft → Lineups → Stats → Scores → Standings."""
        print("\n=== TEST 9: Full Season Simulation ===")

        # 1. Run draft
        print("  1/5 Running draft...")
        self.test_01_draft_complete_season()

        # 2. Set lineups for 5 game dates
        print("  2/5 Setting lineups...")
        managers = data_loader.load_managers()
        game_dates = [SEASON_START + timedelta(days=i) for i in range(5)]

        for game_date in game_dates:
            for manager_id in managers['manager_id']:
                roster = draft_engine.get_manager_roster(manager_id)
                active_players = roster.sort_values('player_id')['player_id'].head(ACTIVE_PLAYERS_PER_DAY).tolist()
                lineup_manager.save_lineup(manager_id, game_date, active_players)

        # 3. Upload stats for each game date
        print("  3/5 Uploading game stats...")
        players = data_loader.load_players()

        for i, game_date in enumerate(game_dates):
            # Rotate which players get stats
            start_idx = (i * 6) % len(players)
            game_players = players.iloc[start_idx:start_idx + 6]['player_id'].tolist()

            # Create varied stats
            game_stats = []
            for j, player_id in enumerate(game_players):
                game_stats.append({
                    'game_id': i + 1,
                    'player_id': player_id,
                    '1PT_MADE': j,
                    '2PT_MADE': 5 + j,
                    'FT_MADE': 2,
                    'REB': 6 + j,
                    'AST': 3,
                    'STL': 1,
                    'BLK': 1,
                    'TOV': 1,
                    'PF': 2,
                    'GAME_WINNER': 1 if j == 0 else 0,
                    'DUNK': 1 if j % 2 == 0 else 0
                })

            stats_df = pd.DataFrame(game_stats)
            data_loader.save_game_stats(stats_df, game_date, game_num=i + 1)

        # 4. Calculate all scores
        print("  4/5 Calculating scores...")
        for game_date in game_dates:
            score_calculator.update_scores_for_date(game_date)

        # 5. Update standings
        print("  5/5 Updating standings...")
        standings_updater.update_standings()

        # Verify final state
        standings = data_loader.load_standings()
        assert len(standings) == NUM_MANAGERS, "Final standings should have all managers"

        # Display final standings
        print("\n📊 Final Standings:")
        standings_display = standings_updater.get_standings_with_details()
        for _, row in standings_display.iterrows():
            print(f"  {row['rank']}. {row['team_name']}: {row['total_points']:.2f} pts")

        print("\n✅ Complete season simulation successful!")


def test_config_constants():
    """Test that config constants are set correctly."""
    print("\n=== Testing Configuration ===")

    assert NUM_MANAGERS == 8, "Should have 8 managers"
    assert TOTAL_DRAFT_PICKS == 48, "Should have 48 total draft picks"
    assert PLAYERS_PER_MANAGER == 6, "Should have 6 players per manager"
    assert ACTIVE_PLAYERS_PER_DAY == 3, "Should have 3 active players per day"
    assert SEASON_START == date(2026, 1, 5), "Season should start Jan 5, 2026"

    print("✅ All config constants correct")


if __name__ == "__main__":
    # Run tests manually
    import traceback

    test_suite = TestSeasonSimulation()

    tests = [
        ("Config Constants", test_config_constants),
        ("Draft", test_suite.test_01_draft_complete_season),
        ("Lineups", test_suite.test_02_set_lineups_multiple_dates),
        ("Sticky Lineups", test_suite.test_03_sticky_lineup_functionality),
        ("Stats & Scoring", test_suite.test_04_upload_game_stats_and_calculate_scores),
        ("Standings", test_suite.test_05_standings_calculation),
        ("Lineup Locks", test_suite.test_06_lineup_lock_functionality),
        ("Tournament", test_suite.test_07_tournament_nominations),
        ("Validation", test_suite.test_08_validation_errors),
        ("Full Season", test_suite.test_09_end_to_end_season),
    ]

    print("=" * 60)
    print("UNRIVALED FANTASY LEAGUE - SEASON SIMULATION TESTS")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            # Setup
            test_suite.setup_teardown().__next__()

            # Run test
            test_func()
            passed += 1

        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name} FAILED:")
            print(f"   {str(e)}")
            traceback.print_exc()

        finally:
            # Teardown
            try:
                test_suite.setup_teardown().__next__()
            except StopIteration:
                pass

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
