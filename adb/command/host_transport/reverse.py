from adb.command import Command
from adb.protocol import Protocol

class ReverseCommand(Command):
    def execute(self, remote, local):
        self._send(f"reverse:forward:{remote};{local}")
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
