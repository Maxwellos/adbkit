from .client import Client
from .auth import Auth
from .connection import Connection

__all__ = ['Client', 'Auth', 'Connection']


import os

from .adb.client import Client
from .adb.keycode import Keycode
from .adb.util import util


class Adb:
    @staticmethod
    def create_client(options=None):
        if options is None:
            options = {}
        
        options['host'] = options.get('host', os.environ.get('ADB_HOST'))
        options['port'] = options.get('port', os.environ.get('ADB_PORT'))

        print("options", options)
        return Client(options)


Adb.Keycode = Keycode
Adb.util = util