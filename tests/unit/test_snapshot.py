import unittest
from pathlib import Path
import tempfile
import shutil
import time

from storage.snapshot import SnapshotManager

class TestSnapshotManager(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for snapshots."""
        self.test_dir = tempfile.mkdtemp()
        self.snapshot_dir = Path(self.test_dir)
        self.manager = SnapshotManager(self.snapshot_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_create_and_restore_snapshot(self):
        """Tests creating a snapshot and restoring it successfully."""
        state = {"key": "value", "number": 123}

        snapshot_id = self.manager.create_snapshot(state)
        self.assertIsNotNone(snapshot_id)

        restored_state = self.manager.restore_snapshot(snapshot_id)
        self.assertEqual(restored_state, state)

    def test_restore_non_existent(self):
        """Tests that restoring a non-existent snapshot returns None."""
        self.assertIsNone(self.manager.restore_snapshot("non-existent-id"))

    def test_restore_corrupted_snapshot(self):
        """Tests that restoring a corrupted snapshot returns None."""
        state = {"key": "value"}
        snapshot_id = self.manager.create_snapshot(state)

        # Corrupt the file by overwriting it with garbage
        snapshot_path = self.snapshot_dir / f"{snapshot_id}.snapshot"
        with snapshot_path.open("w") as f:
            f.write("this is not valid json and has no checksum")

        restored_state = self.manager.restore_snapshot(snapshot_id)
        self.assertIsNone(restored_state)

    def test_get_and_restore_latest_snapshot(self):
        """Tests getting and restoring the latest snapshot."""
        state1 = {"version": 1}
        state2 = {"version": 2}

        # No snapshots exist initially
        self.assertIsNone(self.manager.get_latest_snapshot_id())
        id, state = self.manager.restore_latest_snapshot()
        self.assertIsNone(id)
        self.assertIsNone(state)

        # Create two snapshots
        id1 = self.manager.create_snapshot(state1)
        time.sleep(0.01) # Ensure timestamps are different
        id2 = self.manager.create_snapshot(state2)

        # The latest ID should be the second one
        self.assertEqual(self.manager.get_latest_snapshot_id(), id2)

        # Restore the latest and check its content
        latest_id, latest_state = self.manager.restore_latest_snapshot()
        self.assertEqual(latest_id, id2)
        self.assertEqual(latest_state, state2)

if __name__ == '__main__':
    unittest.main()
