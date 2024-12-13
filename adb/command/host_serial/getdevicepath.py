from adb.command import Command
from adb.protocol import Protocol

class GetDevicePathCommand(Command):

    def execute(self, serial):
        self._send(f"host-serial:{serial}:get-devpath")
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            value = self.parser.readValue()
            return value.decode()
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
