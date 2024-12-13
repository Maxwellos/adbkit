import asyncio
import logging
from typing import Optional, Callable, Any, List, Dict
# import monkey
# import logcat
# debug = logging.debug

from .connection import Connection

from .parser import Parser
from .proc.stat import ProcStat
from .common.host.version import HostVersionCommand
from .common.host.connect import HostConnectCommand
from .common.host.devices import HostDevicesCommand
from .common.host.deviceswithpaths import HostDevicesWithPathsCommand
from .common.host.disconnect import HostDisconnectCommand
from .common.host.trackdevices import HostTrackDevicesCommand
from .common.host.kill import HostKillCommand
from .common.host.transport import HostTransportCommand
from .common.host_transport.clear import ClearCommand
from .common.host_transport.framebuffer import FrameBufferCommand
from .common.host_transport.getfeatures import GetFeaturesCommand
from .common.host_transport.getpackages import GetPackagesCommand
from .common.host_transport.getproperties import GetPropertiesCommand
from .common.host_transport.install import InstallCommand
from .common.host_transport.isinstalled import IsInstalledCommand
from .common.host_transport.listreverses import ListReversesCommand
from .common.host_transport.local import LocalCommand
from .common.host_transport.logcat import LogcatCommand
from .common.host_transport.log import LogCommand
from .common.host_transport.monkey import MonkeyCommand
from .common.host_transport.reboot import RebootCommand
from .common.host_transport.remount import RemountCommand
from .common.host_transport.root import RootCommand
from .common.host_transport.reverse import ReverseCommand
from .common.host_transport.screencap import ScreencapCommand
from .common.host_transport.shell import ShellCommand
from .common.host_transport.startactivity import StartActivityCommand
from .common.host_transport.startservice import StartServiceCommand
from .common.host_transport.sync import SyncCommand
from .common.host_transport.tcp import TcpCommand
from .common.host_transport.tcpip import TcpIpCommand
from .common.host_transport.trackjdwp import TrackJdwpCommand
from .common.host_transport.uninstall import UninstallCommand
from .common.host_transport.usb import UsbCommand
from .common.host_transport.waitbootcomplete import WaitBootCompleteCommand
from .common.host_serial.forward import ForwardCommand
from .common.host_serial.getdevicepath import GetDevicePathCommand
from .common.host_serial.getserialno import GetSerialNoCommand
from .common.host_serial.getstate import GetStateCommand
from .common.host_serial.listforwards import ListForwardsCommand
from .common.host_serial.waitfordevice import WaitForDeviceCommand
from .tcpusb.server import TcpUsbServer

class NoUserOptionError(Exception):
    pass

class Client:
    def __init__(self, options: Dict[str, Any] = None):
        self.options = options or {}
        self.options.setdefault('port', 5037)
        self.options.setdefault('bin', 'adb')

    def create_tcp_usb_bridge(self, serial: str, options: Dict[str, Any]) -> TcpUsbServer:
        return TcpUsbServer(self, serial, options)

    async def connection(self) -> Connection:
        conn = Connection(self.options)
        await conn.connect()
        return conn

    async def version(self) -> str:
        conn = await self.connection()
        return await HostVersionCommand(conn).execute()

    async def connect(self, host: str, port: int = 5555) -> str:
        if ':' in host:
            host, port = host.split(':', 1)
            port = int(port)
        conn = await self.connection()
        return await HostConnectCommand(conn).execute(host, port)

    async def disconnect(self, host: str, port: int = 5555) -> str:
        if ':' in host:
            host, port = host.split(':', 1)
            port = int(port)
        conn = await self.connection()
        return await HostDisconnectCommand(conn).execute(host, port)

    async def list_devices(self) -> List[Dict[str, str]]:
        conn = await self.connection()
        return await HostDevicesCommand(conn).execute()

    async def list_devices_with_paths(self) -> List[Dict[str, str]]:
        conn = await self.connection()
        return await HostDevicesWithPathsCommand(conn).execute()

    async def track_devices(self) -> asyncio.StreamReader:
        conn = await self.connection()
        return await HostTrackDevicesCommand(conn).execute()

    async def kill(self) -> str:
        conn = await self.connection()
        return await HostKillCommand(conn).execute()

    async def get_serial_no(self, serial: str) -> str:
        conn = await self.connection()
        return await GetSerialNoCommand(conn).execute(serial)

    async def get_device_path(self, serial: str) -> str:
        conn = await self.connection()
        return await GetDevicePathCommand(conn).execute(serial)

    async def get_state(self, serial: str) -> str:
        conn = await self.connection()
        return await GetStateCommand(conn).execute(serial)

    async def get_properties(self, serial: str) -> Dict[str, str]:
        transport = await self.transport(serial)
        return await GetPropertiesCommand(transport).execute()

    async def get_features(self, serial: str) -> List[str]:
        transport = await self.transport(serial)
        return await GetFeaturesCommand(transport).execute()

    async def get_packages(self, serial: str) -> List[str]:
        transport = await self.transport(serial)
        return await GetPackagesCommand(transport).execute()

    async def get_dhcp_ip_address(self, serial: str, iface: str = 'wlan0') -> str:
        properties = await self.get_properties(serial)
        ip = properties.get(f"dhcp.{iface}.ipaddress")
        if ip:
            return ip
        raise ValueError(f"Unable to find ipaddress for '{iface}'")

    async def forward(self, serial: str, local: str, remote: str) -> str:
        conn = await self.connection()
        return await ForwardCommand(conn).execute(serial, local, remote)

    async def list_forwards(self, serial: str) -> List[Dict[str, str]]:
        conn = await self.connection()
        return await ListForwardsCommand(conn).execute(serial)

    async def reverse(self, serial: str, remote: str, local: str) -> str:
        transport = await self.transport(serial)
        return await ReverseCommand(transport).execute(remote, local)

    async def list_reverses(self, serial: str) -> List[Dict[str, str]]:
        transport = await self.transport(serial)
        return await ListReversesCommand(transport).execute()

    async def transport(self, serial: str) -> Connection:
        conn = await self.connection()
        await HostTransportCommand(conn).execute(serial)
        return conn

    async def shell(self, serial: str, command: str) -> asyncio.StreamReader:
        transport = await self.transport(serial)
        return await ShellCommand(transport).execute(command)

    async def reboot(self, serial: str) -> str:
        transport = await self.transport(serial)
        return await RebootCommand(transport).execute()

    async def remount(self, serial: str) -> str:
        transport = await self.transport(serial)
        return await RemountCommand(transport).execute()

    async def root(self, serial: str) -> str:
        transport = await self.transport(serial)
        return await RootCommand(transport).execute()

    async def track_jdwp(self, serial: str) -> asyncio.StreamReader:
        transport = await self.transport(serial)
        return await TrackJdwpCommand(transport).execute()

    async def framebuffer(self, serial: str, format: str = 'raw') -> Dict[str, Any]:
        transport = await self.transport(serial)
        return await FrameBufferCommand(transport).execute(format)

    async def screencap(self, serial: str) -> bytes:
        transport = await self.transport(serial)
        try:
            return await ScreencapCommand(transport).execute()
        except Exception as err:
            debug(f"Emulating screencap command due to '{err}'")
            return await self.framebuffer(serial, 'png')

    async def open_local(self, serial: str, path: str) -> asyncio.StreamReader:
        transport = await self.transport(serial)
        return await LocalCommand(transport).execute(path)

    async def open_log(self, serial: str, name: str) -> asyncio.StreamReader:
        transport = await self.transport(serial)
        return await LogCommand(transport).execute(name)

    async def open_tcp(self, serial: str, port: int, host: Optional[str] = None) -> asyncio.StreamReader:
        transport = await self.transport(serial)
        return await TcpCommand(transport).execute(port, host)

    async def open_monkey(self, serial: str, port: int = 1080) -> 'adbkit_monkey.Monkey':
        async def try_connect(times):
            try:
                stream = await self.open_tcp(serial, port)
                return await adbkit_monkey.connect_stream(stream)
            except Exception as err:
                if times > 0:
                    debug(f"Monkey can't be reached, trying {times} more times")
                    await asyncio.sleep(0.1)
                    return await try_connect(times - 1)
                raise err

        try:
            return await try_connect(1)
        except Exception:
            transport = await self.transport(serial)
            out = await MonkeyCommand(transport).execute(port)
            monkey = await try_connect(20)
            monkey.once('end', out.close)
            return monkey

    async def open_logcat(self, serial: str, options: Dict[str, Any] = None) -> 'adbkit_logcat.Logcat':
        options = options or {}
        transport = await self.transport(serial)
        stream = await LogcatCommand(transport).execute(options)
        return adbkit_logcat.read_stream(stream, fix_line_feeds=False)

    async def open_proc_stat(self, serial: str) -> ProcStat:
        sync = await self.sync_service(serial)
        return ProcStat(sync)

    async def clear(self, serial: str, pkg: str) -> str:
        transport = await self.transport(serial)
        return await ClearCommand(transport).execute(pkg)

    async def install(self, serial: str, apk: str) -> bool:
        temp = Sync.temp(apk if isinstance(apk, str) else '_stream.apk')
        transfer = await self.push(serial, apk, temp)
        await transfer.wait_for('end')
        return await self.install_remote(serial, temp)

    async def install_remote(self, serial: str, apk: str) -> bool:
        transport = await self.transport(serial)
        await InstallCommand(transport).execute(apk)
        stream = await self.shell(serial, ['rm', '-f', apk])
        await Parser(stream).read_all()
        return True

    async def uninstall(self, serial: str, pkg: str) -> str:
        transport = await self.transport(serial)
        return await UninstallCommand(transport).execute(pkg)

    async def is_installed(self, serial: str, pkg: str) -> bool:
        transport = await self.transport(serial)
        return await IsInstalledCommand(transport).execute(pkg)

    async def start_activity(self, serial: str, options: Dict[str, Any]) -> str:
        transport = await self.transport(serial)
        try:
            return await StartActivityCommand(transport).execute(options)
        except NoUserOptionError:
            options['user'] = None
            return await self.start_activity(serial, options)

    async def start_service(self, serial: str, options: Dict[str, Any]) -> str:
        transport = await self.transport(serial)
        if 'user' not in options and options.get('user') is not None:
            options['user'] = 0
        try:
            return await StartServiceCommand(transport).execute(options)
        except NoUserOptionError:
            options['user'] = None
            return await self.start_service(serial, options)

    async def sync_service(self, serial: str) -> Sync:
        transport = await self.transport(serial)
        return await SyncCommand(transport).execute()

    async def stat(self, serial: str, path: str) -> Dict[str, Any]:
        sync = await self.sync_service(serial)
        try:
            return await sync.stat(path)
        finally:
            await sync.end()

    async def readdir(self, serial: str, path: str) -> List[Dict[str, Any]]:
        sync = await self.sync_service(serial)
        try:
            return await sync.readdir(path)
        finally:
            await sync.end()

    async def pull(self, serial: str, path: str) -> asyncio.StreamReader:
        sync = await self.sync_service(serial)
        stream = await sync.pull(path)
        stream.on('end', sync.end)
        return stream

    async def push(self, serial: str, contents: Any, path: str, mode: Optional[int] = None) -> asyncio.StreamWriter:
        sync = await self.sync_service(serial)
        stream = await sync.push(contents, path, mode)
        stream.on('end', sync.end)
        return stream

    async def tcpip(self, serial: str, port: int = 5555) -> str:
        transport = await self.transport(serial)
        return await TcpIpCommand(transport).execute(port)

    async def usb(self, serial: str) -> str:
        transport = await self.transport(serial)
        return await UsbCommand(transport).execute()

    async def wait_boot_complete(self, serial: str) -> bool:
        transport = await self.transport(serial)
        return await WaitBootCompleteCommand(transport).execute()

    async def wait_for_device(self, serial: str) -> str:
        conn = await self.connection()
        return await WaitForDeviceCommand(conn).execute(serial)


