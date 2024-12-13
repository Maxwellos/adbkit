import asyncio
import re
from typing import Dict, Any

from ..parser import Parser

class ProcStat(asyncio.Event):
    RE_CPULINE = re.compile(r'^cpu[0-9]+ .*$', re.MULTILINE)
    RE_COLSEP = re.compile(r'\s+')

    def __init__(self, sync):
        super().__init__()
        self.sync = sync
        self.interval = 1000
        self.stats = self._empty_stats()
        self._ignore = {}
        self._timer = None
        self.update()

    async def start(self):
        self._timer = asyncio.create_task(self._update_loop())

    async def _update_loop(self):
        while True:
            await self.update()
            await asyncio.sleep(self.interval / 1000)  # Convert milliseconds to seconds

    async def end(self):
        if self._timer:
            self._timer.cancel()
        await self.sync.end()
        self.sync = None

    async def update(self):
        try:
            out = await Parser(await self.sync.pull('/proc/stat')).read_all()
            await self._parse(out)
        except Exception as err:
            await self._error(err)

    async def _parse(self, out: str):
        stats = self._empty_stats()
        for match in self.RE_CPULINE.finditer(out):
            line = match.group(0)
            cols = self.RE_COLSEP.split(line)
            cpu_type = cols.pop(0)
            if self._ignore.get(cpu_type) == line:
                continue

            total = sum(map(int, cols))
            stats['cpus'][cpu_type] = {
                'line': line,
                'user': int(cols[0]) if len(cols) > 0 else 0,
                'nice': int(cols[1]) if len(cols) > 1 else 0,
                'system': int(cols[2]) if len(cols) > 2 else 0,
                'idle': int(cols[3]) if len(cols) > 3 else 0,
                'iowait': int(cols[4]) if len(cols) > 4 else 0,
                'irq': int(cols[5]) if len(cols) > 5 else 0,
                'softirq': int(cols[6]) if len(cols) > 6 else 0,
                'steal': int(cols[7]) if len(cols) > 7 else 0,
                'guest': int(cols[8]) if len(cols) > 8 else 0,
                'guestnice': int(cols[9]) if len(cols) > 9 else 0,
                'total': total
            }

        await self._set(stats)

    async def _set(self, stats: Dict[str, Any]):
        loads = {}
        found = False
        for cpu_id, cur in stats['cpus'].items():
            old = self.stats['cpus'].get(cpu_id)
            if not old:
                continue

            ticks = cur['total'] - old['total']
            if ticks > 0:
                found = True
                m = 100 / ticks
                loads[cpu_id] = {
                    'user': int(m * (cur['user'] - old['user'])),
                    'nice': int(m * (cur['nice'] - old['nice'])),
                    'system': int(m * (cur['system'] - old['system'])),
                    'idle': int(m * (cur['idle'] - old['idle'])),
                    'iowait': int(m * (cur['iowait'] - old['iowait'])),
                    'irq': int(m * (cur['irq'] - old['irq'])),
                    'softirq': int(m * (cur['softirq'] - old['softirq'])),
                    'steal': int(m * (cur['steal'] - old['steal'])),
                    'guest': int(m * (cur['guest'] - old['guest'])),
                    'guestnice': int(m * (cur['guestnice'] - old['guestnice'])),
                    'total': 100
                }
            else:
                self._ignore[cpu_id] = cur['line']
                del stats['cpus'][cpu_id]

        if found:
            self.set()  # Set the event to notify listeners
            self.clear()  # Clear the event for the next update
            self.load = loads

        self.stats = stats

    async def _error(self, err):
        # In Python, we'll raise an exception instead of emitting an 'error' event
        raise err

    def _empty_stats(self):
        return {
            'cpus': {}
        }
