from adb.command import Command
from adb.protocol import Protocol
from adb.sync import Sync

class SyncCommand(Command):
    def execute(self):
        self._send('sync:')
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            return Sync(self.connection)
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
