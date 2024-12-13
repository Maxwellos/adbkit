class Protocol:
    """
    Protocol class containing ADB protocol constants and utility methods.
    """

    OKAY = b'OKAY'
    FAIL = b'FAIL'
    STAT = b'STAT'
    LIST = b'LIST'
    DENT = b'DENT'
    RECV = b'RECV'
    DATA = b'DATA'
    DONE = b'DONE'
    SEND = b'SEND'
    QUIT = b'QUIT'

    @classmethod
    def decode_length(cls, length: str) -> int:
        """
        Decode a hexadecimal length string to an integer.

        Args:
            length (str): Hexadecimal length string.

        Returns:
            int: Decoded length as an integer.
        """
        return int(length, 16)

    @classmethod
    def encode_length(cls, length: int) -> str:
        """
        Encode an integer length to a 4-character hexadecimal string.

        Args:
            length (int): Length to encode.

        Returns:
            str: Encoded length as a 4-character hexadecimal string.
        """
        return f'{length:04X}'

    @classmethod
    def encode_data(cls, data: bytes) -> bytes:
        """
        Encode data with its length prefix.

        Args:
            data (bytes): Data to encode.

        Returns:
            bytes: Encoded data with length prefix.
        """
        return cls.encode_length(len(data)).encode() + data


