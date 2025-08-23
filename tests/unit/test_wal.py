import unittest
from pathlib import Path
import tempfile
import shutil

from storage.wal import WriteAheadLog, LogEntryType

class TestWriteAheadLog(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for the WAL file."""
        self.test_dir = tempfile.mkdtemp()
        self.wal_path = Path(self.test_dir) / "test.wal"
        self.wal = WriteAheadLog(self.wal_path)

    def tearDown(self):
        """Clean up the temporary directory."""
        self.wal.close()
        shutil.rmtree(self.test_dir)

    def test_log_and_read_events(self):
        """Tests logging structured events and reading them back."""
        event1 = {"bug_id": "123", "description": "first bug"}
        event2 = {"bug_id": "456", "status": "success"}

        self.wal.log_event(LogEntryType.BUG_SUBMITTED, event1)
        self.wal.log_event(LogEntryType.SESSION_COMPLETED, event2)

        # Re-reading should yield the events back
        events = list(self.wal.read_events())

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["type"], LogEntryType.BUG_SUBMITTED.value)
        self.assertEqual(events[0]["payload"], event1)
        self.assertEqual(events[1]["type"], LogEntryType.SESSION_COMPLETED.value)
        self.assertEqual(events[1]["payload"], event2)

    def test_read_empty_log(self):
        """Tests reading from an empty WAL."""
        events = list(self.wal.read_events())
        self.assertFalse(events)

    def test_handle_corrupted_log(self):
        """Tests that the WAL reader stops at a corrupted entry."""
        event1 = {"bug_id": "123"}
        self.wal.log_event(LogEntryType.BUG_SUBMITTED, event1)

        # Manually append garbage to the file
        with self.wal_path.open("ab") as f:
            f.write(b"this is garbage data")

        event2 = {"bug_id": "456"}
        self.wal.log_event(LogEntryType.BUG_SUBMITTED, event2)

        # Only the first, valid event should be read
        events = list(self.wal.read_events())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["payload"], event1)

    def test_clear_log(self):
        """Tests the clear method."""
        event1 = {"bug_id": "123"}
        self.wal.log_event(LogEntryType.BUG_SUBMITTED, event1)
        self.assertTrue(self.wal_path.exists())
        self.assertGreater(self.wal_path.stat().st_size, 0)

        self.wal.clear()

        self.assertTrue(self.wal_path.exists())
        self.assertEqual(self.wal_path.stat().st_size, 0)

        # Ensure we can still write to the log after clearing
        event2 = {"bug_id": "456"}
        self.wal.log_event(LogEntryType.BUG_SUBMITTED, event2)
        self.assertGreater(self.wal_path.stat().st_size, 0)
        events = list(self.wal.read_events())
        self.assertEqual(len(events), 1)

if __name__ == '__main__':
    unittest.main()
