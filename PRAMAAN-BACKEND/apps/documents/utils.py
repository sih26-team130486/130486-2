"""
documents/utils.py — SHA-256 hashing utility
"""
import hashlib


def compute_sha256(file_obj) -> str:
    """
    Compute SHA-256 hash of a file object.
    Reads in 8 KB chunks to handle large files efficiently.
    Returns uppercase hex string (64 chars).
    """
    hasher = hashlib.sha256()
    file_obj.seek(0)  # Always start from beginning
    for chunk in iter(lambda: file_obj.read(8192), b''):
        hasher.update(chunk)
    file_obj.seek(0)  # Reset after reading
    return hasher.hexdigest().upper()


def compute_sha256_from_path(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file on disk.
    Used during verification to re-hash the stored file.
    """
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest().upper()
