import asyncio
from typing import List, Dict, Any
from .parser import Parser

class Tracker(asyncio.Event):
    def __init__(self, command):
        super().__init__()
        self.command = command
        self.device_list: List[Dict[str, Any]] = []
        self.device_map: Dict[str, Dict[str, Any]] = {}
        self.reader_task = None

    async def start(self):
        self.reader_task = asyncio.create_task(self.read())
        try:
            await self.reader_task
        except asyncio.CancelledError:
            pass
        except Parser.PrematureEOFError:
            raise ConnectionError('Connection closed')
        except Exception as err:
            self.set()  # Set the event to notify listeners of an error
            raise err
        finally:
            await self.command.parser.end()
            self.set()  # Set the event to notify listeners that tracking has ended

    async def read(self):
        while True:
            try:
                device_list = await self.command._read_devices()
                self.update(device_list)
                await asyncio.sleep(0)  # Yield control to allow other coroutines to run
            except asyncio.CancelledError:
                break

    def update(self, new_list: List[Dict[str, Any]]):
        change_set = {
            'removed': [],
            'changed': [],
            'added': []
        }
        new_map = {}

        for device in new_list:
            old_device = self.device_map.get(device['id'])
            if old_device:
                if old_device['type'] != device['type']:
                    change_set['changed'].append(device)
                    asyncio.create_task(self.notify_listeners('change', device, old_device))
            else:
                change_set['added'].append(device)
                asyncio.create_task(self.notify_listeners('add', device))
            new_map[device['id']] = device

        for device in self.device_list:
            if device['id'] not in new_map:
                change_set['removed'].append(device)
                asyncio.create_task(self.notify_listeners('remove', device))

        asyncio.create_task(self.notify_listeners('change_set', change_set))
        self.device_list = new_list
        self.device_map = new_map

    async def notify_listeners(self, event_type: str, *args):
        # This method would be used to notify listeners of events
        # In a real implementation, you might use a callback mechanism or another event system
        pass

    def end(self):
        if self.reader_task:
            self.reader_task.cancel()

# Ensure this is at the end of the file
__all__ = ['Tracker']
