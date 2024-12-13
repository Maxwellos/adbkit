from adb.command import Command
from adb.protocol import Protocol

class HostDevicesWithPathsCommand(Command):

    def execute(self):
        self._send('host:devices-l')
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            return self._readDevices()
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')

    def _readDevices(self):
        value = self.parser.readValue()
        return self._parseDevices(value)

    def _parseDevices(self, value):
        devices = []
        if not value:
            return devices
        lines = value.decode('ascii').split('\n')
        for line in lines:
            if line:
                parts = line.split()
                id, type, path = parts[0], parts[1], parts[2]
                devices.append({'id': id, 'type': type, 'path': path})
        return devices
