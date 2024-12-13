import asyncio
from adb.command import Command
from adb.protocol import Protocol
from adb.parser import Parser, PrematureEOFError
from asyncio import Event

class TrackJdwpCommand(Command):
    def execute(self):
        self._send('track-jdwp')
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            return self.Tracker(self)
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')

    class Tracker(Event):
        def __init__(self, command):
            super().__init__()
            self.command = command
            self.pids = []
            self.pidMap = {}
            self.reader = asyncio.create_task(self.read())

        async def read(self):
            try:
                while True:
                    list = await self.command.parser.readValue()
                    pids = list.decode().split('\n')
                    if pids[-1] == '':
                        pids.pop()
                    self.update(pids)
            except PrematureEOFError:
                self.set()
            except asyncio.CancelledError:
                self.command.connection.end()
                self.set()
            except Exception as err:
                self.command.connection.end()
                self.set()
                raise err

        def update(self, newList):
            changeSet = {
                'removed': [],
                'added': []
            }
            newMap = {}
            for pid in newList:
                if pid not in self.pidMap:
                    changeSet['added'].append(pid)
                    newMap[pid] = pid
            for pid in self.pids:
                if pid not in newMap:
                    changeSet['removed'].append(pid)
            self.pids = newList
            self.pidMap = newMap
            self.set()

        def end(self):
            self.reader.cancel()
            self.set()
