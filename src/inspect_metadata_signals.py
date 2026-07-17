import json
from pathlib import Path


METADATA_DIR = Path("data/raw/VEH_01/metadata")

FILES = [
    METADATA_DIR / "config-01.09.json",
    METADATA_DIR / "schema-01.09.json",
]

KEYWORDS = [
    "speed",
    "velocity",
    "rpm",
    "engine",
    "ignition",
    "gps",
    "latitude",
    "longitude",
    "wheel",
]


def search_json(value, path="root"):
    results = []

    if isinstance(value, dict):
        for key, child in value.items():
            current_path = f"{path}.{key}"
            searchable = key.lower()

            if isinstance(child, str):
                searchable += f" {child.lower()}"

            if any(keyword in searchable for keyword in KEYWORDS):
                results.append(
                    f"{current_path}: {str(child)[:200]}"
                )

            results.extend(search_json(child, current_path))

    elif isinstance(value, list):
        for index, child in enumerate(value):
            results.extend(
                search_json(child, f"{path}[{index}]")
            )

    return results


def main():
    all_results = []

    for file_path in FILES:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        results = search_json(data)

        all_results.append(f"\nFILE: {file_path.name}")

        if results:
            all_results.extend(results)
        else:
            all_results.append("- No matching signal definitions found.")

    print("\n".join(all_results))


if __name__ == "__main__":
    main()