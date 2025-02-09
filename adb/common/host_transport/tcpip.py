import re
from adb.command import Command
from adb.protocol import Protocol

class TcpIpCommand(Command):
    RE_OK = re.compile(r'restarting in')

    def execute(self, port):
        self._send(f"tcpip:{port}")
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            value = self.parser.readAll()
            if self.RE_OK.search(value):
                return port
            else:
                raise Exception(value.strip())
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
