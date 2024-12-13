from adb.command import Command
from adb.protocol import Protocol
from adb.parser import Parser, PrematureEOFError
from adb.linetransform import LineTransform

class ScreencapCommand(Command):
    def execute(self):
        self._send('shell:echo && screencap -p 2>/dev/null')
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            try:
                transform = LineTransform(autoDetect=True)
                chunk = self.parser.readBytes(1)
                transform.write(chunk)
                return self.parser.raw().pipe(transform)
            except PrematureEOFError:
                raise Exception('No support for the screencap common')
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
