import struct
import io
import assertpy
from streamz import Stream

class RgbTransform(Stream.Transform):
    def __init__(self, meta, options=None):
        super().__init__(options)
        self.meta = meta
        self._buffer = io.BytesIO()
        assertpy.assert_that(self.meta['bpp']).is_equal_to(24).or_is_equal_to(32)
        self._r_pos = self.meta['red_offset'] // 8
        self._g_pos = self.meta['green_offset'] // 8
        self._b_pos = self.meta['blue_offset'] // 8
        self._a_pos = self.meta['alpha_offset'] // 8
        self._pixel_bytes = self.meta['bpp'] // 8

    def _transform(self, chunk, encoding, done):
        self._buffer.write(chunk)
        source_cursor = 0
        target_cursor = 0
        buffer_data = self._buffer.getvalue()
        buffer_length = len(buffer_data)
        target = io.BytesIO()
        
        while buffer_length - source_cursor >= self._pixel_bytes:
            r = buffer_data[source_cursor + self._r_pos]
            g = buffer_data[source_cursor + self._g_pos]
            b = buffer_data[source_cursor + self._b_pos]
            target.write(struct.pack('BBB', r, g, b))
            source_cursor += self._pixel_bytes
            target_cursor += 3
        
        if target_cursor:
            self.push(target.getvalue()[:target_cursor])
            remaining_buffer = buffer_data[source_cursor:]
            self._buffer.seek(0)
            self._buffer.truncate(0)
            self._buffer.write(remaining_buffer)
        
        done()
