from adb.command import Command
from adb.protocol import Protocol

class HostTransportCommand(Command):

    def execute(self, serial):
        self._send(f"host:transport:{serial}")
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            return True
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
