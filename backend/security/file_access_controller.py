"""
File Access Control & Security
Prevents sandboxed AI from accessing sensitive files or writing outside allowed directories.
Guards against path traversal and shell injection.
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Characters/patterns that could be used for shell injection.
# Backslash is intentionally excluded here because it is a valid Windows path
# separator; path traversal (including Windows-style ..\) is caught separately.
_SHELL_INJECTION_PATTERN = re.compile(
    r"[;&|`$<>]|(%2e%2e)|(%2f)|(\x00)",
    re.IGNORECASE,
)


class SecurityError(Exception):
    """Raised when file access is denied"""
    pass


class FileAccessController:
    """
    Controls file read/write access for safety.

    Rules:
    1. Write only to ALLOWED_OUTPUT_DIR
    2. Cannot read credential files (.env, *.key, *.secret, …)
    3. Cannot write to system directories
    4. Prevents path traversal attacks (../ sequences)
    5. Prevents shell injection in file paths
    """

    def __init__(self, allowed_output_dir: str = "outputs/"):
        """
        Initialize controller.

        Args:
            allowed_output_dir: Directory where writes are allowed
        """
        self.allowed_output_dir = Path(allowed_output_dir).resolve()
        self.allowed_output_dir.mkdir(parents=True, exist_ok=True)

        # Sensitive files that cannot be read
        self.sensitive_patterns = [
            ".env",
            ".key",
            ".secret",
            "credentials",
            "apikey",
            "api_key",
            "password",
            ".pem",
            ".p12",
            "config.ini",
            "secrets.json",
        ]

        logger.info(f"FileAccessController initialized. Allowed output: {self.allowed_output_dir}")

    # ------------------------------------------------------------------
    # Security helpers
    # ------------------------------------------------------------------

    def _check_shell_injection(self, path: str) -> Tuple[bool, str]:
        """Return (safe, reason). safe=False means injection detected."""
        if _SHELL_INJECTION_PATTERN.search(path):
            return False, f"Shell injection characters detected in path: {path!r}"
        return True, "ok"

    def _check_path_traversal(self, path: str) -> Tuple[bool, str]:
        """Return (safe, reason). safe=False means traversal detected."""
        # Detect raw ../  or ..\  (both Unix and Windows styles)
        if ".." in Path(path).parts:
            return False, f"Path traversal detected in: {path!r}"
        # URL-encoded variants (%2e%2e)
        if re.search(r"%2e%2e", path, re.IGNORECASE):
            return False, f"Encoded path traversal detected in: {path!r}"
        return True, "ok"

    # ------------------------------------------------------------------
    # Core access checks
    # ------------------------------------------------------------------

    def is_write_allowed(self, file_path: str) -> Tuple[bool, str]:
        """
        Check if write to file_path is allowed.

        Args:
            file_path: Path to write to

        Returns:
            (allowed: bool, reason: str)
        """
        try:
            safe, reason = self._check_shell_injection(file_path)
            if not safe:
                return False, reason

            safe, reason = self._check_path_traversal(file_path)
            if not safe:
                return False, reason

            target_path = Path(file_path).resolve()

            # Check if path is within allowed directory
            try:
                target_path.relative_to(self.allowed_output_dir)
            except ValueError:
                return False, f"Write outside allowed directory: {self.allowed_output_dir}"

            # Check for system directories (absolute path check)
            system_roots = {"/etc", "/sys", "/proc", "/dev", "/bin", "/sbin", "/boot"}
            for root in system_roots:
                if str(target_path).startswith(root):
                    return False, f"Cannot write to system directory: {root}"

            return True, "Write allowed"

        except Exception as e:
            return False, f"Error checking write access: {e}"

    def is_read_allowed(self, file_path: str) -> Tuple[bool, str]:
        """
        Check if read from file_path is allowed.

        Args:
            file_path: Path to read from

        Returns:
            (allowed: bool, reason: str)
        """
        try:
            safe, reason = self._check_shell_injection(file_path)
            if not safe:
                return False, reason

            safe, reason = self._check_path_traversal(file_path)
            if not safe:
                return False, reason

            file_name = Path(file_path).name.lower()

            # Check against sensitive patterns
            for pattern in self.sensitive_patterns:
                if pattern.lower() in file_name:
                    return False, f"Cannot read sensitive file: {file_name}"

            # Check if file exists
            if not Path(file_path).exists():
                return False, f"File does not exist: {file_path}"

            return True, "Read allowed"

        except Exception as e:
            return False, f"Error checking read access: {e}"

    def validate_output_path(self, file_path: str) -> str:
        """
        Validate and return safe output path.

        Args:
            file_path: Requested file path

        Returns:
            Safe absolute path within allowed directory

        Raises:
            SecurityError: If path is invalid
        """
        allowed, reason = self.is_write_allowed(file_path)

        if not allowed:
            raise SecurityError(f"Invalid output path: {reason}")

        return str(Path(file_path).resolve())

    # ------------------------------------------------------------------
    # Report helpers
    # ------------------------------------------------------------------

    def write_report(self, filename: str, data: dict, intent: Optional[object] = None) -> str:
        """
        Write a JSON report to the allowed output directory.

        Args:
            filename: Base filename (e.g. "trade_report.json"). Must not
                      contain path separators.
            data: Dictionary to serialise as JSON.
            intent: Optional Intent model object; its dict representation
                    is merged into the report when provided.

        Returns:
            Absolute path of the written file.

        Raises:
            SecurityError: If the path is not allowed.
        """
        # Only allow plain filenames – no directory components
        if os.sep in filename or "/" in filename:
            raise SecurityError(f"Filename must not contain path separators: {filename!r}")

        target_path = self.allowed_output_dir / filename
        allowed, reason = self.is_write_allowed(str(target_path))
        if not allowed:
            raise SecurityError(f"Cannot write report: {reason}")

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }

        if intent is not None:
            # Support both dataclass/pydantic models (with .dict()/.model_dump())
            # and plain dicts.
            if hasattr(intent, "model_dump"):
                report["intent"] = intent.model_dump()
            elif hasattr(intent, "dict"):
                report["intent"] = intent.dict()
            elif isinstance(intent, dict):
                report["intent"] = intent

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)

        logger.info(f"Report written: {target_path}")
        return str(target_path)

    def read_report(self, filename: str) -> dict:
        """
        Read a JSON report from the allowed output directory.

        Args:
            filename: Base filename (e.g. "trade_report.json").

        Returns:
            Parsed dict from the JSON file.

        Raises:
            SecurityError: If read is not permitted.
            FileNotFoundError: If the file does not exist.
        """
        if os.sep in filename or "/" in filename:
            raise SecurityError(f"Filename must not contain path separators: {filename!r}")

        target_path = self.allowed_output_dir / filename
        allowed, reason = self.is_read_allowed(str(target_path))
        if not allowed:
            raise SecurityError(f"Cannot read report: {reason}")

        with open(target_path, "r", encoding="utf-8") as fh:
            return json.load(fh)


# Global instance
_controller: Optional[FileAccessController] = None


def get_file_access_controller(allowed_output_dir: str = "outputs/") -> FileAccessController:
    """Get or create global FileAccessController instance"""
    global _controller
    if _controller is None:
        _controller = FileAccessController(allowed_output_dir)
    return _controller