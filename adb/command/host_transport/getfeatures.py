import re
from adb.command import Command
from adb.protocol import Protocol

class GetFeaturesCommand(Command):
    RE_FEATURE = re.compile(r'^feature:(.*?)(?:=(.*?))?\r?$', re.MULTILINE)

    def __init__(self, *args, **kwargs):
        super(GetFeaturesCommand, self).__init__(*args, **kwargs)

    def execute(self):
        self._send('shell:pm list features 2>/dev/null')
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            data = self.parser.read_all().result()
            return self._parse_features(data.decode('utf-8'))
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')

    def _parse_features(self, value):
        features = {}
        for match in self.RE_FEATURE.finditer(value):
            features[match.group(1)] = match.group(2) or True
        return features
