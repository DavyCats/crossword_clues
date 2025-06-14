import json
import re
from pathlib import Path


CLUE_NUMBER_REGEX = re.compile("^[0-9]+\\. ")

BLACKLIST = ["-across", "-down", "this puzzle", "today's theme",
             "hidden theme", "starred clue", "this crossword",
             "with [0-9]+ (down|across)"]


def process_direction(data, direction, database):
    for answer, clue in zip(data["answers"][direction], data["clues"][direction]):
        # Skip answers containing non-ascii or non-alphabetic characters
        if not answer.isascii() or not answer.isalpha():
            continue

        clue_stripped = CLUE_NUMBER_REGEX.sub("", clue)

        # Skip clues relative to other clues or puzzle
        for x in BLACKLIST:
            if re.search(x, clue_stripped.lower()) is not None:
               break
        else:
            try:
                database[len(answer)]
            except KeyError:
                database[len(answer)] = {}

            try:
                database[len(answer)][answer].add(clue_stripped)
            except KeyError:
                database[len(answer)][answer] = {clue_stripped}


def process_file(path, database):
    with path.open("r") as json_file:
        try:
            data = json.load(json_file)
        except json.decoder.JSONDecodeError:
            print(f"skipped '{path}' due to parsing error")
            return

    process_direction(data, "across", database)
    process_direction(data, "down", database)


def main():
    db = {}
    data_dir = Path("./nyt_crosswords/")

    for path in data_dir.rglob("*.json"):
        process_file(path, db)
    print(len(db))

    with open("clues.json", "w") as out_json:
        json.dump(db, out_json, default=lambda x: list(x) if isinstance(x, set) else x)


if __name__ == "__main__":
    main()
