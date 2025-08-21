import pytest
from pathlib import Path
from storage.snapshot import SnapshotManager
import time

@pytest.fixture
def snapshot_dir(tmp_path):
    d = tmp_path / "snapshots"
    d.mkdir()
    return d

def test_snapshot_create_and_restore(snapshot_dir):
    """Tests creating and restoring a snapshot."""
    snapshot_manager = SnapshotManager(snapshot_dir)
    state = {"key": "value", "number": 123}
    snapshot_id = "snap1"

    snapshot_manager.create_snapshot(state, snapshot_id)
    restored_state = snapshot_manager.restore_snapshot(snapshot_id)

    assert restored_state == state

def test_snapshot_restore_non_existent(snapshot_dir):
    """Tests restoring a non-existent snapshot."""
    snapshot_manager = SnapshotManager(snapshot_dir)
    assert snapshot_manager.restore_snapshot("non-existent") is None

def test_snapshot_get_latest(snapshot_dir):
    """Tests getting the latest snapshot ID."""
    snapshot_manager = SnapshotManager(snapshot_dir)

    assert snapshot_manager.get_latest_snapshot_id() is None

    snapshot_manager.create_snapshot({"a": 1}, "snap1")
    time.sleep(0.01)
    snapshot_manager.create_snapshot({"b": 2}, "snap2")

    assert snapshot_manager.get_latest_snapshot_id() == "snap2"
