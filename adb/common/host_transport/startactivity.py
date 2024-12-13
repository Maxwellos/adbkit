import re
from adb.command import Command
from adb.protocol import Protocol
from adb.parser import Parser, PrematureEOFError

class StartActivityCommand(Command):
    RE_ERROR = re.compile(r'^Error: (.*)$')
    EXTRA_TYPES = {
        'string': 's',
        'null': 'sn',
        'bool': 'z',
        'int': 'i',
        'long': 'l',
        'float': 'l',
        'uri': 'u',
        'component': 'cn'
    }

    def execute(self, options):
        args = self._intentArgs(options)
        if options.get('debug'):
            args.append('-D')
        if options.get('wait'):
            args.append('-W')
        if 'user' in options:
            args.append('--user')
            args.append(self._escape(options['user']))
        return self._run('start', args)

    def _run(self, command, args):
        self._send(f"shell:am {command} {' '.join(args)}")
        reply = self.parser.readAscii(4)
        if reply == Protocol.OKAY:
            try:
                match = self.parser.searchLine(self.RE_ERROR)
                raise Exception(match[1])
            except PrematureEOFError:
                return True
            finally:
                self.parser.end()
        elif reply == Protocol.FAIL:
            return self.parser.readError()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')

    def _intentArgs(self, options):
        args = []
        if 'extras' in options:
            args.extend(self._formatExtras(options['extras']))
        if 'action' in options:
            args.extend(['-a', self._escape(options['action'])])
        if 'data' in options:
            args.extend(['-d', self._escape(options['data'])])
        if 'mimeType' in options:
            args.extend(['-t', self._escape(options['mimeType'])])
        if 'category' in options:
            if isinstance(options['category'], list):
                for category in options['category']:
                    args.extend(['-c', self._escape(category)])
            else:
                args.extend(['-c', self._escape(options['category'])])
        if 'component' in options:
            args.extend(['-n', self._escape(options['component'])])
        if 'flags' in options:
            args.extend(['-f', self._escape(options['flags'])])
        return args

    def _formatExtras(self, extras):
        if not extras:
            return []
        if isinstance(extras, list):
            return [self._formatLongExtra(extra) for extra in extras]
        else:
            return [self._formatShortExtra(key, value) for key, value in extras.items()]

    def _formatShortExtra(self, key, value):
        sugared = {'key': key}
        if value is None:
            sugared['type'] = 'null'
        elif isinstance(value, list):
            raise Exception(f"Refusing to format array value '{key}' using short syntax; empty array would cause unpredictable results due to unknown type. Please use long syntax instead.")
        else:
            if isinstance(value, str):
                sugared['type'] = 'string'
                sugared['value'] = value
            elif isinstance(value, bool):
                sugared['type'] = 'bool'
                sugared['value'] = value
            elif isinstance(value, int):
                sugared['type'] = 'int'
                sugared['value'] = value
            elif isinstance(value, dict):
                sugared = value
                sugared['key'] = key
        return self._formatLongExtra(sugared)

    def _formatLongExtra(self, extra):
        args = []
        if not extra.get('type'):
            extra['type'] = 'string'
        type_ = self.EXTRA_TYPES.get(extra['type'])
        if not type_:
            raise Exception(f"Unsupported type '{extra['type']}' for extra '{extra['key']}'")
        if extra['type'] == 'null':
            args.extend([f"--e{type_}", self._escape(extra['key'])])
        elif isinstance(extra['value'], list):
            args.extend([f"--e{type_}a", self._escape(extra['key']), self._escape(','.join(extra['value']))])
        else:
            args.extend([f"--e{type_}", self._escape(extra['key']), self._escape(extra['value'])])
        return args
