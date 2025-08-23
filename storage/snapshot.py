import json
import struct
import time
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from storage.crc import crc32, verify_crc32

logger = logging.getLogger(__name__)

class SnapshotManager:
    """
    Manages creating and restoring snapshots of the system's state using
    JSON serialization and CRC32 checksums for integrity.

    Snapshot format: [checksum (4 bytes)][utf-8 encoded json data]
    """
    def __init__(self, snapshot_dir: Path):
        self.snapshot_dir = snapshot_dir
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, state: Dict[str, Any]) -> str:
        """
        Creates a new snapshot of the given state, using a nanosecond timestamp
        as the snapshot ID.

        Returns:
            The ID of the created snapshot.
        """
        snapshot_id = str(time.time_ns())
        snapshot_path = self.snapshot_dir / f"{snapshot_id}.snapshot"

        data = json.dumps(state).encode("utf-8")
        checksum = crc32(data)
        header = struct.pack("!I", checksum)

        with snapshot_path.open("wb") as f:
            f.write(header)
            f.write(data)

        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        Restores a snapshot with the given ID, verifying its checksum.

        Returns:
            The restored state dict, or None if the snapshot does not exist
            or is corrupt.
        """
        snapshot_path = self.snapshot_dir / f"{snapshot_id}.snapshot"
        if not snapshot_path.is_file():
            return None

        with snapshot_path.open("rb") as f:
            header = f.read(4)
            if len(header) < 4:
                logger.warning(f"Snapshot {snapshot_id} is corrupt (invalid header).")
                return None

            checksum = struct.unpack("!I", header)[0]
            data = f.read()

            if verify_crc32(data, checksum):
                return json.loads(data.decode("utf-8"))
            else:
                logger.warning(f"Snapshot {snapshot_id} is corrupt (checksum mismatch).")
                return None

    def get_latest_snapshot_id(self) -> Optional[str]:
        """
        Finds the ID of the most recent snapshot file based on filename.
        """
        snapshots = list(self.snapshot_dir.glob("*.snapshot"))
        if not snapshots:
            return None

        # Assuming snapshot IDs are numeric timestamps, so we can sort them
        try:
            latest_snapshot = max(snapshots, key=lambda p: int(p.stem))
            return latest_snapshot.stem
        except (ValueError, TypeError):
            return None # Handle cases with invalid filenames

    def restore_latest_snapshot(self) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Finds and restores the latest valid snapshot.

        Returns:
            A tuple of (snapshot_id, state), or (None, None) if no valid
            snapshot is found.
        """
        latest_id = self.get_latest_snapshot_id()
        if not latest_id:
            return None, None

        state = self.restore_snapshot(latest_id)
        if state is not None:
            return latest_id, state

        # If the latest is corrupt, we could try older ones, but for now, we'll fail.
        return None, None
