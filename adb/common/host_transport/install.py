from adb.command import Command
from adb.protocol import Protocol

class InstallCommand(Command):
    def __init__(self, *args, **kwargs):
        super(InstallCommand, self).__init__(*args, **kwargs)

    def execute(self, apk):
        self._send(f"shell:pm install -r {self._escape_compat(apk)}")
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            match = self.parser.search_line(r'^(Success|Failure \[(.*?)\])$').result()
            if match[1] == 'Success':
                return True
            else:
                code = match[2]
                err = Exception(f"{apk} could not be installed [{code}]")
                err.code = code
                raise err
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
