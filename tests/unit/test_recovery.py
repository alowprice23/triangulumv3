import unittest
from unittest.mock import MagicMock

from storage.recovery import RecoveryManager
from storage.wal import WriteAheadLog, LogEntryType
from storage.snapshot import SnapshotManager

class TestRecoveryManager(unittest.TestCase):

    def setUp(self):
        """Set up mock storage components for each test."""
        self.mock_wal = MagicMock(spec=WriteAheadLog)
        self.mock_snapshot_manager = MagicMock(spec=SnapshotManager)
        self.recovery_manager = RecoveryManager(self.mock_wal, self.mock_snapshot_manager)

    def test_recover_from_nothing(self):
        """Test recovery when no snapshot or WAL entries exist."""
        self.mock_snapshot_manager.restore_latest_snapshot.return_value = (None, None)
        self.mock_wal.read_events.return_value = []
        state = self.recovery_manager.recover_state()
        self.assertEqual(state, {"scheduler_tickets": [], "active_sessions": {}})

    def test_recover_from_snapshot_only(self):
        """Test recovery with a snapshot but no new WAL entries."""
        snapshot_id = "1000"
        snapshot_state = {"scheduler_tickets": [{"bug_id": "bug900"}], "active_sessions": {}}
        self.mock_snapshot_manager.restore_latest_snapshot.return_value = (snapshot_id, snapshot_state)
        # This event should be ignored because its timestamp is less than the snapshot_id
        self.mock_wal.read_events.return_value = [{"type": "DUMMY", "timestamp_ns": 500, "payload": {}}]
        state = self.recovery_manager.recover_state()
        self.assertEqual(state, snapshot_state)

    def test_recover_from_wal_only(self):
        """Test recovery with only WAL entries and no snapshot."""
        self.mock_snapshot_manager.restore_latest_snapshot.return_value = (None, None)
        event1 = {"type": LogEntryType.BUG_SUBMITTED, "timestamp_ns": 100, "payload": {"bug_id": "bug123"}}
        event2 = {"type": LogEntryType.BUG_SUBMITTED, "timestamp_ns": 200, "payload": {"bug_id": "bug456"}}
        self.mock_wal.read_events.return_value = [event1, event2]
        state = self.recovery_manager.recover_state()
        expected_state = {"scheduler_tickets": [event1["payload"], event2["payload"]], "active_sessions": {}}
        self.assertEqual(state, expected_state)

    def test_full_recovery_snapshot_and_wal(self):
        """Test recovery combining a snapshot with subsequent WAL entries."""
        snapshot_id = "1000" # This corresponds to the last_event_timestamp
        snapshot_state = {"scheduler_tickets": [{"bug_id": "bug900"}], "active_sessions": {}}
        self.mock_snapshot_manager.restore_latest_snapshot.return_value = (snapshot_id, snapshot_state)

        events = [
            {"type": LogEntryType.BUG_SUBMITTED, "timestamp_ns": 500, "payload": {"bug_id": "bug500"}},      # Ignored (ts < snapshot_id)
            {"type": LogEntryType.BUG_SUBMITTED, "timestamp_ns": 1100, "payload": {"bug_id": "bug1100"}},     # Applied
            {"type": LogEntryType.SESSION_LAUNCHED, "timestamp_ns": 900, "payload": {"bug_id": "bug900"}},    # Ignored (ts < snapshot_id)
            {"type": LogEntryType.SESSION_COMPLETED, "timestamp_ns": 1200, "payload": {"bug_id": "bug1100"}}, # Applied
        ]
        self.mock_wal.read_events.return_value = events
        state = self.recovery_manager.recover_state()

        # Expected state trace:
        # 1. Start with snapshot: tickets=[{bug_id:"bug900"}], active={}
        # 2. Replay WAL (events with ts > 1000):
        #    - apply BUG_SUBMITTED for "bug1100": tickets=[{...}, {bug_id:"bug1100"}], active={}
        #    - apply SESSION_COMPLETED for "bug1100": tickets=[{bug_id:"bug900"}], active={}
        # Final state should just have the original ticket from the snapshot.
        final_tickets = state["scheduler_tickets"]
        final_sessions = state["active_sessions"]

        self.assertEqual(len(final_tickets), 1)
        self.assertEqual(len(final_sessions), 0)
        self.assertEqual(final_tickets[0]["bug_id"], "bug900")

if __name__ == '__main__':
    unittest.main()
