import io
import struct
from threading import Event
from .packet import Packet

class PacketReader:
    """
    PacketReader 类用于从流中读取和解析 ADB 协议数据包。
    
    它实现了以下功能：
    1. 从输入流中读取数据。
    2. 解析数据包头部和主体。
    3. 验证数据包的校验和和魔术值。
    4. 发出事件通知数据包的到达或错误的发生。

    主要方法：
    - _try_read: 尝试从流中读取和解析数据包。
    - _append_chunk: 将新的数据块追加到缓冲区。
    - _consume: 从缓冲区中消费指定长度的数据。

    事件：
    - packet: 当完整的数据包被成功解析时触发。
    - error: 当发生错误（如校验和错误或魔术值错误）时触发。
    - end: 当输入流结束时触发。
    """

    def __init__(self, stream):
        self.stream = stream
        self.in_body = False
        self.buffer = bytearray()
        self.packet = None
        self.packet_event = Event()
        self.error_event = Event()
        self.end_event = Event()

    def read_packets(self):
        while True:
            self._try_read()
            if self.end_event.is_set():
                break
            if self.error_event.is_set():
                raise PacketReaderError("An error occurred while reading packets")
            if self.packet_event.is_set():
                yield self.packet
                self.packet_event.clear()

    def _try_read(self):
        while self._append_chunk():
            while self.buffer:
                if self.in_body:
                    if len(self.buffer) < self.packet.length:
                        break
                    self.packet.data = self._consume(self.packet.length)
                    if not self.packet.verify_checksum():
                        self.error_event.set()
                        raise ChecksumError(self.packet)
                    self.packet_event.set()
                    self.in_body = False
                else:
                    if len(self.buffer) < 24:
                        break
                    header = self._consume(24)
                    self.packet = Packet(*struct.unpack('<IIIIII', header), bytearray())
                    if not self.packet.verify_magic():
                        self.error_event.set()
                        raise MagicError(self.packet)
                    if self.packet.length == 0:
                        self.packet_event.set()
                    else:
                        self.in_body = True

    def _append_chunk(self):
        chunk = self.stream.read(4096)
        if chunk:
            self.buffer.extend(chunk)
            return True
        else:
            self.end_event.set()
            return False

    def _consume(self, length):
        chunk = self.buffer[:length]
        del self.buffer[:length]
        return chunk


class PacketReaderError(Exception):
    """基础的 PacketReader 错误类"""
    pass


class ChecksumError(PacketReaderError):
    """当数据包校验和不匹配时抛出"""

    def __init__(self, packet):
        self.packet = packet
        super().__init__("Checksum mismatch")


class MagicError(PacketReaderError):
    """当数据包魔术值不匹配时抛出"""

    def __init__(self, packet):
        self.packet = packet
        super().__init__("Magic value mismatch")
