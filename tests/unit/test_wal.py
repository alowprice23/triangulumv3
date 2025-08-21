import pytest
from pathlib import Path
from storage.wal import WriteAheadLog
import struct

@pytest.fixture
def wal_path(tmp_path):
    return tmp_path / "test.wal"

def test_wal_append_and_read(wal_path):
    """Tests appending to and reading from the WAL."""
    wal = WriteAheadLog(wal_path)
    data1 = b"first entry"
    data2 = b"second entry"

    wal.append(data1)
    wal.append(data2)
    wal.close()

    wal_reader = WriteAheadLog(wal_path)
    entries = list(wal_reader.read_log())
    wal_reader.close()

    assert len(entries) == 2
    assert entries[0] == data1
    assert entries[1] == data2

def test_wal_empty_log(wal_path):
    """Tests reading from an empty WAL."""
    wal = WriteAheadLog(wal_path)
    entries = list(wal.read_log())
    wal.close()
    assert not entries

def test_wal_corrupted_log(wal_path):
    """Tests reading from a corrupted WAL."""
    wal = WriteAheadLog(wal_path)
    data = b"good entry"
    wal.append(data)

    # Corrupt the log by writing some garbage
    with open(wal_path, "ab") as f:
        f.write(b"garbage")

    wal.close()

    wal_reader = WriteAheadLog(wal_path)
    entries = list(wal_reader.read_log())
    wal_reader.close()

    # Should only read the valid entry
    assert len(entries) == 1
    assert entries[0] == data
