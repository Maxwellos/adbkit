from adb.command import Command
from adb.protocol import Protocol

class WaitForDeviceCommand(Command):

    def execute(self, serial):
        self._send(f"host-serial:{serial}:wait-for-any")
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            reply = self.parser.readAscii(4)
            if reply == Protocol.OKAY:
                return serial
            elif reply == Protocol.FAIL:
                return self.parser.readError()
            else:
                return self.parser.unexpected(reply, 'OKAY or FAIL')
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
