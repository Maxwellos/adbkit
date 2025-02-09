import re
from adb.command import Command
from adb.protocol import Protocol

class RootCommand(Command):
    RE_OK = re.compile(r'restarting adbd as root')

    def execute(self):
        self._send('root:')
        reply = self.parser.read_ascii(4)
        if reply == Protocol.OKAY:
            value = self.parser.readAll()
            if self.RE_OK.search(value):
                return True
            else:
                raise Exception(value.strip())
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
