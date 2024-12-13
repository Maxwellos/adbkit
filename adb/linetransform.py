import io

class LineTransform(io.BufferedIOBase):
    def __init__(self, options=None):
        super().__init__()
        if options is None:
            options = {}
        self.savedR = None
        self.autoDetect = options.get('autoDetect', False)
        self.transformNeeded = True
        self.skipBytes = 0

    @staticmethod
    def _null_transform(chunk):
        return chunk

    def _transform(self, chunk):
        if self.autoDetect:
            if chunk[0] == 0x0a:
                self.transform_needed = False
                self.skipBytes = 1
            else:
                self.skipBytes = 2
            self.autoDetect = False

        if self.skipBytes:
            skip = min(len(chunk), self.skipBytes)
            chunk = chunk[skip:]
            self.skipBytes -= skip

        if not chunk:
            return b''

        if not self.transform_needed:
            return self._null_transform(chunk)

        result = bytearray()
        lo = 0
        hi = 0

        if self.savedR:
            if chunk[0] != 0x0a:
                result.extend(self.savedR)
            self.savedR = None

        last = len(chunk) - 1
        while hi <= last:
            if chunk[hi] == 0x0d:
                if hi == last:
                    self.savedR = chunk[last:last+1]
                    break
                elif chunk[hi + 1] == 0x0a:
                    result.extend(chunk[lo:hi])
                    lo = hi + 1
            hi += 1

        if hi != lo:
            result.extend(chunk[lo:hi])

        return bytes(result)

    def read(self, size=-1):
        chunk = super().read(size)
        if chunk:
            return self._transform(chunk)
        return chunk

    def readline(self, size=-1):
        line = super().readline(size)
        if line:
            return self._transform(line)
        return line

    def close(self):
        if self.savedR:
            self.write(self.savedR)
        super().close()
