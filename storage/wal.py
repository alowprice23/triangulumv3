import json
import struct
import logging
from enum import Enum
from pathlib import Path
from typing import Generator, Dict, Any

from storage.crc import crc32, verify_crc32

logger = logging.getLogger(__name__)

class LogEntryType(str, Enum):
    """Defines the types of events that can be logged."""
    BUG_SUBMITTED = "BUG_SUBMITTED"
    SESSION_LAUNCHED = "SESSION_LAUNCHED"
    SESSION_COMPLETED = "SESSION_COMPLETED"

class WriteAheadLog:
    """
    A simple write-ahead log (WAL) implementation that stores structured,
    JSON-serialized events.
    Each log entry is stored with a length, checksum, and the JSON data.
    Format: [length (4 bytes)][checksum (4 bytes)][data (length bytes)]
    """
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self._log_file = self.log_path.open("ab")

    def log_event(self, entry_type: LogEntryType, payload: Dict[str, Any]):
        """
        Serializes and appends a new structured event to the log.
        """
        event = {
            "type": entry_type.value,
            "timestamp_ns": time.time_ns(),
            "payload": payload,
        }
        data = json.dumps(event).encode("utf-8")
        self._append_raw(data)

    def _append_raw(self, data: bytes):
        """Appends raw bytes to the log with header and checksum."""
        checksum = crc32(data)
        length = len(data)
        header = struct.pack("!II", length, checksum)
        self._log_file.write(header + data)
        self._log_file.flush()

    def read_events(self) -> Generator[Dict[str, Any], None, None]:
        """Reads, deserializes, and yields all valid log events."""
        self.close() # Ensure buffer is flushed before reading
        with self.log_path.open("rb") as f:
            while True:
                header_data = f.read(8)
                if not header_data:
                    break
                if len(header_data) < 8:
                    logger.warning(f"Log file corrupted. Invalid header size.")
                    break

                length, checksum = struct.unpack("!II", header_data)
                data = f.read(length)

                if len(data) < length:
                    logger.warning(f"Log file corrupted. Incomplete data for entry.")
                    break

                if verify_crc32(data, checksum):
                    event = json.loads(data.decode("utf-8"))
                    yield event
                else:
                    logger.warning(f"Log file corrupted. Checksum mismatch.")
                    break
        self._log_file = self.log_path.open("ab") # Reopen for appending

    def clear(self):
        """Clears the log file. Useful for testing."""
        self.close()
        if self.log_path.exists():
            self.log_path.unlink()
        self._log_file = self.log_path.open("ab")

    def close(self):
        """Closes the log file."""
        if self._log_file and not self._log_file.closed:
            self._log_file.close()

    def __del__(self):
        self.close()
