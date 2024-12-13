from .parser import Parser
from .auth import Auth


def read_all(stream, callback):
    parser = Parser(stream)
    result = parser.read_all(stream)
    if callback:
        callback(result)
    return result


def parse_public_key(key_string, callback):
    result = Auth.parse_public_key(key_string)
    if callback:
        callback(result)
    return result
