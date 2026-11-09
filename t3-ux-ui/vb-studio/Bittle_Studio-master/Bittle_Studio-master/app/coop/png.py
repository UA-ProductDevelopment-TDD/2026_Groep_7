"""A minimal PNG writer and reader (zlib and struct only), so camera frames need no imaging library."""
import struct
import zlib

import numpy as np

SIGNATURE = b'\x89PNG\r\n\x1a\n'
COLOUR_TYPES = {1: 0, 3: 2, 4: 6}  # channels -> PNG colour type: grey, RGB, RGBA
CHANNELS = {kind: channels for channels, kind in COLOUR_TYPES.items()}


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)


def encode(array, level=3):
    """PNG bytes of a uint8 array: HxW (grey), HxWx3 (RGB) or HxWx4 (RGBA)."""
    image = np.asarray(array)
    if image.dtype != np.uint8:
        raise ValueError('PNG images must be uint8 arrays')
    if image.ndim == 2:
        image = image[:, :, None]
    if image.ndim != 3 or image.shape[2] not in COLOUR_TYPES or 0 in image.shape:
        raise ValueError('PNG images must be HxW, HxWx3 or HxWx4')
    height, width, channels = image.shape
    rows = np.zeros((height, width * channels + 1), np.uint8)  # first byte of every row is the filter type, 0 = none
    rows[:, 1:] = image.reshape(height, width * channels)
    header = struct.pack('>IIBBBBB', width, height, 8, COLOUR_TYPES[channels], 0, 0, 0)
    data = zlib.compress(rows.tobytes(), level)
    return SIGNATURE + chunk(b'IHDR', header) + chunk(b'IDAT', data) + chunk(b'IEND', b'')


def chunks(data):
    """The (type, payload) chunks of a PNG, each with its checksum verified."""
    if data[:8] != SIGNATURE:
        raise ValueError('This is not a PNG image')
    result, position = [], 8
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError('The PNG image is cut off')
        length, kind = struct.unpack('>I4s', data[position:position + 8])
        payload = data[position + 8:position + 8 + length]
        checksum = data[position + 8 + length:position + 12 + length]
        if len(payload) != length or len(checksum) != 4 or struct.unpack('>I', checksum)[0] != zlib.crc32(kind + payload):
            raise ValueError(f'The PNG chunk {kind.decode("latin-1")} is damaged')
        result.append((kind, payload))
        position += 12 + length
    return result


def unfilter(kind, line, above, step):
    """One row of pixels from its filtered bytes, the row above it already unfiltered and the bytes per pixel."""
    if kind == 0:
        return line
    if kind == 1:  # Sub: each byte adds the one a pixel to its left; a running sum per channel does that for all
        return line.reshape(-1, step).cumsum(axis=0, dtype=np.uint8).reshape(-1)
    if kind == 2:  # Up
        return line + above
    if kind not in (3, 4):
        raise ValueError(f'The PNG row filter {kind} does not exist')
    row, up = bytearray(len(line)), above.tolist()  # Average and Paeth read the byte just decoded: one byte at a time
    for i, byte in enumerate(line.tolist()):
        left = row[i - step] if i >= step else 0
        if kind == 3:  # Average of the byte to the left and the one above
            row[i] = (byte + ((left + up[i]) >> 1)) & 255
        else:  # Paeth: left, above or above-left, whichever is nearest to left + above - above-left
            corner = up[i - step] if i >= step else 0
            to_left, to_up, to_corner = abs(up[i] - corner), abs(left - corner), abs(left + up[i] - 2 * corner)
            nearest = left if to_left <= to_up and to_left <= to_corner else up[i] if to_up <= to_corner else corner
            row[i] = (byte + nearest) & 255
    return np.frombuffer(bytes(row), np.uint8)


def decode(data):
    """Pixels of a PNG as a uint8 array: HxWx3 (RGB), HxWx4 (RGBA) or HxW (grey).

    Only what encode() writes and common cameras and libraries produce: 8 bits per channel, no palette, no
    interlacing. All five row filters are understood.
    """
    parts = chunks(data)
    if not parts or parts[0][0] != b'IHDR' or len(parts[0][1]) != 13:
        raise ValueError('The PNG image has no header')
    width, height, depth, colour, _, _, interlace = struct.unpack('>IIBBBBB', parts[0][1])
    if depth != 8 or colour not in CHANNELS or interlace:
        raise ValueError('Only 8-bit grey, RGB and RGBA PNGs without interlacing can be read')
    channels = CHANNELS[colour]
    stride = width * channels
    try:
        raw = zlib.decompress(b''.join(payload for kind, payload in parts if kind == b'IDAT'))
    except zlib.error:
        raise ValueError('The PNG image data is damaged') from None
    if not width or not height or len(raw) != height * (stride + 1):
        raise ValueError('The PNG image data does not fit its size')
    rows = np.frombuffer(raw, np.uint8).reshape(height, stride + 1)
    image = np.empty((height, stride), np.uint8)
    above = np.zeros(stride, np.uint8)
    for y in range(height):
        above = image[y] = unfilter(int(rows[y, 0]), rows[y, 1:], above, channels)
    return image.reshape(height, width, channels) if channels > 1 else image.reshape(height, width)
