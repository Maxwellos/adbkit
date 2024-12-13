from adb.command import Command
from adb.protocol import Protocol

class ShellCommand(Command):
    def execute(self, command):
        if isinstance(command, list):
            command = ' '.join(map(self._escape, command))
        self._send(f"shell:{command}")
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            return self.parser.raw()
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
