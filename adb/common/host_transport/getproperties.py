import re
from adb.command import Command
from adb.protocol import Protocol

class GetPropertiesCommand(Command):
    RE_KEYVAL = re.compile(r'^\[([\s\S]*?)\]: \[([\s\S]*?)\]\r?$', re.MULTILINE)

    def __init__(self, *args, **kwargs):
        super(GetPropertiesCommand, self).__init__(*args, **kwargs)

    def execute(self):
        self._send('shell:getprop')
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            data = self.parser.read_all().result()
            return self._parse_properties(data.decode('utf-8'))
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')

    def _parse_properties(self, value):
        properties = {}
        for match in self.RE_KEYVAL.finditer(value):
            properties[match.group(1)] = match.group(2)
        return properties
