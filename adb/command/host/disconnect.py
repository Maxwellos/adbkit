from ...connection import ADBConnection

async def disconnect(connection: ADBConnection, host: str = None, port: int = None):
    if host and port:
        cmd = f'host:disconnect:{host}:{port}'
    elif host:
        cmd = f'host:disconnect:{host}'
    else:
        cmd = 'host:disconnect:'
    
    await connection.send(cmd.encode())
    await connection.check_okay()
    result = await connection.read_string()
    return result.strip()
