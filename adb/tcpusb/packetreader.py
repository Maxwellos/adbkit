import asyncio
from typing import Optional
from .packet import Packet

class PacketReader:
    def __init__(self, stream):
        self.stream = stream
        self.in_body = False
        self.buffer = b''
        self.packet: Optional[Packet] = None
        self.packet_handlers = []
        self.error_handlers = []
        self.end_handlers = []

    async def start_reading(self):
        try:
            while True:
                chunk = await self.stream.read(4096)
                if not chunk:
                    break
                await self._process_chunk(chunk)
        except Exception as e:
            for handler in self.error_handlers:
                handler(e)
        finally:
            for handler in self.end_handlers:
                handler()

    async def _process_chunk(self, chunk):
        self.buffer += chunk
        while self.buffer:
            if self.in_body:
                if len(self.buffer) >= self.packet.length:
                    self.packet.data = self.buffer[:self.packet.length]
                    self.buffer = self.buffer[self.packet.length:]
                    if not self.packet.verify_checksum():
                        raise ChecksumError(self.packet)
                    for handler in self.packet_handlers:
                        handler(self.packet)
                    self.in_body = False
                else:
                    break
            else:
                if len(self.buffer) >= 24:
                    header = self.buffer[:24]
                    self.buffer = self.buffer[24:]
                    self.packet = Packet.from_header(header)
                    if not self.packet.verify_magic():
                        raise MagicError(self.packet)
                    if self.packet.length == 0:
                        for handler in self.packet_handlers:
                            handler(self.packet)
                    else:
                        self.in_body = True
                else:
                    break

    def on_packet(self, handler):
        self.packet_handlers.append(handler)

    def on_error(self, handler):
        self.error_handlers.append(handler)

    def on_end(self, handler):
        self.end_handlers.append(handler)

class ChecksumError(Exception):
    def __init__(self, packet):
        super().__init__("Checksum mismatch")
        self.packet = packet

class MagicError(Exception):
    def __init__(self, packet):
        super().__init__("Magic value mismatch")
        self.packet = packet
