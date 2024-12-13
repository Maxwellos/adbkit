from adb.command import Command
from adb.protocol import Protocol

class WaitBootCompleteCommand(Command):
    def execute(self):
        self._send('shell:while getprop sys.boot_completed 2>/dev/null; do sleep 1; done')
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            try:
                self.parser.searchLine(r'^1$')
                return True
            finally:
                self.parser.end()
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
