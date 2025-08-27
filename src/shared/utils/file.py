"""File manipulation utilities."""

from pathlib import Path


def get_file_extension(file_path: str | Path) -> str:
    """Get file extension from path."""
    return Path(file_path).suffix.lower()


def is_binary_file(file_path: str | Path) -> bool:
    """Check if file is likely binary based on extension."""
    binary_extensions = {
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".bin",
        ".obj",
        ".o",
        ".a",
        ".lib",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".ico",
        ".svg",
        ".tiff",
        ".mp3",
        ".mp4",
        ".avi",
        ".mov",
        ".wav",
        ".flac",
        ".ogg",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".zip",
        ".tar",
        ".gz",
        ".bz2",
        ".7z",
        ".rar",
        ".sqlite",
        ".db",
        ".mdb",
    }
    return get_file_extension(file_path) in binary_extensions
