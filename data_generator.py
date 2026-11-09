from pathlib import Path
import random


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def create_folder(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def generate_text(size_bytes, seed=42):
    if size_bytes < 0:
        raise ValueError("Size cannot be negative")
    rng = random.Random(seed)
    alphabet = b"abcdefghijklmnopqrstuvwxyz "
    return bytes(rng.choice(alphabet) for _ in range(size_bytes))


def generate_binary(size_bytes, seed=42):
    if size_bytes < 0:
        raise ValueError("Size cannot be negative")
    rng = random.Random(seed)
    return bytes(rng.randrange(256) for _ in range(size_bytes))


def generate_repetitive(size_bytes):
    if size_bytes < 0:
        raise ValueError("Size cannot be negative")
    pattern = b"ABAB"
    return (pattern * ((size_bytes + len(pattern) - 1) // len(pattern)))[:size_bytes]


def generate_csv(size_bytes, seed=42):
    if size_bytes < 0:
        raise ValueError("Size cannot be negative")
    rng = random.Random(seed)
    content = bytearray()

    while len(content) < size_bytes:
        line = (
            f"user_{rng.randrange(100)},action_{rng.randrange(10)},"
            f"{rng.randrange(1000)}\n"
        )
        content.extend(line.encode("utf-8"))

    return bytes(content[:size_bytes])


def generate_all_data():
    sizes = [10 * 1024, 100 * 1024, 1024 * 1024, 5 * 1024 * 1024]
    create_folder(DATA_DIR)

    for size in sizes:
        name = f"{size // 1024}kb"
        datasets = {
            f"text_{name}.txt": generate_text(size),
            f"binary_{name}.bin": generate_binary(size),
            f"repetitive_{name}.bin": generate_repetitive(size),
            f"csv_{name}.csv": generate_csv(size),
        }
        for file_name, data in datasets.items():
            (DATA_DIR / file_name).write_bytes(data)


if __name__ == "__main__":
    generate_all_data()
