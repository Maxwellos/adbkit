from adb.command import Command
from adb.protocol import Protocol

class ClearCommand(Command):
    def __init__(self, *args, **kwargs):
        super(ClearCommand, self).__init__(*args, **kwargs)

    def execute(self, pkg):
        self._send(f"shell:pm clear {pkg}")
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            result = self.parser.search_line(r'^(Success|Failed)$').result()
            self.parser.end()
            if result[0] == 'Success':
                return True
            elif result[0] == 'Failed':
                raise Exception(f"Package '{pkg}' could not be cleared")
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
