import csv
from pathlib import Path
import time
from xml.sax.saxutils import escape

from huffman import huffman_compress, huffman_decompress
from lzw import lzw_compress, lzw_decompress


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
if not DATA_DIR.is_dir():
    DATA_DIR = PROJECT_DIR.parent / "data"

RESULTS_FILE = PROJECT_DIR / "results" / "results.csv"
CHART_FILE = PROJECT_DIR / "charts" / "compression_time.svg"


def measure_time(function, data):
    start = time.perf_counter()
    result = function(data)
    return result, time.perf_counter() - start


def run_benchmark():
    if not DATA_DIR.is_dir():
        raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")

    files = sorted(path for path in DATA_DIR.iterdir() if path.is_file())
    if not files:
        raise ValueError(f"No input files found in {DATA_DIR}")

    results = []
    algorithms = (
        ("Huffman", huffman_compress, huffman_decompress),
        ("LZW", lzw_compress, lzw_decompress),
    )

    for file_path in files:
        data = file_path.read_bytes()

        for name, compress, decompress in algorithms:
            compressed, compression_time = measure_time(compress, data)
            restored, decompression_time = measure_time(decompress, compressed)
            if restored != data:
                raise RuntimeError(f"{name} round-trip failed for {file_path}")

            results.append([
                file_path.name,
                name,
                len(data),
                len(compressed),
                compression_time,
                decompression_time,
            ])

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "file",
            "algorithm",
            "original_size",
            "compressed_size",
            "compression_time",
            "decompression_time",
        ])
        writer.writerows(results)

    return results


def create_chart():
    if not RESULTS_FILE.is_file():
        raise FileNotFoundError(f"Benchmark results not found: {RESULTS_FILE}")

    series = {"Huffman": [], "LZW": []}
    with RESULTS_FILE.open("r", newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if Path(row["file"]).name.startswith("text_"):
                algorithm = row["algorithm"]
                if algorithm in series:
                    series[algorithm].append(
                        (int(row["original_size"]), float(row["compression_time"]))
                    )

    for points in series.values():
        points.sort()
    if not any(series.values()):
        raise ValueError("No text-file benchmark results found to chart")

    width, height = 900, 520
    left, right, top, bottom = 90, 40, 55, 80
    plot_width = width - left - right
    plot_height = height - top - bottom
    all_points = [point for points in series.values() for point in points]
    min_size = min(size for size, _ in all_points)
    max_size = max(size for size, _ in all_points)
    max_time = max(duration for _, duration in all_points)
    max_time = max_time or 1.0
    size_range = max_size - min_size or 1

    def x_position(size):
        return left + (size - min_size) / size_range * plot_width

    def y_position(duration):
        return top + plot_height - duration / max_time * plot_height

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="450" y="30" text-anchor="middle" font-size="18">'
        'Compression Time vs. Input Size</text>',
    ]

    for index in range(6):
        fraction = index / 5
        y = top + plot_height * (1 - fraction)
        value = max_time * fraction
        svg.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" '
            f'y2="{y:.2f}" stroke="#dddddd"/>'
        )
        svg.append(
            f'<text x="{left - 10}" y="{y + 4:.2f}" text-anchor="end" '
            f'font-size="12">{value:.3f}</text>'
        )

    for index in range(6):
        fraction = index / 5
        x = left + plot_width * fraction
        value = min_size + size_range * fraction
        svg.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" '
            f'y2="{top + plot_height}" stroke="#eeeeee"/>'
        )
        svg.append(
            f'<text x="{x:.2f}" y="{top + plot_height + 22}" text-anchor="middle" '
            f'font-size="12">{value:.0f}</text>'
        )

    svg.extend([
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" '
        f'y2="{top + plot_height}" stroke="black"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" '
        f'y2="{top + plot_height}" stroke="black"/>',
        f'<text x="{left + plot_width / 2:.2f}" y="{height - 20}" '
        'text-anchor="middle" font-size="14">Input size (bytes)</text>',
        f'<text x="22" y="{top + plot_height / 2:.2f}" text-anchor="middle" '
        f'font-size="14" transform="rotate(-90 22 {top + plot_height / 2:.2f})">'
        'Compression time (seconds)</text>',
    ])

    colors = {"Huffman": "#2563eb", "LZW": "#dc2626"}
    for line_index, (algorithm, points) in enumerate(series.items()):
        if not points:
            continue
        coordinates = " ".join(
            f"{x_position(size):.2f},{y_position(duration):.2f}"
            for size, duration in points
        )
        color = colors[algorithm]
        svg.append(
            f'<polyline points="{coordinates}" fill="none" stroke="{color}" '
            'stroke-width="2"/>'
        )
        for size, duration in points:
            svg.append(
                f'<circle cx="{x_position(size):.2f}" cy="{y_position(duration):.2f}" '
                f'r="4" fill="{color}"/>'
            )
        legend_y = top + 20 + line_index * 24
        svg.append(
            f'<line x1="{width - 150}" y1="{legend_y}" x2="{width - 125}" '
            f'y2="{legend_y}" stroke="{color}" stroke-width="3"/>'
        )
        svg.append(
            f'<text x="{width - 118}" y="{legend_y + 4}" font-size="13">'
            f'{escape(algorithm)}</text>'
        )

    svg.append("</svg>")
    CHART_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHART_FILE.write_text("\n".join(svg), encoding="utf-8")
    return CHART_FILE


if __name__ == "__main__":
    results = run_benchmark()
    chart_file = create_chart()
    print(f"Benchmark complete: {len(results)} results saved to {RESULTS_FILE}")
    print(f"Chart saved to {chart_file}")
