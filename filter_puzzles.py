import csv
import json
import zstandard as zstd
import io
import random

INPUT_FILE = "lichess_db_puzzle.csv.zst"
OUTPUT_FILE = "puzzles/intermediate.json"
MIN_RATING = 1400
MAX_RATING = 1800
TARGET_COUNT = 2000  # how many puzzles to keep for this tier

def main():
    matches = []

    with open(INPUT_FILE, "rb") as fh:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(fh) as reader:
            text_stream = io.TextIOWrapper(reader, encoding="utf-8")
            csv_reader = csv.DictReader(text_stream)

            for row in csv_reader:
                rating = int(row["Rating"])
                if MIN_RATING <= rating <= MAX_RATING:
                    matches.append({
                        "id": row["PuzzleId"],
                        "fen": row["FEN"],
                        "moves": row["Moves"].split(" "),
                        "rating": rating,
                        "themes": row["Themes"]
                    })

    print(f"Found {len(matches)} puzzles in range {MIN_RATING}-{MAX_RATING}")

    random.shuffle(matches)
    selected = matches[:TARGET_COUNT]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        json.dump(selected, out, indent=2)

    print(f"Saved {len(selected)} puzzles to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()