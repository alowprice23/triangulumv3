import zlib

def crc32(data: bytes) -> int:
    """
    Calculates the CRC32 checksum for the given data.
    """
    return zlib.crc32(data)

def verify_crc32(data: bytes, checksum: int) -> bool:
    """
    Verifies the CRC32 checksum for the given data.
    """
    return crc32(data) == checksum
