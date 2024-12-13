import re
from adb.command import Command
from adb.protocol import Protocol

class GetPackagesCommand(Command):
    RE_PACKAGE = re.compile(r'^package:(.*?)\r?$', re.MULTILINE)

    def __init__(self, *args, **kwargs):
        super(GetPackagesCommand, self).__init__(*args, **kwargs)

    def execute(self):
        self._send('shell:pm list packages 2>/dev/null')
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            data = self.parser.read_all().result()
            return self._parse_packages(data.decode('utf-8'))
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')

    def _parse_packages(self, value):
        packages = []
        for match in self.RE_PACKAGE.finditer(value):
            packages.append(match.group(1))
        return packages
