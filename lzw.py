import struct


_MAGIC = b"LZW1"
_CODE = struct.Struct(">H")
_MAX_CODE = (1 << (_CODE.size * 8)) - 1


def lzw_compress(data):
    if not data:
        return b""

    dictionary = {}
    next_code = 256
    current = data[0]
    codes = []

    for symbol in data[1:]:
        candidate = (current, symbol)
        code = dictionary.get(candidate)
        if code is not None:
            current = code
            continue

        codes.append(current)
        if next_code <= _MAX_CODE:
            dictionary[candidate] = next_code
            next_code += 1
        current = symbol

    codes.append(current)
    encoded = bytearray(_MAGIC)
    for code in codes:
        encoded.extend(_CODE.pack(code))
    return bytes(encoded)


def _decompress_codes(codes):
    codes = iter(codes)
    first_code = next(codes, None)
    if first_code is None:
        return b""

    dictionary = {code: bytes([code]) for code in range(256)}
    next_code = 256
    if first_code not in dictionary:
        raise ValueError("LZW stream starts with an invalid code")

    previous = dictionary[first_code]
    result = bytearray(previous)

    for code in codes:
        if code in dictionary:
            current = dictionary[code]
        elif code == next_code and next_code <= _MAX_CODE:
            current = previous + previous[:1]
        else:
            raise ValueError(f"Invalid LZW code: {code}")

        result.extend(current)
        if next_code <= _MAX_CODE:
            dictionary[next_code] = previous + current[:1]
            next_code += 1
        previous = current

    return bytes(result)


def lzw_decompress(compressed_data):
    if not compressed_data:
        return b""

    if isinstance(compressed_data, (bytes, bytearray, memoryview)):
        if len(compressed_data) < len(_MAGIC) or bytes(compressed_data[:4]) != _MAGIC:
            raise ValueError("Compressed data has an invalid LZW signature")
        payload = memoryview(compressed_data)[len(_MAGIC):]
        if len(payload) % _CODE.size:
            raise ValueError("Compressed LZW data ends with an incomplete code")
        codes = (
            _CODE.unpack_from(payload, offset)[0]
            for offset in range(0, len(payload), _CODE.size)
        )
        return _decompress_codes(codes)

    return _decompress_codes(compressed_data)
