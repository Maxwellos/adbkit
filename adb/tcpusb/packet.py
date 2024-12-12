import struct

class Packet:
    A_SYNC = 0x434e5953
    A_CNXN = 0x4e584e43
    A_OPEN = 0x4e45504f
    A_OKAY = 0x59414b4f
    A_CLSE = 0x45534c43
    A_WRTE = 0x45545257
    A_AUTH = 0x48545541

    @classmethod
    def checksum(cls, data):
        return sum(data) if data else 0

    @classmethod
    def magic(cls, command):
        return (command ^ 0xffffffff) & 0xffffffff

    @classmethod
    def assemble(cls, command, arg0, arg1, data=None):
        if data:
            chunk = bytearray(24 + len(data))
            struct.pack_into('<IIIIII', chunk, 0, command, arg0, arg1, len(data), cls.checksum(data), cls.magic(command))
            chunk[24:] = data
        else:
            chunk = struct.pack('<IIIIII', command, arg0, arg1, 0, 0, cls.magic(command))
        return chunk

    @staticmethod
    def swap32(n):
        return struct.unpack('>I', struct.pack('<I', n))[0]

    def __init__(self, command, arg0, arg1, length, check, magic, data):
        self.command = command
        self.arg0 = arg0
        self.arg1 = arg1
        self.length = length
        self.check = check
        self.magic = magic
        self.data = data

    def verify_checksum(self):
        return self.check == self.checksum(self.data)

    def verify_magic(self):
        return self.magic == self.magic(self.command)

    def __str__(self):
        command_type = {
            self.A_SYNC: "SYNC",
            self.A_CNXN: "CNXN",
            self.A_OPEN: "OPEN",
            self.A_OKAY: "OKAY",
            self.A_CLSE: "CLSE",
            self.A_WRTE: "WRTE",
            self.A_AUTH: "AUTH"
        }.get(self.command, None)

        if command_type is None:
            raise ValueError(f"Unknown command {self.command}")

        return f"{command_type} arg0={self.arg0} arg1={self.arg1} length={self.length}"
