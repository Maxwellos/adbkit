import asyncio
from typing import Dict, List, Callable


class PushTransfer:
    """
      A base class representing a transfer operation (push or pull).
      """

    def __init__(self):
        """
        Initialize a Transfer object.
        """
        self._stack: List[int] = []
        self.stats: Dict[str, int] = {
            "bytesTransferred": 0
        }
        self._event_handlers: Dict[str, List[Callable]] = {
            "cancel": [],
            "progress": [],
            "end": []
        }

    def on(self, event: str, callback: Callable) -> None:
        """
        Register an event handler.

        Args:
            event (str): The event name.
            callback (Callable): The callback function to be called when the event is emitted.
        """
        if event in self._event_handlers:
            self._event_handlers[event].append(callback)

    def emit(self, event: str, *args) -> None:
        """
        Emit an event.

        Args:
            event (str): The event name.
            *args: Arguments to be passed to the event handlers.
        """
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                handler(*args)

    async def cancel(self) -> None:
        """
        Cancel the transfer operation.
        """
        self.emit("cancel")

    def push(self, byte_count: int) -> None:
        """
        Push a byte count to the stack.

        Args:
            byte_count (int): The number of bytes to push.
        """
        self._stack.append(byte_count)

    def pop(self) -> None:
        """
        Pop a byte count from the stack and update the stats.
        """
        byte_count = self._stack.pop()
        self.stats["bytesTransferred"] += byte_count
        self.emit("progress", self.stats)

    async def end(self) -> None:
        """
        End the transfer operation.
        """
        self.emit("end")

    async def wait_for_completion(self) -> None:
        """
        Wait for the transfer operation to complete.
        """
        end_event = asyncio.Event()
        self.on("end", end_event.set)
        await end_event.wait()
