from adb.command import Command
from adb.protocol import Protocol

class ForwardCommand(Command):

    def execute(self, serial, local, remote):
        self._send(f"host-serial:{serial}:forward:{local};{remote}")
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            reply = self.parser.readAscii(4)
            if reply == Protocol.OKAY:
                return True
            elif reply == Protocol.FAIL:
                return self.parser.readError()
            else:
                return self.parser.unexpected(reply, 'OKAY or FAIL')
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
