from adb.command import Command
from adb.protocol import Protocol

class RemountCommand(Command):
    def __init__(self, *args, **kwargs):
        super(RemountCommand, self).__init__(*args, **kwargs)

    def execute(self):
        self._send('remount:')
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            return True
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
