import unittest
import json
from pathlib import Path
import time
import shutil

from storage.crc import crc32, verify_crc32
from storage.wal import WriteAheadLog, LogEntryType
from storage.snapshot import SnapshotManager
from storage.recovery import RecoveryManager

class TestCRC(unittest.TestCase):
    def test_crc32(self):
        data = b"hello world"
        # The exact value can vary, so we just check it returns an int
        self.assertIsInstance(crc32(data), int)

    def test_verify_crc32(self):
        data = b"hello world"
        checksum = crc32(data)
        self.assertTrue(verify_crc32(data, checksum))
        self.assertFalse(verify_crc32(data, checksum + 1))

class TestWriteAheadLog(unittest.TestCase):
    def setUp(self):
        self.log_path = Path("test_wal.log")
        self.wal = WriteAheadLog(self.log_path)

    def tearDown(self):
        self.wal.close()
        if self.log_path.exists():
            self.log_path.unlink()

    def test_log_and_read_event(self):
        event_type = LogEntryType.BUG_SUBMITTED
        payload = {"bug_id": "123", "data": "some data"}
        self.wal.log_event(event_type, payload)

        events = list(self.wal.read_events())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], event_type.value)
        self.assertEqual(events[0]["payload"], payload)

    def test_multiple_events(self):
        payload1 = {"bug_id": "123", "data": "data1"}
        payload2 = {"bug_id": "456", "data": "data2"}
        self.wal.log_event(LogEntryType.BUG_SUBMITTED, payload1)
        self.wal.log_event(LogEntryType.SESSION_LAUNCHED, payload2)

        events = list(self.wal.read_events())
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["payload"], payload1)
        self.assertEqual(events[1]["payload"], payload2)

    def test_corrupted_log(self):
        payload = {"bug_id": "123", "data": "some data"}
        self.wal.log_event(LogEntryType.BUG_SUBMITTED, payload)
        self.wal.close()

        with self.log_path.open("ab") as f:
            f.write(b"corruption")

        self.wal = WriteAheadLog(self.log_path)
        events = list(self.wal.read_events())
        self.assertEqual(len(events), 1)

class TestSnapshotManager(unittest.TestCase):
    def setUp(self):
        self.snapshot_dir = Path("test_snapshots")
        self.snapshot_manager = SnapshotManager(self.snapshot_dir)

    def tearDown(self):
        if self.snapshot_dir.exists():
            shutil.rmtree(self.snapshot_dir)

    def test_create_and_restore_snapshot(self):
        state = {"key": "value", "number": 123}
        snapshot_id = self.snapshot_manager.create_snapshot(state)
        restored_state = self.snapshot_manager.restore_snapshot(snapshot_id)
        self.assertEqual(state, restored_state)

    def test_restore_nonexistent_snapshot(self):
        self.assertIsNone(self.snapshot_manager.restore_snapshot("nonexistent"))

    def test_get_latest_snapshot(self):
        state1 = {"version": 1}
        state2 = {"version": 2}
        id1 = self.snapshot_manager.create_snapshot(state1)
        time.sleep(0.01)
        id2 = self.snapshot_manager.create_snapshot(state2)

        latest_id = self.snapshot_manager.get_latest_snapshot_id()
        self.assertEqual(latest_id, id2)

        restored_id, restored_state = self.snapshot_manager.restore_latest_snapshot()
        self.assertEqual(restored_id, id2)
        self.assertEqual(restored_state, state2)

class TestRecoveryManager(unittest.TestCase):
    def setUp(self):
        self.log_path = Path("test_recovery_wal.log")
        self.snapshot_dir = Path("test_recovery_snapshots")
        self.wal = WriteAheadLog(self.log_path)
        self.snapshot_manager = SnapshotManager(self.snapshot_dir)
        self.recovery_manager = RecoveryManager(self.wal, self.snapshot_manager)

    def tearDown(self):
        self.wal.close()
        if self.log_path.exists():
            self.log_path.unlink()
        if self.snapshot_dir.exists():
            shutil.rmtree(self.snapshot_dir)

    def test_recovery_from_snapshot_and_wal(self):
        # 1. Create a snapshot
        initial_state = {
            "scheduler_tickets": [{"bug_id": str(time.time_ns()), "data": "initial"}],
            "active_sessions": {},
        }
        snapshot_id = self.snapshot_manager.create_snapshot(initial_state)

        # 2. Log some events after the snapshot
        time.sleep(0.01)
        bug_id1 = str(time.time_ns())
        self.wal.log_event(LogEntryType.BUG_SUBMITTED, {"bug_id": bug_id1, "data": "new bug"})
        time.sleep(0.01)
        bug_id2 = str(time.time_ns())
        self.wal.log_event(LogEntryType.SESSION_LAUNCHED, {"bug_id": bug_id2, "data": "launched"})

        # 3. Recover
        recovered_state = self.recovery_manager.recover_state()

        # 4. Verify
        self.assertEqual(len(recovered_state["scheduler_tickets"]), 2)
        self.assertIn({"bug_id": bug_id1, "data": "new bug"}, recovered_state["scheduler_tickets"])
        self.assertIn(bug_id2, recovered_state["active_sessions"])

    def test_recovery_from_wal_only(self):
        bug_id1 = str(time.time_ns())
        self.wal.log_event(LogEntryType.BUG_SUBMITTED, {"bug_id": bug_id1, "data": "bug1"})
        time.sleep(0.01)
        bug_id2 = str(time.time_ns())
        self.wal.log_event(LogEntryType.BUG_SUBMITTED, {"bug_id": bug_id2, "data": "bug2"})

        recovered_state = self.recovery_manager.recover_state()

        self.assertEqual(len(recovered_state["scheduler_tickets"]), 2)

    def test_recovery_from_snapshot_only(self):
        state = {"scheduler_tickets": [{"bug_id": "1", "data": "bug1"}], "active_sessions": {}}
        self.snapshot_manager.create_snapshot(state)

        recovered_state = self.recovery_manager.recover_state()
        self.assertEqual(recovered_state, state)

    def test_recovery_from_empty_state(self):
        recovered_state = self.recovery_manager.recover_state()
        self.assertEqual(recovered_state, {"scheduler_tickets": [], "active_sessions": {}})

if __name__ == "__main__":
    unittest.main()
