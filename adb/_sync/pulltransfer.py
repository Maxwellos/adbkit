import asyncio
from typing import Dict, Any

class PullTransfer(asyncio.StreamReader):
    """
    A class representing a pull transfer operation.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop = None):
        super().__init__(loop=loop)
        self.stats: Dict[str, int] = {
            "bytesTransferred": 0
        }
        self._cancel_event = asyncio.Event()

    def cancel(self) -> None:
        """
        Cancel the transfer operation.
        """
        self._cancel_event.set()
        self.feed_eof()

    async def read(self, n: int = -1) -> bytes:
        """
        Read data from the stream.

        Args:
            n (int): Number of bytes to read. -1 means read all available.

        Returns:
            bytes: The read data.
        """
        data = await super().read(n)
        self.stats["bytesTransferred"] += len(data)
        self._progress_callback(self.stats)
        return data

    def feed_data(self, data: bytes) -> None:
        """
        Feed data into the stream.

        Args:
            data (bytes): The data to feed into the stream.
        """
        super().feed_data(data)
        self.stats["bytesTransferred"] += len(data)
        self._progress_callback(self.stats)

    def _progress_callback(self, stats: Dict[str, Any]) -> None:
        """
        Callback method for progress updates.

        Args:
            stats (Dict[str, Any]): The current transfer statistics.
        """
        # This method can be overridden or set by the user to handle progress updates
        pass

    def set_progress_callback(self, callback: callable) -> None:
        """
        Set the progress callback function.

        Args:
            callback (callable): The function to call with progress updates.
        """
        self._progress_callback = callback

    async def wait_for_transfer(self) -> None:
        """
        Wait for the transfer to complete or be cancelled.
        """
        done, pending = await asyncio.wait(
            [self._cancel_event.wait(), self._wait_for_eof()],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

    async def _wait_for_eof(self) -> None:
        """
        Wait for the end of the stream.
        """
        while not self.at_eof():
            await asyncio.sleep(0.1)
