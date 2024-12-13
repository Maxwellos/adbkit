from adb.command import Command
from adb.protocol import Protocol
from adb.parser import PrematureEOFError

class IsInstalledCommand(Command):
    def __init__(self, *args, **kwargs):
        super(IsInstalledCommand, self).__init__(*args, **kwargs)

    def execute(self, pkg):
        self._send(f"shell:pm path {pkg} 2>/dev/null")
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            try:
                reply = self.parser.read_ascii(8).result()
                if reply == 'package:':
                    return True
                else:
                    return self.parser.unexpected(reply, "'package:'")
            except PrematureEOFError:
                return False
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
