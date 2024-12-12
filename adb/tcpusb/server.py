import asyncio
from typing import List, Any
from .socket import Socket

class Server:
    """
    Server 类实现了一个异步网络服务器，用于管理 ADB 连接。

    这个类使用 asyncio 来处理异步事件和网络操作。

    属性:
        client: ADB 客户端实例。
        serial: 设备序列号。
        options: 服务器配置选项。
        connections (List[Socket]): 当前活动的连接列表。
        server (asyncio.Server): asyncio 服务器实例。
    """

    def __init__(self, client: Any, serial: str, options: dict):
        """
        初始化 Server 实例。

        参数:
            client: ADB 客户端实例。
            serial (str): 设备序列号。
            options (dict): 服务器配置选项。
        """
        self.client = client
        self.serial = serial
        self.options = options
        self.connections: List[Socket] = []
        self.server: asyncio.Server = None
        self.loop = asyncio.get_event_loop()

    async def start_server(self, host: str, port: int):
        """
        启动服务器并开始监听连接。

        参数:
            host (str): 要监听的主机地址。
            port (int): 要监听的端口号。
        """
        self.server = await asyncio.start_server(
            self._handle_connection, host, port
        )
        addr = self.server.sockets[0].getsockname()
        print(f'Serving on {addr}')

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        处理新的客户端连接。

        参数:
            reader (asyncio.StreamReader): 用于读取客户端数据的流。
            writer (asyncio.StreamWriter): 用于向客户端写入数据的流。
        """
        socket = Socket(self.client, self.serial, (reader, writer), self.options)
        self.connections.append(socket)
        try:
            await socket.handle()
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            self.connections.remove(socket)
            writer.close()
            await writer.wait_closed()

    async def close(self):
        """
        关闭服务器和所有活动连接。
        """
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        for conn in self.connections:
            await conn.close()
        self.connections.clear()

    def __del__(self):
        """
        确保在对象被销毁时关闭服务器。
        """
        if self.server:
            self.loop.run_until_complete(self.close())

# 示例用法
async def main():
    server = Server(None, "device_serial", {})
    await server.start_server('127.0.0.1', 8888)
    try:
        await asyncio.Future()  # 运行直到被取消
    finally:
        await server.close()

if __name__ == "__main__":
    asyncio.run(main())
