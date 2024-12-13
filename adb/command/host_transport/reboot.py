from adb.command import Command
from adb.protocol import Protocol

class RebootCommand(Command):
    def __init__(self, *args, **kwargs):
        super(RebootCommand, self).__init__(*args, **kwargs)

    def execute(self):
        self._send('reboot:')
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            self.parser.read_all().result()
            return True
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
