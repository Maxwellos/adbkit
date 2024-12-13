import asyncio
import logging
import struct
from asyncio import StreamReader, StreamWriter
from typing import Optional
from .packet import Packet
from .packetreader import PacketReader
from .protocol import Protocol
from .service import Service
from .servicemap import ServiceMap
from .rollingcounter import RollingCounter
from .auth import Auth

logger = logging.getLogger('adb.tcpusb.socket')

UINT32_MAX = 0xFFFFFFFF
UINT16_MAX = 0xFFFF
AUTH_TOKEN = 1
AUTH_SIGNATURE = 2
AUTH_RSAPUBLICKEY = 3
TOKEN_LENGTH = 20

class Socket:
    class AuthError(Exception):
        def __init__(self, message):
            super().__init__(message)
            self.name = 'AuthError'

    class UnauthorizedError(Exception):
        def __init__(self):
            super().__init__("Unauthorized access")
            self.name = 'UnauthorizedError'

    def __init__(self, client, serial, reader: StreamReader, writer: StreamWriter, options=None):
        self.client = client
        self.serial = serial
        self.reader = reader
        self.writer = writer
        self.options = options or {}
        self.options.setdefault('auth', asyncio.Future())
        self.ended = False
        self.version = 1
        self.max_payload = 4096
        self.authorized = False
        self.sync_token = RollingCounter(UINT32_MAX)
        self.remote_id = RollingCounter(UINT32_MAX)
        self.services = ServiceMap()
        self.token = None
        self.signature = None
        self.packet_reader = PacketReader(self.reader)
        self.packet_reader.on('packet', self._handle)
        self.packet_reader.on('error', self._error)
        self.packet_reader.on('end', self.end)

    async def end(self):
        if self.ended:
            return
        self.services.end()
        self.writer.close()
        await self.writer.wait_closed()
        self.ended = True

    def _error(self, err):
        logger.error(f"PacketReader error: {err}")
        self.end()

    async def _handle(self, packet):
        if self.ended:
            return
        try:
            if packet.command == Packet.A_SYNC:
                await self._handle_sync_packet(packet)
            elif packet.command == Packet.A_CNXN:
                await self._handle_connection_packet(packet)
            elif packet.command == Packet.A_OPEN:
                await self._handle_open_packet(packet)
            elif packet.command in (Packet.A_OKAY, Packet.A_WRTE, Packet.A_CLSE):
                await self._forward_service_packet(packet)
            elif packet.command == Packet.A_AUTH:
                await self._handle_auth_packet(packet)
            else:
                raise ValueError(f"Unknown command {packet.command}")
        except (Socket.AuthError, Socket.UnauthorizedError):
            await self.end()
        except Exception as err:
            logger.error(f"Error handling packet: {err}")
            await self.end()

    async def _handle_sync_packet(self, packet):
        logger.debug('I:A_SYNC')
        logger.debug('O:A_SYNC')
        await self.write(Packet.assemble(Packet.A_SYNC, 1, self.sync_token.next(), None))

    async def _handle_connection_packet(self, packet):
        logger.debug('I:A_CNXN', packet)
        self.version = struct.unpack('<I', packet.arg0)[0]
        self.max_payload = min(UINT16_MAX, packet.arg1)
        self.token = await self._create_token()
        logger.debug(f"Created challenge '{self.token.hex()}'")
        logger.debug('O:A_AUTH')
        await self.write(Packet.assemble(Packet.A_AUTH, AUTH_TOKEN, 0, self.token))

    async def _handle_auth_packet(self, packet):
        logger.debug('I:A_AUTH', packet)
        if packet.arg0 == AUTH_SIGNATURE:
            logger.debug(f"Received signature '{packet.data.hex()}'")
            if not self.signature:
                self.signature = packet.data
            logger.debug('O:A_AUTH')
            await self.write(Packet.assemble(Packet.A_AUTH, AUTH_TOKEN, 0, self.token))
        elif packet.arg0 == AUTH_RSAPUBLICKEY:
            if not self.signature:
                raise Socket.AuthError("Public key sent before signature")
            if not packet.data or len(packet.data) < 2:
                raise Socket.AuthError("Empty RSA public key")
            logger.debug(f"Received RSA public key '{packet.data.hex()}'")
            key = await Auth.parse_public_key(self._skip_null(packet.data))
            digest = self.token
            sig = self.signature
            if not key.verify(digest, sig):
                logger.debug("Signature mismatch")
                raise Socket.AuthError("Signature mismatch")
            logger.debug("Signature verified")
            await self.options['auth'](key)
            self.authorized = True
            logger.debug('O:A_CNXN')
            await self.write(Packet.assemble(Packet.A_CNXN, struct.pack('<I', self.version), self.max_payload, await self._device_id()))
        else:
            raise ValueError(f"Unknown authentication method {packet.arg0}")

    async def _handle_open_packet(self, packet):
        if not self.authorized:
            raise Socket.UnauthorizedError()
        remote_id = packet.arg0
        local_id = self.remote_id.next()
        if not packet.data or len(packet.data) < 2:
            raise ValueError("Empty service name")
        name = self._skip_null(packet.data)
        logger.debug(f"Calling {name}")
        service = Service(self.client, self.serial, local_id, remote_id, self.reader, self.writer)
        self.services.insert(local_id, service)
        logger.debug(f"Handling {self.services.count} services simultaneously")
        await service.handle(packet)
        self.services.remove(local_id)
        logger.debug(f"Handling {self.services.count} services simultaneously")
        await service.end()

    async def _forward_service_packet(self, packet):
        if not self.authorized:
            raise Socket.UnauthorizedError()
        remote_id = packet.arg0
        local_id = packet.arg1
        service = self.services.get(local_id)
        if service:
            await service.handle(packet)
        else:
            logger.debug("Received a packet to a service that may have been closed already")

    async def write(self, chunk):
        if self.ended:
            return
        self.writer.write(chunk)
        await self.writer.drain()

    async def _create_token(self):
        return await asyncio.get_event_loop().run_in_executor(None, lambda: os.urandom(TOKEN_LENGTH))

    def _skip_null(self, data):
        return data[:-1]

    async def _device_id(self):
        logger.debug("Loading device properties to form a standard device ID")
        properties = await self.client.get_properties(self.serial)
        id_str = ''.join([f"{prop}={properties[prop]};" for prop in ['ro.product.name', 'ro.product.model', 'ro.product.device']])
        return f"device::{id_str}\0".encode()
