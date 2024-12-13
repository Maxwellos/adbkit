import re
from logging import debug
from typing import Union
from .parser import Parser
from .protocol import Protocol

class Command:
    RE_SQUOT = re.compile(r"'")
    RE_ESCAPE = re.compile(r'([$`\\!"])')

    def __init__(self, connection):
        self.connection = connection
        self.parser = self.connection.parser
        self.protocol = Protocol()

    def execute(self):
        raise NotImplementedError('Missing implementation')

    def _send(self, data):
        encoded = self.protocol.encode_data(data)
        debug(f"Send '{encoded}'")
        self.connection.write(encoded)
        return self

    def _escape(self, arg: Union[int, str]) -> str:
        if isinstance(arg, int):
            return str(arg)
        escaped_arg = self.RE_SQUOT.sub(r"'\"'\"'", str(arg))
        return f"'{escaped_arg}'"

    def _escapeCompat(self, arg: Union[int, str]) -> str:
        if isinstance(arg, int):
            return str(arg)
        escaped_arg = self.RE_ESCAPE.sub(r"\\\1", str(arg))
        return f'"{escaped_arg}"'
