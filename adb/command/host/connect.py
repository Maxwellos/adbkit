from ...connection import ADBConnection

async def connect(connection: ADBConnection, host: str, port: int = 5555):
    await connection.send(f'host:connect:{host}:{port}'.encode())
    await connection.check_okay()
    result = await connection.read_string()
    return result.strip()
