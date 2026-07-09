import csv
import json
import zstandard as zstd
import io
import random

INPUT_FILE = "lichess_db_puzzle.csv.zst"

TIERS = {
    "nivel1": {"min": 800, "max": 1200},
    "nivel2": {"min": 1400, "max": 1800},
    "nivel3": {"min": 1800, "max": 2200},
    "nivel4": {"min": 2200, "max": 2600},
}
TARGET_COUNT = 2000

def main():
    buckets = {name: [] for name in TIERS}

    with open(INPUT_FILE, "rb") as fh:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(fh) as reader:
            text_stream = io.TextIOWrapper(reader, encoding="utf-8")
            csv_reader = csv.DictReader(text_stream)

            for row in csv_reader:
                rating = int(row["Rating"])
                entry = {
                    "id": row["PuzzleId"],
                    "fen": row["FEN"],
                    "moves": row["Moves"].split(" "),
                    "rating": rating,
                    "themes": row["Themes"]
                }
                for name, bounds in TIERS.items():
                    if bounds["min"] <= rating <= bounds["max"]:
                        buckets[name].append(entry)

    for name, matches in buckets.items():
        random.shuffle(matches)
        selected = matches[:TARGET_COUNT]
        out_path = f"puzzles/{name}.json"
        with open(out_path, "w", encoding="utf-8") as out:
            json.dump(selected, out, indent=2)
        print(f"{name}: found {len(matches)}, saved {len(selected)} to {out_path}")

if __name__ == "__main__":
    main()