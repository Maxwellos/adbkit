import argparse
import asyncio
from .client import Client

async def list_devices(client):
    devices = await client.devices()
    print("Connected devices:")
    for device in devices:
        print(f"  {device['serial']} - {device.get('product', 'Unknown')}")

async def shell_command(client, serial, command):
    result = await client.shell(serial, command)
    print(result)

async def install_apk(client, serial, apk_path):
    await client.install(serial, apk_path)
    print(f"Successfully installed {apk_path}")

async def main_async():
    parser = argparse.ArgumentParser(description="PyADBKit CLI")
    parser.add_argument("--serial", help="Device serial number")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List devices command
    subparsers.add_parser("devices", help="List connected devices")

    # Shell command
    shell_parser = subparsers.add_parser("shell", help="Run a shell command")
    shell_parser.add_argument("shell_command", help="Shell command to run")

    # Install APK command
    install_parser = subparsers.add_parser("install", help="Install an APK")
    install_parser.add_argument("apk_path", help="Path to the APK file")

    args = parser.parse_args()

    client = Client()

    if args.command == "devices":
        await list_devices(client)
    elif args.command == "shell":
        if not args.serial:
            print("Error: --serial is required for shell command")
            return
        await shell_command(client, args.serial, args.shell_command)
    elif args.command == "install":
        if not args.serial:
            print("Error: --serial is required for install command")
            return
        await install_apk(client, args.serial, args.apk_path)

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
