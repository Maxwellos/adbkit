from adb.command import Command
from adb.protocol import Protocol
from adb.parser import Promise, TimeoutError

class MonkeyCommand(Command):
    def __init__(self, *args, **kwargs):
        super(MonkeyCommand, self).__init__(*args, **kwargs)

    def execute(self, port):
        self._send(f"shell:EXTERNAL_STORAGE=/data/local/tmp monkey --port {port} -v")
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            try:
                self.parser.search_line(r'^:Monkey:').timeout(1000).result()
                return self.parser.raw()
            except TimeoutError:
                return self.parser.raw()
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
