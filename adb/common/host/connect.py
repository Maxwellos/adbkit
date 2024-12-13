import re

from adb.command import Command
from adb.protocol import Protocol

class HostConnectCommand(Command):
    RE_OK = r'connected to|already connected'

    def execute(self, host, port):
        self._send(f"host:connect:{host}:{port}")
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            value = self.parser.readValue()
            if re.search(self.RE_OK, value):
                return f"{host}:{port}"
            else:
                raise Exception(value)
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
