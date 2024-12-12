import asyncio
from typing import Optional, Union

from .protocol import Protocol

class Parser:
    """Parser for ADB protocol data."""

    def __init__(self, stream: asyncio.StreamReader):
        self.stream = stream
        self.ended = False

    async def end(self) -> bool:
        """End the parser and consume any remaining data."""
        if self.ended:
            return True

        while await self.stream.read(1024):
            pass

        self.ended = True
        return True

    def raw(self) -> asyncio.StreamReader:
        """Get the raw stream."""
        return self.stream

    async def read_all(self) -> bytes:
        """Read all remaining data from the stream."""
        data = await self.stream.read()
        self.ended = True
        return data

    async def read_ascii(self, how_many: int) -> str:
        """Read a specified number of ASCII characters."""
        chunk = await self.read_bytes(how_many)
        return chunk.decode('ascii')

    async def read_bytes(self, how_many: int) -> bytes:
        """Read a specified number of bytes."""
        if how_many == 0:
            return b''

        chunk = await self.stream.readexactly(how_many)
        if len(chunk) < how_many:
            self.ended = True
            raise PrematureEOFError(how_many - len(chunk))

        return chunk

    async def read_byte_flow(self, how_many: int, target_stream: asyncio.StreamWriter) -> None:
        """Read bytes and write them to another stream."""
        remaining = how_many
        while remaining > 0:
            chunk = await self.stream.read(min(remaining, 4096))
            if not chunk:
                self.ended = True
                raise PrematureEOFError(remaining)
            target_stream.write(chunk)
            await target_stream.drain()
            remaining -= len(chunk)

    async def read_error(self) -> None:
        """Read an error message and raise a FailError."""
        value = await self.read_value()
        raise FailError(value.decode())

    async def read_value(self) -> bytes:
        """Read a length-prefixed value."""
        length_str = await self.read_ascii(4)
        length = Protocol.decode_length(length_str)
        return await self.read_bytes(length)

    async def read_until(self, code: int) -> bytes:
        """Read until a specific byte is encountered."""
        buffer = bytearray()
        while True:
            chunk = await self.read_bytes(1)
            if chunk[0] == code:
                return bytes(buffer)
            buffer.extend(chunk)

    async def search_line(self, regex: 're.Pattern') -> Optional[Union[str, 're.Match']]:
        """Search for a line matching the given regex."""
        while True:
            line = await self.read_line()
            match = regex.search(line)
            if match:
                return match
            if self.ended:
                return None

    async def read_line(self) -> str:
        """Read a line (until newline character)."""
        line = await self.read_until(0x0a)
        return line.rstrip(b'\r\n').decode()

    async def unexpected(self, data: str, expected: str) -> None:
        """Raise an UnexpectedDataError."""
        raise UnexpectedDataError(data, expected)


class FailError(Exception):
    """Error raised when a failure occurs in the ADB protocol."""

    def __init__(self, message: str):
        super().__init__(f"Failure: '{message}'")


class PrematureEOFError(Exception):
    """Error raised when the stream ends prematurely."""

    def __init__(self, missing_bytes: int):
        super().__init__(f"Premature end of stream, needed {missing_bytes} more bytes")
        self.missing_bytes = missing_bytes


class UnexpectedDataError(Exception):
    """Error raised when unexpected data is encountered."""

    def __init__(self, unexpected: str, expected: str):
        super().__init__(f"Unexpected '{unexpected}', was expecting {expected}")
        self.unexpected = unexpected
        self.expected = expected
