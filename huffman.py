import struct
from collections import Counter
from heapq import heappop, heappush

from bitstream import BitReader, BitWriter


_MAGIC = b"HUF1"
_HEADER = struct.Struct(">4sH")
_FREQUENCY = struct.Struct(">BQ")
_BIT_COUNT = struct.Struct(">Q")


class Node:
    def __init__(self, symbol=None, frequency=0, left=None, right=None):
        self.symbol = symbol
        self.frequency = frequency
        self.left = left
        self.right = right


def count_frequencies(data):
    return Counter(data)


def build_huffman_tree(frequencies):
    if not frequencies:
        return None

    heap = []
    counter = 0

    for symbol, frequency in sorted(frequencies.items()):
        if not 0 <= symbol <= 255 or frequency <= 0:
            raise ValueError("Huffman symbols and frequencies are invalid")
        heappush(heap, (frequency, counter, Node(symbol, frequency)))
        counter += 1

    while len(heap) > 1:
        left_frequency, _, left = heappop(heap)
        right_frequency, _, right = heappop(heap)
        parent = Node(
            frequency=left_frequency + right_frequency,
            left=left,
            right=right,
        )
        heappush(heap, (parent.frequency, counter, parent))
        counter += 1

    return heappop(heap)[2]


def build_codes(root):
    codes = {}

    def traverse(node, code):
        if node is None:
            return
        if node.symbol is not None:
            codes[node.symbol] = code or "0"
            return
        traverse(node.left, code + "0")
        traverse(node.right, code + "1")

    traverse(root, "")
    return codes


def huffman_compress(data):
    if not data:
        return b""

    frequencies = count_frequencies(data)
    codes = build_codes(build_huffman_tree(frequencies))
    useful_bits = sum(frequencies[symbol] * len(code) for symbol, code in codes.items())

    writer = BitWriter()
    for symbol in data:
        writer.write_bits(0 if bit == "0" else 1 for bit in codes[symbol])

    header = bytearray(_HEADER.pack(_MAGIC, len(frequencies)))
    for symbol, frequency in sorted(frequencies.items()):
        header.extend(_FREQUENCY.pack(symbol, frequency))
    header.extend(_BIT_COUNT.pack(useful_bits))
    return bytes(header) + writer.get_bytes()


def huffman_decompress(compressed_data):
    if not compressed_data:
        return b""

    if len(compressed_data) < _HEADER.size:
        raise ValueError("Compressed Huffman data has a truncated header")

    magic, unique_count = _HEADER.unpack_from(compressed_data)
    if magic != _MAGIC:
        raise ValueError("Compressed data has an invalid Huffman signature")
    if unique_count == 0 or unique_count > 256:
        raise ValueError("Compressed Huffman data has an invalid symbol count")

    offset = _HEADER.size
    expected_header_size = offset + unique_count * _FREQUENCY.size + _BIT_COUNT.size
    if len(compressed_data) < expected_header_size:
        raise ValueError("Compressed Huffman data has a truncated frequency table")

    frequencies = {}
    for _ in range(unique_count):
        symbol, frequency = _FREQUENCY.unpack_from(compressed_data, offset)
        offset += _FREQUENCY.size
        if symbol in frequencies or frequency == 0:
            raise ValueError("Compressed Huffman frequency table is invalid")
        frequencies[symbol] = frequency

    useful_bits = _BIT_COUNT.unpack_from(compressed_data, offset)[0]
    offset += _BIT_COUNT.size
    payload = compressed_data[offset:]
    if len(payload) != (useful_bits + 7) // 8:
        raise ValueError("Compressed Huffman payload length is invalid")
    if sum(frequencies.values()) == 0:
        raise ValueError("Compressed Huffman data contains no symbols")

    root = build_huffman_tree(frequencies)
    if root.symbol is not None:
        if useful_bits != frequencies[root.symbol]:
            raise ValueError("Compressed Huffman bit count is invalid")
        reader = BitReader(payload)
        if any(reader.read_bit() != 0 for _ in range(useful_bits)):
            raise ValueError("Single-symbol Huffman payload contains invalid bits")
        return bytes([root.symbol]) * frequencies[root.symbol]

    reader = BitReader(payload)
    result = bytearray()
    node = root

    for _ in range(useful_bits):
        node = node.left if reader.read_bit() == 0 else node.right
        if node is None:
            raise ValueError("Compressed Huffman payload contains an invalid code")
        if node.symbol is not None:
            result.append(node.symbol)
            node = root

    if node is not root or len(result) != sum(frequencies.values()):
        raise ValueError("Compressed Huffman payload does not match its frequency table")
    return bytes(result)
