import struct
import subprocess
from adb.command import Command
from adb.protocol import Protocol
from adb.framebuffer.rgbtransform import RgbTransform

class FrameBufferCommand(Command):
    def __init__(self, *args, **kwargs):
        super(FrameBufferCommand, self).__init__(*args, **kwargs)

    def execute(self, format):
        self._send('framebuffer:')
        reply = self.parser.read_ascii(4).result()
        if reply == Protocol.OKAY:
            header = self.parser.read_bytes(52).result()
            meta = self._parse_header(header)
            if format == 'raw':
                stream = self.parser.raw()
                stream.meta = meta
                return stream
            else:
                stream = self._convert(meta, format)
                stream.meta = meta
                return stream
        elif reply == Protocol.FAIL:
            return self.parser.read_error()
        else:
            return self.parser.unexpected(reply, 'OKAY or FAIL')

    def _convert(self, meta, format):
        print(f"Converting raw framebuffer stream into {format.upper()}")
        if meta['format'] not in ['rgb', 'rgba']:
            print(f"Silently transforming '{meta['format']}' into 'rgb' for `gm`")
            transform = RgbTransform(meta)
            meta['format'] = 'rgb'
            raw = self.parser.raw().pipe(transform)
        else:
            raw = self.parser.raw()
        proc = subprocess.Popen(['gm', 'convert', '-size', f"{meta['width']}x{meta['height']}", f"{meta['format']}:-", f"{format}:-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        raw.pipe(proc.stdin)
        return proc.stdout

    def _parse_header(self, header):
        meta = {}
        offset = 0
        meta['version'] = struct.unpack_from('<I', header, offset)[0]
        if meta['version'] == 16:
            raise Exception('Old-style raw images are not supported')
        offset += 4
        meta['bpp'] = struct.unpack_from('<I', header, offset)[0]
        offset += 4
        meta['size'] = struct.unpack_from('<I', header, offset)[0]
        offset += 4
        meta['width'] = struct.unpack_from('<I', header, offset)[0]
        offset += 4
        meta['height'] = struct.unpack_from('<I', header, offset)[0]
        offset += 4
        meta['red_offset'] = struct.unpack_from('<I', header, offset)[0]
        offset += 4
        meta['red_length'] = struct.unpack_from('<I', header, offset)[0]
        offset += 4
        meta['blue_offset'] = struct.unpack_from('<I', header, offset)[0]
        offset += 4
        meta['blue_length'] = struct.unpack_from('<I', header, offset)[0]
        offset += 4
        meta['green_offset'] = struct.unpack_from('<I', header, offset)[0]
        offset += 4
        meta['green_length'] = struct.unpack_from('<I', header, offset)[0]
        offset += 4
        meta['alpha_offset'] = struct.unpack_from('<I', header, offset)[0]
        offset += 4
        meta['alpha_length'] = struct.unpack_from('<I', header, offset)[0]
        meta['format'] = 'bgr' if meta['blue_offset'] == 0 else 'rgb'
        if meta['bpp'] == 32 or meta['alpha_length']:
            meta['format'] += 'a'
        return meta
