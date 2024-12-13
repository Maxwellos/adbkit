from adb.command.host_transport.startactivity import StartActivityCommand

class StartServiceCommand(StartActivityCommand):
    def execute(self, options):
        args = self._intentArgs(options)
        if 'user' in options:
            args.append('--user')
            args.append(self._escape(options['user']))
        return self._run('startservice', args)
