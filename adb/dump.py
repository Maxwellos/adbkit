import os

if 'ADBKIT_DUMP' in os.environ:
    out = open('adbkit.dump', 'wb')

    def process_chunk(chunk):
        out.write(chunk)
        return chunk
else:
    def process_chunk(chunk):
        return chunk
