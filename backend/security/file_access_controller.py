"""
File Access Control & Security
Prevents sandboxed AI from accessing sensitive files or writing outside allowed directories
"""

import os
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when file access is denied"""
    pass


class FileAccessController:
    """
    Controls file read/write access for safety.
    
    Rules:
    1. Write only to ALLOWED_OUTPUT_DIR
    2. Cannot read credential files (.env, *.key, *.secret)
    3. Cannot write to system directories
    """
    
    def __init__(self, allowed_output_dir: str = "outputs/"):
        """
        Initialize controller.
        
        Args:
            allowed_output_dir: Directory where writes are allowed
        """
        self.allowed_output_dir = Path(allowed_output_dir).resolve()
        
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
    
    def is_write_allowed(self, file_path: str) -> Tuple[bool, str]:
        """
        Check if write to file_path is allowed.
        
        Args:
            file_path: Path to write to
        
        Returns:
            (allowed: bool, reason: str)
        """
        try:
            target_path = Path(file_path).resolve()
            
            # Check if path is within allowed directory
            try:
                target_path.relative_to(self.allowed_output_dir)
            except ValueError:
                return False, f"Write outside allowed directory: {self.allowed_output_dir}"
            
            # Check for system directories
            if target_path.parts[0] in ["etc", "sys", "proc", "dev", "Windows", "System32"]:
                return False, "Cannot write to system directories"
            
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
            Safe path within allowed directory
        
        Raises:
            SecurityError: If path is invalid
        """
        allowed, reason = self.is_write_allowed(file_path)
        
        if not allowed:
            raise SecurityError(f"Invalid output path: {reason}")
        
        return str(Path(file_path).resolve())


# Global instance
_controller = None


def get_file_access_controller(allowed_output_dir: str = "outputs/") -> FileAccessController:
    """Get or create global FileAccessController instance"""
    global _controller
    if _controller is None:
        _controller = FileAccessController(allowed_output_dir)
    return _controller