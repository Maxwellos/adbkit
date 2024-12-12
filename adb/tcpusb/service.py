import asyncio
import logging
from typing import Any, Optional
from ..parser import Parser
from ..protocol import Protocol
from .packet import Packet

logger = logging.getLogger(__name__)

class Service:
    """
    Service 类实现了 ADB 服务的核心功能，包括处理各种类型的数据包和管理与设备的通信。
    """

    def __init__(self, client: Any, serial: str, local_id: int, remote_id: int, socket: Any):
        self.client = client
        self.serial = serial
        self.local_id = local_id
        self.remote_id = remote_id
        self.socket = socket
        self.opened = False
        self.ended = False
        self.transport = None
        self.need_ack = False

    async def end(self):
        """结束服务并关闭连接。"""
        if self.transport:
            self.transport.close()
        if self.ended:
            return self

        logger.debug('O:A_CLSE')
        local_id = self.local_id if self.opened else 0
        try:
            await self.socket.write(Packet.assemble(Packet.A_CLSE, local_id, self.remote_id, None))
        except Exception as err:
            logger.error(f"Error while ending service: {err}")

        self.transport = None
        self.ended = True
        return self

    async def handle(self, packet: Packet):
        """处理接收到的数据包。"""
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

    async def _handle_open_packet(self, packet: Packet):
        logger.debug(f'I:A_OPEN {packet}')
        try:
            self.transport = await self.client.transport(self.serial)
            if self.ended:
                raise LateTransportError()

            await self.transport.write(Protocol.encode_data(packet.data[:-1]))
            reply = await self.transport.parser.read_ascii(4)

            if reply == Protocol.OKAY:
                logger.debug('O:A_OKAY')
                await self.socket.write(Packet.assemble(Packet.A_OKAY, self.local_id, self.remote_id, None))
                self.opened = True
            elif reply == Protocol.FAIL:
                error = await self.transport.parser.read_error()
                raise Exception(f"Failed to open transport: {error}")
            else:
                raise ValueError(f"Unexpected reply: {reply}")

            while not self.ended:
                await self._try_push()
                await asyncio.sleep(0)  # Allow other tasks to run

        except Exception as err:
            logger.error(f"Error in _handle_open_packet: {err}")
        finally:
            await self.end()

    async def _handle_okay_packet(self, packet: Packet):
        logger.debug(f'I:A_OKAY {packet}')
        if self.ended:
            return
        if not self.transport:
            raise PrematurePacketError(packet)
        self.need_ack = False
        await self._try_push()

    async def _handle_write_packet(self, packet: Packet):
        logger.debug(f'I:A_WRTE {packet}')
        if self.ended:
            return
        if not self.transport:
            raise PrematurePacketError(packet)
        if packet.data:
            await self.transport.write(packet.data)
        logger.debug('O:A_OKAY')
        await self.socket.write(Packet.assemble(Packet.A_OKAY, self.local_id, self.remote_id, None))

    async def _handle_close_packet(self, packet: Packet):
        logger.debug(f'I:A_CLSE {packet}')
        if self.ended:
            return
        if not self.transport:
            raise PrematurePacketError(packet)
        await self.end()

    async def _try_push(self):
        if self.need_ack or self.ended:
            return
        chunk = self._read_chunk(self.transport.socket)
        if chunk:
            logger.debug('O:A_WRTE')
            await self.socket.write(Packet.assemble(Packet.A_WRTE, self.local_id, self.remote_id, chunk))
            self.need_ack = True

    def _read_chunk(self, stream: Any) -> Optional[bytes]:
        return stream.read(self.socket.max_payload) or stream.read()

class PrematurePacketError(Exception):
    """当收到预期之外的数据包时抛出的异常。"""
    def __init__(self, packet: Packet):
        self.packet = packet
        super().__init__("Premature packet")

class LateTransportError(Exception):
    """当传输已经结束但仍尝试使用时抛出的异常。"""
    def __init__(self):
        super().__init__("Late transport")
