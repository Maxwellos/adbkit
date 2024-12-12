from .stats import Stats

class Entry(Stats):
    """
    A class representing a file or directory entry, extending the Stats class.
    """

    def __init__(self, name: str, mode: int, size: int, mtime: int):
        """
        Initialize an Entry object.

        Args:
            name (str): The name of the file or directory.
            mode (int): The file mode (type and permissions).
            size (int): The total size of the file in bytes.
            mtime (int): The time of last modification in seconds since the epoch.
        """
        super().__init__(mode, size, mtime)
        self.name = name

    def __str__(self) -> str:
        """
        Return a string representation of the entry.

        Returns:
            str: The name of the file or directory.
        """
        return self.name

    def __repr__(self) -> str:
        """
        Return a detailed string representation of the entry.

        Returns:
            str: A detailed representation including name, mode, size, and mtime.
        """
        return f"Entry(name='{self.name}', mode={self.mode}, size={self.size}, mtime={self.mtime})"
