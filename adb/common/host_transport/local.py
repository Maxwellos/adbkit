from adb.command import Command
from adb.protocol import Protocol

class LocalCommand(Command):
    def __init__(self, *args, **kwargs):
        super(LocalCommand, self).__init__(*args, **kwargs)

    def execute(self, path):
        self._send(path if ':' in path else f"localfilesystem:{path}")
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            return self.parser.raw()
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
