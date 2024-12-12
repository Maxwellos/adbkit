import asyncio
import logging
from typing import Optional, List, Dict, Any, Union

from .connection import Connection
from .sync import Sync
from .parser import Parser
from .proc.stat import ProcStat
from .tcpusb.server import TcpUsbServer

# Import all command classes here
from .command.host.version import HostVersionCommand
from .command.host.connect import HostConnectCommand
from .command.host.disconnect import HostDisconnectCommand
from .command.host.devices import HostDevicesCommand
from .command.host.deviceswithpaths import HostDevicesWithPathsCommand
from .command.host.trackdevices import HostTrackDevicesCommand
from .command.host.kill import HostKillCommand
from .command.host.transport import HostTransportCommand
from .command.host_serial.getdevicepath import GetDevicePathCommand
from .command.host_serial.getserialno import GetSerialNoCommand
from .command.host_serial.getstate import GetStateCommand
from .command.host_transport.getproperties import GetPropertiesCommand
from .command.host_transport.shell import ShellCommand
from .command.host_transport.reboot import RebootCommand
from .command.host_transport.root import RootCommand
from .command.host_transport.install import InstallCommand
from .command.host_transport.uninstall import UninstallCommand
from .command.host_transport.sync import SyncCommand

logger = logging.getLogger(__name__)

class AdbError(Exception):
    """Base exception for ADB-related errors."""
    pass

class DeviceNotFoundError(AdbError):
    """Exception raised when a device is not found."""
    pass

class CommandExecutionError(AdbError):
    """Exception raised when a command fails to execute."""
    pass

class Client:
    """
    A client for interacting with Android Debug Bridge (ADB).

    This class provides methods for various ADB operations such as connecting to devices,
    executing shell commands, transferring files, and managing applications.
    """

    def __init__(self, options: Dict[str, Any] = None):
        """
        Initialize the ADB client.

        Args:
            options (Dict[str, Any], optional): Configuration options for the client.
        """
        self.options = options or {}
        self.options.setdefault('port', 5037)
        self.options.setdefault('bin', 'adb')

    async def create_tcp_usb_bridge(self, serial: str, options: Dict[str, Any]) -> TcpUsbServer:
        """
        Create a TCP/USB bridge for the specified device.

        Args:
            serial (str): The serial number of the device.
            options (Dict[str, Any]): Options for the TCP/USB bridge.

        Returns:
            TcpUsbServer: The created TCP/USB bridge server.
        """
        return TcpUsbServer(self, serial, options)

    async def connection(self) -> Connection:
        """
        Establish a connection to the ADB server.

        Returns:
            Connection: The established connection.

        Raises:
            AdbError: If the connection cannot be established.
        """
        conn = Connection(self.options)
        try:
            await conn.connect()
            return conn
        except Exception as e:
            await conn.close()
            raise AdbError(f"Failed to establish connection: {str(e)}") from e

    async def version(self) -> str:
        """
        Get the version of the ADB server.

        Returns:
            str: The version string.

        Raises:
            AdbError: If the version cannot be retrieved.
        """
        try:
            async with await self.connection() as conn:
                return await HostVersionCommand(conn).execute()
        except Exception as e:
            raise AdbError(f"Failed to get ADB version: {str(e)}") from e

    async def connect(self, host: str, port: int = 5555) -> str:
        """
        Connect to a device.

        Args:
            host (str): The host address of the device.
            port (int, optional): The port to connect to. Defaults to 5555.

        Returns:
            str: The result of the connection attempt.

        Raises:
            AdbError: If the connection fails.
        """
        if ':' in host:
            host, port = host.split(':', 1)
            port = int(port)
        try:
            async with await self.connection() as conn:
                return await HostConnectCommand(conn).execute(host, port)
        except Exception as e:
            raise AdbError(f"Failed to connect to {host}:{port}: {str(e)}") from e

    async def disconnect(self, host: str, port: int = 5555) -> str:
        """
        Disconnect from a device.

        Args:
            host (str): The host address of the device.
            port (int, optional): The port to disconnect from. Defaults to 5555.

        Returns:
            str: The result of the disconnection attempt.

        Raises:
            AdbError: If the disconnection fails.
        """
        if ':' in host:
            host, port = host.split(':', 1)
            port = int(port)
        try:
            async with await self.connection() as conn:
                return await HostDisconnectCommand(conn).execute(host, port)
        except Exception as e:
            raise AdbError(f"Failed to disconnect from {host}:{port}: {str(e)}") from e

    async def devices(self) -> List[Dict[str, str]]:
        """
        Get a list of connected devices.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing device information.

        Raises:
            AdbError: If the device list cannot be retrieved.
        """
        try:
            async with await self.connection() as conn:
                return await HostDevicesCommand(conn).execute()
        except Exception as e:
            raise AdbError(f"Failed to get device list: {str(e)}") from e

    async def shell(self, serial: str, command: Union[str, List[str]]) -> str:
        """
        Execute a shell command on the device.

        Args:
            serial (str): The serial number of the device.
            command (Union[str, List[str]]): The command to execute.

        Returns:
            str: The output of the command.

        Raises:
            DeviceNotFoundError: If the specified device is not found.
            CommandExecutionError: If the command fails to execute.
        """
        try:
            transport = await self.transport(serial)
            result = await ShellCommand(transport).execute(command)
            return result.decode('utf-8').strip()
        except DeviceNotFoundError:
            raise
        except Exception as e:
            raise CommandExecutionError(f"Failed to execute shell command: {str(e)}") from e

    async def reboot(self, serial: str) -> None:
        """
        Reboot the device.

        Args:
            serial (str): The serial number of the device.

        Raises:
            DeviceNotFoundError: If the specified device is not found.
            AdbError: If the reboot command fails.
        """
        try:
            transport = await self.transport(serial)
            await RebootCommand(transport).execute()
        except DeviceNotFoundError:
            raise
        except Exception as e:
            raise AdbError(f"Failed to reboot device {serial}: {str(e)}") from e

    async def root(self, serial: str) -> None:
        """
        Restart adbd with root permissions.

        Args:
            serial (str): The serial number of the device.

        Raises:
            DeviceNotFoundError: If the specified device is not found.
            AdbError: If the root command fails.
        """
        try:
            transport = await self.transport(serial)
            await RootCommand(transport).execute()
        except DeviceNotFoundError:
            raise
        except Exception as e:
            raise AdbError(f"Failed to restart adbd as root on device {serial}: {str(e)}") from e

    async def install(self, serial: str, apk_path: str) -> None:
        """
        Install an APK on the device.

        Args:
            serial (str): The serial number of the device.
            apk_path (str): The path to the APK file.

        Raises:
            DeviceNotFoundError: If the specified device is not found.
            AdbError: If the installation fails.
        """
        try:
            transport = await self.transport(serial)
            await InstallCommand(transport).execute(apk_path)
        except DeviceNotFoundError:
            raise
        except Exception as e:
            raise AdbError(f"Failed to install APK on device {serial}: {str(e)}") from e

    async def uninstall(self, serial: str, package: str) -> None:
        """
        Uninstall an app from the device.

        Args:
            serial (str): The serial number of the device.
            package (str): The package name of the app to uninstall.

        Raises:
            DeviceNotFoundError: If the specified device is not found.
            AdbError: If the uninstallation fails.
        """
        try:
            transport = await self.transport(serial)
            await UninstallCommand(transport).execute(package)
        except DeviceNotFoundError:
            raise
        except Exception as e:
            raise AdbError(f"Failed to uninstall package {package} from device {serial}: {str(e)}") from e

    async def push(self, serial: str, local: str, remote: str) -> None:
        """
        Push a file or directory to the device.

        Args:
            serial (str): The serial number of the device.
            local (str): The local path of the file or directory to push.
            remote (str): The remote path on the device.

        Raises:
            DeviceNotFoundError: If the specified device is not found.
            AdbError: If the push operation fails.
        """
        try:
            sync = await self.sync_service(serial)
            try:
                await sync.push(local, remote)
            finally:
                await sync.close()
        except DeviceNotFoundError:
            raise
        except Exception as e:
            raise AdbError(f"Failed to push {local} to {remote} on device {serial}: {str(e)}") from e

    async def pull(self, serial: str, remote: str, local: str) -> None:
        """
        Pull a file or directory from the device.

        Args:
            serial (str): The serial number of the device.
            remote (str): The remote path on the device.
            local (str): The local path to save the file or directory.

        Raises:
            DeviceNotFoundError: If the specified device is not found.
            AdbError: If the pull operation fails.
        """
        try:
            sync = await self.sync_service(serial)
            try:
                await sync.pull(remote, local)
            finally:
                await sync.close()
        except DeviceNotFoundError:
            raise
        except Exception as e:
            raise AdbError(f"Failed to pull {remote} to {local} from device {serial}: {str(e)}") from e

    async def sync_service(self, serial: str) -> Sync:
        """
        Start a sync service for file operations.

        Args:
            serial (str): The serial number of the device.

        Returns:
            Sync: The sync service object.

        Raises:
            DeviceNotFoundError: If the specified device is not found.
            AdbError: If the sync service cannot be started.
        """
        try:
            transport = await self.transport(serial)
            return await SyncCommand(transport).execute()
        except DeviceNotFoundError:
            raise
        except Exception as e:
            raise AdbError(f"Failed to start sync service for device {serial}: {str(e)}") from e

    async def transport(self, serial: str) -> Connection:
        """
        Create a transport connection to a specific device.

        Args:
            serial (str): The serial number of the device.

        Returns:
            Connection: The transport connection.

        Raises:
            DeviceNotFoundError: If the specified device is not found.
            AdbError: If the transport connection cannot be established.
        """
        try:
            conn = await self.connection()
            await HostTransportCommand(conn).execute(serial)
            return conn
        except Exception as e:
            if "device not found" in str(e).lower():
                raise DeviceNotFoundError(f"Device with serial {serial} not found") from e
            raise AdbError(f"Failed to create transport for device {serial}: {str(e)}") from e

    @staticmethod
    def _is_no_user_option_error(err: Exception) -> bool:
        """
        Check if the error is related to a missing user option.

        Args:
            err (Exception): The exception to check.

        Returns:
            bool: True if the error is related to a missing user option, False otherwise.
        """
        return '--user' in str(err)

    async def execute_command(self, serial: str, command: str) -> str:
        """
        Execute a custom ADB command on the device.

        Args:
            serial (str): The serial number of the device.
            command (str): The ADB command to execute.

        Returns:
            str: The output of the command.

        Raises:
            DeviceNotFoundError: If the specified device is not found.
            CommandExecutionError: If the command fails to execute.
        """
        try:
            transport = await self.transport(serial)
            result = await ShellCommand(transport).execute(command)
            return result.decode('utf-8').strip()
        except DeviceNotFoundError:
            raise
        except Exception as e:
            raise CommandExecutionError(f"Failed to execute command '{command}': {str(e)}") from e

    async def get_device_info(self, serial: str) -> Dict[str, str]:
        """
        Get detailed information about a device.

        Args:
            serial (str): The serial number of the device.

        Returns:
            Dict[str, str]: A dictionary containing device information.

        Raises:
            DeviceNotFoundError: If the specified device is not found.
            AdbError: If the device information cannot be retrieved.
        """
        try:
            props = await self.get_properties(serial)
            return {
                "serial": serial,
                "model": props.get("ro.product.model", "Unknown"),
                "device": props.get("ro.product.device", "Unknown"),
                "release": props.get("ro.build.version.release", "Unknown"),
                "sdk": props.get("ro.build.version.sdk", "Unknown"),
                "battery": await self.get_battery_level(serial)
            }
        except DeviceNotFoundError:
            raise
        except Exception as e:
            raise AdbError(f"Failed to get device info for {serial}: {str(e)}") from e

    async def get_battery_level(self, serial: str) -> str:
        """
        Get the current battery level of the device.

        Args:
            serial (str): The serial number of the device.

        Returns:
            str: The battery level as a percentage.

        Raises:
            DeviceNotFoundError: If the specified device is not found.
            AdbError: If the battery level cannot be retrieved.
        """
        try:
            result = await self.shell(serial, "dumpsys battery | grep level")
            return result.split(":")[1].strip()
        except DeviceNotFoundError:
            raise
        except Exception as e:
            raise AdbError(f"Failed to get battery level for device {serial}: {str(e)}") from e

# Add more helper classes or functions if needed
