import asyncio
from asyncio import StreamReader, StreamWriter
from typing import Optional
from .packet import Packet
from .protocol import Protocol
from .parser import Parser
import logging

logger = logging.getLogger('adb.tcpusb.service')

class Service:
    class PrematurePacketError(Exception):
        def __init__(self, packet):
            self.packet = packet
            super().__init__("Premature packet")

    class LateTransportError(Exception):
        def __init__(self):
            super().__init__("Late transport")

    def __init__(self, client, serial, local_id, remote_id, reader: StreamReader, writer: StreamWriter):
        self.client = client
        self.serial = serial
        self.local_id = local_id
        self.remote_id = remote_id
        self.reader = reader
        self.writer = writer
        self.opened = False
        self.ended = False
        self.transport = None
        self.need_ack = False

    async def end(self):
        if self.transport:
            self.transport.close()
        if self.ended:
            return
        logger.debug('O:A_CLSE')
        local_id = self.local_id if self.opened else 0
        try:
            self.writer.write(Packet.assemble(Packet.A_CLSE, local_id, self.remote_id, None))
            await self.writer.drain()
        except Exception as err:
            logger.error(f"Error sending A_CLSE packet: {err}")
        self.transport = None
        self.ended = True

    async def handle(self, packet):
        try:
            if packet.command == Packet.A_OPEN:
                await self._handle_open_packet(packet)
            elif packet.command == Packet.A_OKAY:
                await self._handle_okay_packet(packet)
            elif packet.command == Packet.A_WRTE:
                await self._handle_write_packet(packet)
            elif packet.command == Packet.A_CLSE:
                await self._handle_close_packet(packet)
            else:
                raise ValueError(f"Unexpected packet {packet.command}")
        except Exception as err:
            logger.error(f"Error handling packet: {err}")
            await self.end()

    async def _handle_open_packet(self, packet):
        logger.debug('I:A_OPEN', packet)
        self.transport = await self.client.transport(self.serial)
        if self.ended:
            raise self.LateTransportError()
        self.transport.write(Protocol.encode_data(packet.data[:-1]))
        reply = await self.transport.parser.read_ascii(4)
        if reply == Protocol.OKAY:
            logger.debug('O:A_OKAY')
            self.writer.write(Packet.assemble(Packet.A_OKAY, self.local_id, self.remote_id, None))
            await self.writer.drain()
            self.opened = True
        elif reply == Protocol.FAIL:
            await self.transport.parser.read_error()
        else:
            await self.transport.parser.unexpected(reply, 'OKAY or FAIL')
        await self._start_transport()

    async def _start_transport(self):
        try:
            while not self.ended:
                await self._try_push()
                await asyncio.sleep(0.1)
        finally:
            await self.end()

    async def _handle_okay_packet(self, packet):
        logger.debug('I:A_OKAY', packet)
        if self.ended:
            return
        if not self.transport:
            raise self.PrematurePacketError(packet)
        self.need_ack = False
        await self._try_push()

    async def _handle_write_packet(self, packet):
        logger.debug('I:A_WRTE', packet)
        if self.ended:
            return
        if not self.transport:
            raise self.PrematurePacketError(packet)
        if packet.data:
            self.transport.write(packet.data)
        logger.debug('O:A_OKAY')
        self.writer.write(Packet.assemble(Packet.A_OKAY, self.local_id, self.remote_id, None))
        await self.writer.drain()

    async def _handle_close_packet(self, packet):
        logger.debug('I:A_CLSE', packet)
        if self.ended:
            return
        if not self.transport:
            raise self.PrematurePacketError(packet)
        await self.end()

    async def _try_push(self):
        if self.need_ack or self.ended:
            return
        chunk = await self._read_chunk(self.transport)
        if chunk:
            logger.debug('O:A_WRTE')
            self.writer.write(Packet.assemble(Packet.A_WRTE, self.local_id, self.remote_id, chunk))
            await self.writer.drain()
            self.need_ack = True

    async def _read_chunk(self, stream):
        return await stream.read(self.writer.get_extra_info('max_payload')) or await stream.read()
