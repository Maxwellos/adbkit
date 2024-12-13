import os
import asyncio
import aiofiles
import logging
from typing import List, Union, BinaryIO

from .parser import Parser
from .protocol import Protocol
from ._sync.stats import Stats
from ._sync.entry import Entry
from ._sync.pushtransfer import PushTransfer
from ._sync.pulltransfer import PullTransfer

logger = logging.getLogger(__name__)

class Sync:
    TEMP_PATH = '/data/local/tmp'
    DEFAULT_CHMOD = 0o644
    DATA_MAX_LENGTH = 65536

    @staticmethod
    def temp(path: str) -> str:
        return f"{Sync.TEMP_PATH}/{os.path.basename(path)}"

    def __init__(self, connection):
        self.connection = connection
        self.parser = self.connection.parser

    async def stat(self, path: str) -> Stats:
        await self._send_command_with_arg(Protocol.STAT, path)
        reply = await self.parser.read_ascii(4)
        if reply == Protocol.STAT:
            stat_data = await self.parser.read_bytes(12)
            mode = int.from_bytes(stat_data[:4], 'little')
            size = int.from_bytes(stat_data[4:8], 'little')
            mtime = int.from_bytes(stat_data[8:12], 'little')
            if mode == 0:
                raise FileNotFoundError(f"No such file or directory: '{path}'")
            return Stats(mode, size, mtime)
        elif reply == Protocol.FAIL:
            await self._read_error()
        else:
            await self.parser.unexpected(reply, 'STAT or FAIL')

    async def readdir(self, path: str) -> List[Entry]:
        files = []
        await self._send_command_with_arg(Protocol.LIST, path)
        while True:
            reply = await self.parser.read_ascii(4)
            if reply == Protocol.DENT:
                stat_data = await self.parser.read_bytes(16)
                mode = int.from_bytes(stat_data[:4], 'little')
                size = int.from_bytes(stat_data[4:8], 'little')
                mtime = int.from_bytes(stat_data[8:12], 'little')
                namelen = int.from_bytes(stat_data[12:16], 'little')
                name = (await self.parser.read_bytes(namelen)).decode()
                if name not in ('.', '..'):
                    files.append(Entry(name, mode, size, mtime))
            elif reply == Protocol.DONE:
                await self.parser.read_bytes(16)  # Read and discard 16 zero bytes
                return files
            elif reply == Protocol.FAIL:
                await self._read_error()
            else:
                await self.parser.unexpected(reply, 'DENT, DONE or FAIL')

    async def push(self, contents: Union[str, BinaryIO], path: str, mode: int = DEFAULT_CHMOD) -> PushTransfer:
        if isinstance(contents, str):
            return await self.push_file(contents, path, mode)
        else:
            return await self.push_stream(contents, path, mode)

    async def push_file(self, file: str, path: str, mode: int = DEFAULT_CHMOD) -> PushTransfer:
        mode |= Stats.S_IFREG
        await self._send_command_with_arg(Protocol.SEND, f"{path},{mode}")
        async with aiofiles.open(file, 'rb') as f:
            return await self._write_data(f, int(os.path.getmtime(file)))

    async def push_stream(self, stream: BinaryIO, path: str, mode: int = DEFAULT_CHMOD) -> PushTransfer:
        mode |= Stats.S_IFREG
        await self._send_command_with_arg(Protocol.SEND, f"{path},{mode}")
        return await self._write_data(stream, int(asyncio.get_event_loop().time()))

    async def pull(self, path: str) -> PullTransfer:
        await self._send_command_with_arg(Protocol.RECV, path)
        return await self._read_data()

    async def end(self):
        await self.connection.close()

    async def _write_data(self, stream: BinaryIO, timestamp: int) -> PushTransfer:
        transfer = PushTransfer()
        try:
            while True:
                chunk = await stream.read(self.DATA_MAX_LENGTH)
                if not chunk:
                    break
                await self._send_command_with_length(Protocol.DATA, len(chunk))
                transfer.push(len(chunk))
                self.connection.write(chunk)
                await self.connection.drain()
            await self._send_command_with_length(Protocol.DONE, timestamp)
            reply = await self.parser.read_ascii(4)
            if reply == Protocol.OKAY:
                await self.parser.read_bytes(4)  # Read and discard 4 zero bytes
            elif reply == Protocol.FAIL:
                await self._read_error()
            else:
                await self.parser.unexpected(reply, 'OKAY or FAIL')
        except Exception as e:
            transfer.emit('error', e)
        finally:
            transfer.end()
        return transfer

    async def _read_data(self) -> PullTransfer:
        transfer = PullTransfer()
        try:
            while True:
                reply = await self.parser.read_ascii(4)
                if reply == Protocol.DATA:
                    length_data = await self.parser.read_bytes(4)
                    length = int.from_bytes(length_data, 'little')
                    await self.parser.read_byte_flow(length, transfer)
                elif reply == Protocol.DONE:
                    await self.parser.read_bytes(4)  # Read and discard 4 zero bytes
                    break
                elif reply == Protocol.FAIL:
                    await self._read_error()
                else:
                    await self.parser.unexpected(reply, 'DATA, DONE or FAIL')
        except Exception as e:
            transfer.emit('error', e)
        finally:
            transfer.end()
        return transfer

    async def _read_error(self):
        length = int.from_bytes(await self.parser.read_bytes(4), 'little')
        error_msg = (await self.parser.read_bytes(length)).decode()
        raise Exception(f"ADB Sync Error: {error_msg}")

    async def _send_command_with_length(self, cmd: bytes, length: int):
        if cmd != Protocol.DATA:
            logger.debug(cmd.decode())
        payload = cmd + length.to_bytes(4, 'little')
        self.connection.write(payload)
        await self.connection.drain()

    async def _send_command_with_arg(self, cmd: bytes, arg: str):
        logger.debug(f"{cmd.decode()} {arg}")
        arg_bytes = arg.encode()
        payload = cmd + len(arg_bytes).to_bytes(4, 'little') + arg_bytes
        self.connection.write(payload)
        await self.connection.drain()
