"""
Helper Utilities Module

Common utility functions used across the application.
"""

import os
import sys
import time
import platform
import subprocess
from typing import Optional


def get_timestamp(format_str: str = "%a_%d%b_%Y_%Hh%Mm%Ss") -> str:
    """
    Get current timestamp as formatted string.

    Args:
        format_str: strftime format string

    Returns:
        Formatted timestamp string
    """
    return time.strftime(format_str, time.localtime())


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename


def open_file(file_path: str) -> bool:
    """
    Open a file with the system's default application.

    Args:
        file_path: Path to the file

    Returns:
        True if successful
    """
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", file_path])
        else:  # Linux
            subprocess.call(["xdg-open", file_path])
        return True
    except Exception:
        return False


def open_directory(dir_path: str) -> bool:
    """
    Open a directory in the system's file explorer.

    Args:
        dir_path: Path to the directory

    Returns:
        True if successful
    """
    try:
        if platform.system() == "Windows":
            os.startfile(dir_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", dir_path])
        else:  # Linux
            subprocess.call(["xdg-open", dir_path])
        return True
    except Exception:
        return False


def get_platform_path_separator() -> str:
    """Get the platform-specific path separator."""
    return os.sep


def normalize_path(path: str) -> str:
    """
    Normalize a path for the current platform.

    Args:
        path: Path string

    Returns:
        Normalized path
    """
    return os.path.normpath(path)


def ensure_directory_exists(dir_path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Directory path

    Returns:
        True if directory exists or was created
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception:
        return False


def get_file_extension(file_path: str) -> str:
    """
    Get the extension of a file.

    Args:
        file_path: Path to file

    Returns:
        File extension (including dot)
    """
    return os.path.splitext(file_path)[1]


def get_filename_without_extension(file_path: str) -> str:
    """
    Get filename without extension.

    Args:
        file_path: Path to file

    Returns:
        Filename without extension
    """
    return os.path.splitext(os.path.basename(file_path))[0]


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def is_valid_xml_file(file_path: str) -> bool:
    """
    Check if a file appears to be a valid XML file.

    Args:
        file_path: Path to file

    Returns:
        True if file appears to be XML
    """
    if not os.path.exists(file_path):
        return False

    ext = get_file_extension(file_path).lower()
    if ext != ".xml":
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            first_line = f.readline()
            return first_line.strip().startswith("<?xml") or first_line.strip().startswith("<!DOCTYPE")
    except Exception:
        return False


def is_valid_excel_file(file_path: str) -> bool:
    """
    Check if a file appears to be a valid Excel file.

    Args:
        file_path: Path to file

    Returns:
        True if file appears to be Excel
    """
    if not os.path.exists(file_path):
        return False

    ext = get_file_extension(file_path).lower()
    return ext in [".xlsx", ".xlsm", ".xls"]


def is_valid_csv_file(file_path: str) -> bool:
    """
    Check if a file appears to be a valid CSV file.

    Args:
        file_path: Path to file

    Returns:
        True if file appears to be CSV
    """
    if not os.path.exists(file_path):
        return False

    ext = get_file_extension(file_path).lower()
    return ext == ".csv"
