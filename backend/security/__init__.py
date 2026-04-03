"""
backend.security - File access control and security utilities
"""

from backend.security.file_access_controller import (
    FileAccessController,
    SecurityError,
    get_file_access_controller,
)

__all__ = [
    "FileAccessController",
    "SecurityError",
    "get_file_access_controller",
]
