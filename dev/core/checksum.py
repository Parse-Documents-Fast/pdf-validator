import hashlib


def calculate_checksum(content: bytes) -> str:
    """Calculate the SHA-256 checksum of the given bytes."""
    return hashlib.sha256(content).hexdigest()
