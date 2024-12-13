import asyncio
import base64
import re
import struct
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_der_public_key

class Auth:
    RE = re.compile(r'^((?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?)\0?( .*|)\s*$')

    @staticmethod
    def read_public_key_from_struct(struct_data: bytes, comment: str):
        if not struct_data:
            raise ValueError("Invalid public key")

        offset = 0
        length = struct.unpack_from('<I', struct_data, offset)[0] * 4
        offset += 4

        if len(struct_data) != 4 + 4 + length + length + 4:
            raise ValueError("Invalid public key")

        offset += 4
        n = struct_data[offset:offset+length]
        n = bytes(reversed(n))
        offset += length * 2

        e = struct.unpack_from('<I', struct_data, offset)[0]
        if e not in (3, 65537):
            raise ValueError(f"Invalid exponent {e}, only 3 and 65537 are supported")

        key = load_der_public_key(
            rsa.RSAPublicNumbers(e, int.from_bytes(n, 'big')).public_key().public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

        fingerprint = hashes.Hash(hashes.MD5())
        fingerprint.update(struct_data)
        key.fingerprint = ':'.join(f'{b:02x}' for b in fingerprint.finalize())
        key.comment = comment

        return key

    @classmethod
    async def parse_public_key(cls, buffer: bytes):
        match = cls.RE.match(buffer.decode())
        if match:
            struct_data = base64.b64decode(match.group(1))
            comment = match.group(2).strip()
            return cls.read_public_key_from_struct(struct_data, comment)
        else:
            raise ValueError("Unrecognizable public key format")
