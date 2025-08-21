import pytest
from storage.crc import crc32, verify_crc32

def test_crc32():
    """Tests the crc32 function with sample data."""
    data = b"hello world"
    checksum = crc32(data)
    assert isinstance(checksum, int)

def test_verify_crc32_correct():
    """Tests verify_crc32 with a correct checksum."""
    data = b"hello world"
    checksum = crc32(data)
    assert verify_crc32(data, checksum)

def test_verify_crc32_incorrect():
    """Tests verify_crc32 with an incorrect checksum."""
    data = b"hello world"
    checksum = crc32(data)
    assert not verify_crc32(data, checksum + 1)

def test_verify_crc32_different_data():
    """Tests verify_crc32 with different data."""
    data1 = b"hello world"
    data2 = b"hello world!"
    checksum1 = crc32(data1)
    assert not verify_crc32(data2, checksum1)
