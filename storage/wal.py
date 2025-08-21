from pathlib import Path
from typing import List, Generator
from storage.crc import crc32, verify_crc32
import struct

class WriteAheadLog:
    """
    A simple write-ahead log (WAL) implementation.
    Each log entry is stored with a length, checksum, and data.
    Format: [length (4 bytes)][checksum (4 bytes)][data (length bytes)]
    """
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_file = open(log_path, "ab")

    def append(self, data: bytes):
        """Appends a new entry to the log."""
        checksum = crc32(data)
        length = len(data)
        header = struct.pack("!II", length, checksum)
        self.log_file.write(header + data)
        self.log_file.flush()

    def read_log(self) -> Generator[bytes, None, None]:
        """Reads and yields all valid log entries."""
        with open(self.log_path, "rb") as f:
            while True:
                header_data = f.read(8)
                if len(header_data) < 8:
                    # Not enough data for a header, assume end of file or corruption
                    break

                length, checksum = struct.unpack("!II", header_data)
                data = f.read(length)

                if len(data) < length:
                    # Not enough data for the entry, assume corruption
                    break

                if verify_crc32(data, checksum):
                    yield data
                else:
                    # Log corruption detected.
                    # In a real implementation, we would handle this,
                    # e.g., by truncating the log or reporting an error.
                    break

    def close(self):
        """Closes the log file."""
        self.log_file.close()
