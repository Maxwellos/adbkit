import unittest
import asyncio
from unittest.mock import Mock, patch
from pyadbkit.client import Client, AdbError, DeviceNotFoundError, CommandExecutionError

class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    @patch('pyadbkit.client.Connection')
    async def test_connection(self, mock_connection):
        mock_conn = Mock()
        mock_connection.return_value = mock_conn
        mock_conn.connect = asyncio.coroutine(lambda: None)

        conn = await self.client.connection()
        
        self.assertEqual(conn, mock_conn)
        mock_conn.connect.assert_called_once()

    @patch('pyadbkit.client.Connection')
    @patch('pyadbkit.client.HostVersionCommand')
    async def test_version(self, mock_version_command, mock_connection):
        mock_conn = Mock()
        mock_connection.return_value = mock_conn
        mock_conn.connect = asyncio.coroutine(lambda: None)
        mock_conn.close = asyncio.coroutine(lambda: None)

        mock_command = Mock()
        mock_version_command.return_value = mock_command
        mock_command.execute = asyncio.coroutine(lambda: "1.0.41")

        version = await self.client.version()
        
        self.assertEqual(version, "1.0.41")
        mock_version_command.assert_called_once_with(mock_conn)
        mock_command.execute.assert_called_once()

    # Add more test methods here...

if __name__ == '__main__':
    unittest.main()
