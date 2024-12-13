from adb.command import Command
from adb.protocol import Protocol

class HostVersionCommand(Command):

    def execute(self):
        self._send('host:version')
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            value = self.parser.readValue()
            return self._parseVersion(value)
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self._parseVersion(reply)

    def _parseVersion(self, version):
        return int(version, 16)
