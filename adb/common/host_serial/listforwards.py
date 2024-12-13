from adb.command import Command
from adb.protocol import Protocol

class ListForwardsCommand(Command):

    def execute(self, serial):
        self._send(f"host-serial:{serial}:list-forward")
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            value = self.parser.readValue()
            return self._parseForwards(value)
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')

    def _parseForwards(self, value):
        forwards = []
        lines = value.decode().split('\n')
        for line in lines:
            if line:
                parts = line.split()
                serial, local, remote = parts[0], parts[1], parts[2]
                forwards.append({'serial': serial, 'local': local, 'remote': remote})
        return forwards
