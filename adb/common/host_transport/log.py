from adb.command import Command
from adb.protocol import Protocol

class LogCommand(Command):
    def __init__(self, *args, **kwargs):
        super(LogCommand, self).__init__(*args, **kwargs)

    def execute(self, name):
        self._send(f"log:{name}")
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            return self.parser.raw()
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
