import random

from huffman import huffman_compress, huffman_decompress
from lzw import lzw_compress, lzw_decompress


def run_tests():
    rng = random.Random(42)
    test_data = [
        b"",
        b"A",
        b"AAAA",
        b"BANANA",
        b"ABABABAB",
        bytes(range(256)),
        bytes(range(256)) * 4,
        bytes(rng.randrange(256) for _ in range(10_000)),
    ]
    algorithms = (
        ("Huffman", huffman_compress, huffman_decompress),
        ("LZW", lzw_compress, lzw_decompress),
    )

    for data in test_data:
        for name, compress, decompress in algorithms:
            compressed = compress(data)
            restored = decompress(compressed)
            if restored != data:
                raise AssertionError(
                    f"{name} round-trip failed for input of {len(data)} bytes"
                )
            print(
                f"{name}: {len(data)} bytes -> {len(compressed)} bytes; "
                "round-trip passed"
            )


if __name__ == "__main__":
    run_tests()
