import asyncio
import logging
from typing import Any, Optional, Dict
import subprocess

from .parser import Parser
from .dump import dump

logger = logging.getLogger(__name__)

class Connection:
    """
    Represents a connection to the ADB server.
    """

    def __init__(self, options: Dict[str, Any]):
        """
        Initialize the Connection.

        Args:
            options (Dict[str, Any]): Connection options including 'host', 'port', and 'bin' (path to ADB binary).
        """
        self.options = options
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.parser: Optional[Parser] = None
        self.tried_starting = False

    async def connect(self) -> 'Connection':
        """
        Establish a connection to the ADB server.

        Returns:
            Connection: The current Connection instance.
        """
        self.reader, self.writer = await asyncio.open_connection(
            self.options['host'], self.options['port'])
        self.parser = Parser(self.reader)
        return self

    async def close(self):
        """Close the connection."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    async def write(self, data: bytes):
        """
        Write data to the connection.

        Args:
            data (bytes): The data to write.
        """
        if self.writer:
            self.writer.write(dump(data))
            await self.writer.drain()

    async def start_server(self):
        """Start the ADB server."""
        logger.debug(f"Starting ADB server via '{self.options['bin']} start-server'")
        await self._exec(['start-server'])

    async def _exec(self, args: list, options: Dict[str, Any] = {}):
        """
        Execute an ADB common.

        Args:
            args (list): Command arguments.
            options (Dict[str, Any], optional): Execution options. Defaults to {}.
        """
        cmd = [self.options['bin']] + args
        logger.debug(f"CLI: {' '.join(cmd)}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"ADB common failed: {stderr.decode()}")

    async def _handle_error(self, err: Exception):
        """
        Handle connection errors.

        Args:
            err (Exception): The error that occurred.
        """
        if isinstance(err, ConnectionRefusedError) and not self.tried_starting:
            logger.debug("Connection was refused, trying to start the server once")
            self.tried_starting = True
            try:
                await self.start_server()
                await self.connect()
            except Exception as e:
                logger.error(f"Failed to start ADB server: {e}")
                raise
        else:
            logger.error(f"Connection error: {err}")
            await self.close()
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
