from adb.command import Command
from adb.protocol import Protocol

class UninstallCommand(Command):
    def execute(self, pkg):
        self._send(f"shell:pm uninstall {pkg}")
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            match = self.parser.searchLine(r'^(Success|Failure.*|.*Unknown package:.*)$')
            if match[1] == 'Success':
                return True
            else:
                return True
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, "OKAY or FAIL")
