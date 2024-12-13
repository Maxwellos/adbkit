from adb.common.host.devices import HostDevicesCommand
from adb.protocol import Protocol
from adb.tracker import Tracker

class HostTrackDevicesCommand(HostDevicesCommand):

    def execute(self):
        self._send('host:track-devices')
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            return Tracker(self)
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')
