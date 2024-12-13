from adb.command import Command
from adb.protocol import Protocol

class TcpCommand(Command):
    def execute(self, port, host=None):
        self._send(f"tcp:{port}" + (f":{host}" if host else ''))
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            return self.parser.raw()
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
