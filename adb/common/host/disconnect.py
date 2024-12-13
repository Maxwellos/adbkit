from adb.command import Command
from adb.protocol import Protocol
import re

class HostDisconnectCommand(Command):
    RE_OK = re.compile(r'^$')

    def execute(self, host, port):
        self._send(f"host:disconnect:{host}:{port}")
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            value = self.parser.readValue()
            if self.RE_OK.match(value):
                return f"{host}:{port}"
            else:
                raise Exception(value)
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
