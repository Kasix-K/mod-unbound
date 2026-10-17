"""
Read-only MPQ archive reader (the WoW 3.3.5 client's data archives), for tools/fetch_assets.py.

Supports what WotLK-era archives use: encrypted hash and block tables, zlib (0x02) or bzip2 (0x10)
compressed sectors, single-unit files, encrypted files with or without a fixed key. Not supported (the file is
reported as unreadable): other compressions (PKWARE implode, LZMA, sparse), patch files, MPQ format 4 tables.

    archive = MpqArchive(path)
    archive.names()            # the archive's (listfile), if it has one
    archive.read(name)         # the file's bytes, or None if it isn't in the archive
"""
import bz2
import struct
import zlib

_CRYPT = [0] * 1280
_seed = 0x00100001
for _i in range(256):
    _idx = _i
    for _ in range(5):
        _seed = (_seed * 125 + 3) % 0x2AAAAB
        _t1 = (_seed & 0xFFFF) << 16
        _seed = (_seed * 125 + 3) % 0x2AAAAB
        _CRYPT[_idx] = _t1 | (_seed & 0xFFFF)
        _idx += 256

HASH_OFFSET, HASH_A, HASH_B, HASH_KEY = 0, 1, 2, 3
FLAG_COMPRESS, FLAG_ENCRYPTED, FLAG_FIX_KEY, FLAG_SINGLE_UNIT = 0x200, 0x10000, 0x20000, 0x1000000


def hash_string(text, kind):
    seed1, seed2 = 0x7FED7FED, 0xEEEEEEEE
    for ch in text.upper().replace('/', '\\'):
        c = ord(ch)
        seed1 = _CRYPT[(kind << 8) + c] ^ ((seed1 + seed2) & 0xFFFFFFFF)
        seed2 = (c + seed1 + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
    return seed1


def decrypt(data, key):
    out = bytearray()
    seed = 0xEEEEEEEE
    for (v,) in struct.iter_unpack('<I', data[:len(data) // 4 * 4]):
        seed = (seed + _CRYPT[0x400 + (key & 0xFF)]) & 0xFFFFFFFF
        v ^= (key + seed) & 0xFFFFFFFF
        key = ((((~key) << 0x15) + 0x11111111) | (key >> 0x0B)) & 0xFFFFFFFF
        seed = (v + seed + (seed << 5) + 3) & 0xFFFFFFFF
        out += struct.pack('<I', v)
    return bytes(out) + data[len(data) // 4 * 4:]


def _decompress(chunk):
    if chunk[0] == 0x02:
        return zlib.decompress(chunk[1:])
    if chunk[0] == 0x10:
        return bz2.decompress(chunk[1:])
    raise ValueError(f'unsupported compression {chunk[0]:#x}')


class MpqArchive:
    def __init__(self, path):
        self.path = path
        self._f = open(path, 'rb')
        head = self._f.read(4096)
        self.offset = head.find(b'MPQ\x1a')
        if self.offset < 0:
            raise ValueError(f'{path}: no MPQ header')
        self._f.seek(self.offset)
        _, _, _, _, shift, htpos, btpos, hcount, bcount = struct.unpack('<4sIIHHIIII', self._f.read(32))
        self.sector = 512 << shift
        self._f.seek(self.offset + htpos)
        self._hash = decrypt(self._f.read(hcount * 16), hash_string('(hash table)', HASH_KEY))
        self._f.seek(self.offset + btpos)
        self._block = decrypt(self._f.read(bcount * 16), hash_string('(block table)', HASH_KEY))
        self._hcount = hcount

    def close(self):
        self._f.close()

    def _find(self, name):
        a, b = hash_string(name, HASH_A), hash_string(name, HASH_B)
        start = hash_string(name, HASH_OFFSET) % self._hcount
        for i in range(self._hcount):
            ha, hb, _, _, block = struct.unpack_from('<IIHHI', self._hash, ((start + i) % self._hcount) * 16)
            if block == 0xFFFFFFFF:
                return None
            if ha == a and hb == b and block < 0xFFFFFFFE:
                return block
        return None

    def read(self, name):
        block = self._find(name)
        if block is None:
            return None
        pos, csize, fsize, flags = struct.unpack_from('<IIII', self._block, block * 16)
        self._f.seek(self.offset + pos)
        raw = self._f.read(csize)
        key = None
        if flags & FLAG_ENCRYPTED:
            key = hash_string(name.replace('/', '\\').split('\\')[-1], HASH_KEY)
            if flags & FLAG_FIX_KEY:
                key = ((key + pos) ^ fsize) & 0xFFFFFFFF
        compressed = bool(flags & FLAG_COMPRESS)
        if flags & FLAG_SINGLE_UNIT:
            data = decrypt(raw, key) if key is not None else raw
            return _decompress(data) if compressed and csize < fsize else data
        if not compressed:
            if key is None:
                return raw[:fsize]
            return b''.join(decrypt(raw[i:i + self.sector], (key + n) & 0xFFFFFFFF)
                            for n, i in enumerate(range(0, fsize, self.sector)))
        count = (fsize + self.sector - 1) // self.sector
        table = raw[:(count + 1) * 4]
        if key is not None:
            table = decrypt(table, (key - 1) & 0xFFFFFFFF)
        offsets = struct.unpack(f'<{count + 1}I', table)
        out = bytearray()
        for n in range(count):
            chunk = raw[offsets[n]:offsets[n + 1]]
            if key is not None:
                chunk = decrypt(chunk, (key + n) & 0xFFFFFFFF)
            want = min(self.sector, fsize - n * self.sector)
            out += _decompress(chunk) if len(chunk) < want else chunk
        return bytes(out)

    def names(self):
        data = self.read('(listfile)')
        if not data:
            return []
        return [n for n in data.decode('latin-1').replace('\r', '').split('\n') if n]
