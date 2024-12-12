# PyADBKit

PyADBKit is a Python library for interacting with Android devices using the Android Debug Bridge (ADB) protocol. It provides a high-level, asynchronous API for common ADB operations.

## Features

- Connect to and manage Android devices
- Execute shell commands on devices
- Install and uninstall applications
- Push and pull files
- Reboot devices
- Get device information
- And more...

## Installation

You can install PyADBKit using pip:

```bash
pip install pyadbkit
```

## Requirements

- Python 3.7+
- ADB (Android Debug Bridge) installed and accessible in your system PATH

## Basic Usage

Here's a quick example of how to use PyADBKit:

```python
import asyncio
from pyadbkit import Client

async def main():
    client = Client()
    
    # List connected devices
    devices = await client.devices()
    print(f"Connected devices: {devices}")
    
    # Execute a shell command
    serial = devices[0]['serial']  # Use the first device
    result = await client.shell(serial, 'ls /sdcard')
    print(f"Files in /sdcard: {result}")
    
    # Install an APK
    await client.install(serial, 'path/to/your/app.apk')
    print("App installed successfully")

asyncio.run(main())
```

For more examples, check out the `examples` directory in the repository.

## Development

To set up the development environment:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pyadbkit.git
   cd pyadbkit
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the development dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running Tests

To run the tests:

```bash
pytest tests/
```

### Code Quality Checks

To run code quality checks:

```bash
flake8 src/ tests/
mypy src/
```

### Continuous Integration

This project uses GitHub Actions for continuous integration. The CI pipeline runs automatically on every push and pull request to the main branch. It performs the following checks:

- Runs tests on multiple Python versions (3.7, 3.8, 3.9, 3.10)
- Runs code quality checks using flake8
- Runs type checking using mypy

You can view the CI configuration in the `.github/workflows/ci.yml` file.

## Contributing

Contributions are welcome! Please see the [Contributing Guide](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
