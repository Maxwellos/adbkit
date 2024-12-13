from adb.command import Command
from adb.protocol import Protocol
from adb.linetransform import LineTransform

class LogcatCommand(Command):
    def __init__(self, *args, **kwargs):
        super(LogcatCommand, self).__init__(*args, **kwargs)

    def execute(self, options=None):
        if options is None:
            options = {}
        cmd = 'logcat -B *:I 2>/dev/null'
        if options.get('clear'):
            cmd = f"logcat -c 2>/dev/null && {cmd}"
        self._send(f"shell:echo && {cmd}")
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            return self.parser.raw().pipe(LineTransform(auto_detect=True))
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
