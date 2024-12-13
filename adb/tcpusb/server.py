import asyncio
from typing import List
from .socket import Socket

class TcpUsbServer:
    def __init__(self, client, serial, options):
        self.client = client
        self.serial = serial
        self.options = options
        self.connections: List[Socket] = []
        self.server = None
        self.loop = asyncio.get_event_loop()

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_connection, '0.0.0.0', 0
        )
        addr = self.server.sockets[0].getsockname()
        print(f'Serving on {addr}')
        self.loop.create_task(self.server.serve_forever())

    async def handle_connection(self, reader, writer):
        socket = Socket(self.client, self.serial, reader, writer, self.options)
        self.connections.append(socket)
        try:
            await socket.start()  # Start the socket's packet reading process
            await socket.handle()  # If handle() method exists, otherwise remove this line
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            self.connections.remove(socket)
            await socket.end()  # Ensure the socket is properly closed

    def close(self):
        if self.server:
            self.server.close()
