class BitWriter:
    def __init__(self):
        self._data = bytearray()
        self._buffer = 0
        self._bit_count = 0

    def write_bit(self, bit):
        if bit not in (0, 1):
            raise ValueError("A bit must be 0 or 1")

        self._buffer = (self._buffer << 1) | bit
        self._bit_count += 1

        if self._bit_count == 8:
            self._data.append(self._buffer)
            self._buffer = 0
            self._bit_count = 0

    def write_bits(self, bits):
        for bit in bits:
            self.write_bit(bit)

    def get_bytes(self):
        result = bytearray(self._data)
        if self._bit_count:
            result.append(self._buffer << (8 - self._bit_count))
        return bytes(result)


class BitReader:
    def __init__(self, data):
        self.data = data
        self.position = 0

    def read_bit(self):
        if not self.has_bits():
            raise EOFError("No bits remain in the bit stream")

        byte_index = self.position // 8
        bit_index = 7 - (self.position % 8)
        bit = (self.data[byte_index] >> bit_index) & 1
        self.position += 1
        return bit

    def read_bits(self, count):
        if count < 0:
            raise ValueError("Bit count cannot be negative")

        result = 0
        for _ in range(count):
            result = (result << 1) | self.read_bit()
        return result

    def has_bits(self):
            return self.position < len(self.data) * 8