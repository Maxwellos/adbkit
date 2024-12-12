import asyncio
import logging
from typing import Any, Optional
import os
import struct

from ..parser import Parser
from ..protocol import Protocol
from ..auth import Auth
from .packet import Packet
from .packetreader import PacketReader
from .service import Service
from .servicemap import ServiceMap
from .rollingcounter import RollingCounter

logger = logging.getLogger(__name__)

class Socket:
    UINT32_MAX = 0xFFFFFFFF
    UINT16_MAX = 0xFFFF
    AUTH_TOKEN = 1
    AUTH_SIGNATURE = 2
    AUTH_RSAPUBLICKEY = 3
    TOKEN_LENGTH = 20

    def __init__(self, client: Any, serial: str, socket: Any, options: dict = None):
        self.client = client
        self.serial = serial
        self.socket = socket
        self.options = options or {}
        self.options['auth'] = self.options.get('auth', lambda: True)

        self.ended = False
        self.socket.setblocking(False)
        self.reader = PacketReader(self.socket)
        self.reader.on_packet(self._handle)
        self.reader.on_error(self._on_reader_error)
        self.reader.on_end(self.end)

        self.version = 1
        self.max_payload = 4096
        self.authorized = False
        self.sync_token = RollingCounter(self.UINT32_MAX)
        self.remote_id = RollingCounter(self.UINT32_MAX)
        self.services = ServiceMap()
        self.remote_address = self.socket.getpeername()[0]
        self.token = None
        self.signature = None

    async def end(self):
        if self.ended:
            return self
        await self.services.end()
        self.socket.close()
        self.ended = True
        return self

    async def _error(self, err):
        logger.error(f"Socket error: {err}")
        await self.end()

    async def _handle(self, packet: Packet):
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
        except AuthError:
            await self.end()
        except UnauthorizedError:
            await self.end()
        except Exception as err:
            await self._error(err)

    async def _handle_sync_packet(self, packet: Packet):
        logger.debug('I:A_SYNC')
        logger.debug('O:A_SYNC')
        await self.write(Packet.assemble(Packet.A_SYNC, 1, self.sync_token.next(), None))

    async def _handle_connection_packet(self, packet: Packet):
        logger.debug(f'I:A_CNXN {packet}')
        version = struct.unpack('>I', struct.pack('<I', packet.arg0))[0]
        self.max_payload = min(self.UINT16_MAX, packet.arg1)
        self.token = os.urandom(self.TOKEN_LENGTH)
        logger.debug(f"Created challenge '{self.token.hex()}'")
        logger.debug('O:A_AUTH')
        await self.write(Packet.assemble(Packet.A_AUTH, self.AUTH_TOKEN, 0, self.token))

    async def _handle_auth_packet(self, packet: Packet):
        logger.debug(f'I:A_AUTH {packet}')
        if packet.arg0 == self.AUTH_SIGNATURE:
            logger.debug(f"Received signature '{packet.data.hex()}'")
            if not self.signature:
                self.signature = packet.data
            logger.debug('O:A_AUTH')
            await self.write(Packet.assemble(Packet.A_AUTH, self.AUTH_TOKEN, 0, self.token))
        elif packet.arg0 == self.AUTH_RSAPUBLICKEY:
            if not self.signature:
                raise AuthError("Public key sent before signature")
            if not (packet.data and len(packet.data) >= 2):
                raise AuthError("Empty RSA public key")
            logger.debug(f"Received RSA public key '{packet.data[:-1].decode()}'")
            key = await Auth.parse_public_key(packet.data[:-1])
            digest = self.token
            sig = self.signature
            if not key.verify(digest, sig):
                logger.debug("Signature mismatch")
                raise AuthError("Signature mismatch")
            logger.debug("Signature verified")
            try:
                await self.options['auth'](key)
            except Exception as err:
                logger.debug("Connection rejected by user-defined auth handler")
                raise AuthError("Rejected by user-defined handler") from err
            device_id = await self._device_id()
            self.authorized = True
            logger.debug('O:A_CNXN')
            version_bytes = struct.pack('>I', self.version)
            await self.write(Packet.assemble(Packet.A_CNXN, struct.unpack('<I', version_bytes)[0], self.max_payload, device_id))
        else:
            raise ValueError(f"Unknown authentication method {packet.arg0}")

    async def _handle_open_packet(self, packet: Packet):
        if not self.authorized:
            raise UnauthorizedError()
        remote_id = packet.arg0
        local_id = self.remote_id.next()
        if not (packet.data and len(packet.data) >= 2):
            raise ValueError("Empty service name")
        name = packet.data[:-1].decode()
        logger.debug(f"Calling {name}")
        service = Service(self.client, self.serial, local_id, remote_id, self)
        try:
            self.services.insert(local_id, service)
            logger.debug(f"Handling {self.services.count} services simultaneously")
            await service.handle(packet)
        except Exception as err:
            logger.error(f"Error handling service: {err}")
        finally:
            self.services.remove(local_id)
            logger.debug(f"Handling {self.services.count} services simultaneously")
            await service.end()

    async def _forward_service_packet(self, packet: Packet):
        if not self.authorized:
            raise UnauthorizedError()
        remote_id = packet.arg0
        local_id = packet.arg1
        service = self.services.get(local_id)
        if service:
            await service.handle(packet)
        else:
            logger.debug("Received a packet to a service that may have been closed already")

    async def write(self, chunk: bytes):
        if self.ended:
            return
        self.socket.sendall(chunk)

    async def _device_id(self):
        logger.debug("Loading device properties to form a standard device ID")
        properties = await self.client.get_properties(self.serial)
        id_parts = [f"{prop}={properties.get(prop, '')};" for prop in ['ro.product.name', 'ro.product.model', 'ro.product.device']]
        return f"device::{''.join(id_parts)}".encode() + b'\0'

    async def _on_reader_error(self, err):
        logger.debug(f"PacketReader error: {err}")
        await self.end()

class AuthError(Exception):
    pass

class UnauthorizedError(Exception):
    def __init__(self):
        super().__init__("Unauthorized access")
