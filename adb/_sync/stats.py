import os
from datetime import datetime

class Stats:
    """
    A class representing file statistics, similar to os.stat_result.
    """

    # File type and mode constants
    S_IFMT = 0xf000   # Bit mask for the file type bit field
    S_IFSOCK = 0xc000 # Socket
    S_IFLNK = 0xa000  # Symbolic link
    S_IFREG = 0x8000  # Regular file
    S_IFBLK = 0x6000  # Block device
    S_IFDIR = 0x4000  # Directory
    S_IFCHR = 0x2000  # Character device
    S_IFIFO = 0x1000  # FIFO

    # Permission bits
    S_ISUID = 0x800   # Set UID bit
    S_ISGID = 0x400   # Set GID bit
    S_ISVTX = 0x200   # Sticky bit

    # User permission bits
    S_IRWXU = 0x1c0   # Mask for file owner permissions
    S_IRUSR = 0x100   # Owner has read permission
    S_IWUSR = 0x80    # Owner has write permission
    S_IXUSR = 0x40    # Owner has execute permission

    # Group permission bits
    S_IRWXG = 0x38    # Mask for group permissions
    S_IRGRP = 0x20    # Group has read permission

    def __init__(self, mode: int, size: int, mtime: int):
        """
        Initialize a Stats object.

        Args:
            mode (int): The file mode (type and permissions).
            size (int): The total size of the file in bytes.
            mtime (int): The time of last modification in seconds since the epoch.
        """
        self.mode = mode
        self.size = size
        self.mtime = datetime.fromtimestamp(mtime)

    def is_dir(self) -> bool:
        """Check if this is a directory."""
        return (self.mode & self.S_IFMT) == self.S_IFDIR

    def is_file(self) -> bool:
        """Check if this is a regular file."""
        return (self.mode & self.S_IFMT) == self.S_IFREG

    def is_symlink(self) -> bool:
        """Check if this is a symbolic link."""
        return (self.mode & self.S_IFMT) == self.S_IFLNK

    def __repr__(self) -> str:
        return f"Stats(mode={self.mode}, size={self.size}, mtime={self.mtime})"
