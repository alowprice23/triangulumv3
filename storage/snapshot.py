from pathlib import Path
import pickle

class SnapshotManager:
    """
    Manages creating and restoring snapshots of the system's state.
    """
    def __init__(self, snapshot_dir: Path):
        self.snapshot_dir = snapshot_dir
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, state: dict, snapshot_id: str):
        """
        Creates a new snapshot of the given state.
        The state is serialized using pickle.
        """
        snapshot_path = self.snapshot_dir / f"{snapshot_id}.snapshot"
        with open(snapshot_path, "wb") as f:
            pickle.dump(state, f)

    def restore_snapshot(self, snapshot_id: str) -> dict | None:
        """
        Restores a snapshot with the given ID.
        Returns the restored state, or None if the snapshot does not exist.
        """
        snapshot_path = self.snapshot_dir / f"{snapshot_id}.snapshot"
        if not snapshot_path.is_file():
            return None

        with open(snapshot_path, "rb") as f:
            return pickle.load(f)

    def get_latest_snapshot_id(self) -> str | None:
        """
        Returns the ID of the latest snapshot.
        """
        snapshots = list(self.snapshot_dir.glob("*.snapshot"))
        if not snapshots:
            return None

        latest_snapshot = max(snapshots, key=lambda p: p.stat().st_mtime)
        return latest_snapshot.stem
