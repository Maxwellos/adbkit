from adb.command import Command
from adb.protocol import Protocol

class ListReversesCommand(Command):
    def __init__(self, *args, **kwargs):
        super(ListReversesCommand, self).__init__(*args, **kwargs)

    def execute(self):
        self._send("reverse:list-forward")
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            value = self.parser.read_value().result()
            return self._parse_reverses(value.decode('utf-8'))
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')

    def _parse_reverses(self, value):
        reverses = []
        for reverse in value.split('\n'):
            if reverse:
                serial, remote, local = reverse.split()
                reverses.append({
                    'remote': remote,
                    'local': local
                })
        return reverses
