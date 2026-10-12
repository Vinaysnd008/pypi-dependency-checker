import json
import sys
import urllib.error
import urllib.request

PYPI_URL = "https://pypi.org/pypi"


def fetch_json(url):
    """Return parsed JSON for url, or None if PyPI answers 404."""
    request = urllib.request.Request(url, headers={"User-Agent": "requirements-checker"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def parse_line(line):
    """Split 'name==version' into (name, version). Version is None if not pinned."""
    if "==" in line:
        name, version = line.split("==", 1)
        return name.strip(), version.strip()
    return line.strip(), None


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "requirements.txt"

    with open(path, encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]

    packages_missing = 0
    versions_missing = 0
    oldest = None  # (upload_time, name, version)

    for line in lines:
        name, version = parse_line(line)

        # 1) Does the package exist at all?
        if fetch_json(f"{PYPI_URL}/{name}/json") is None:
            packages_missing += 1
            continue

        if version is None:
            continue

        # 2) Does the pinned version exist?
        release = fetch_json(f"{PYPI_URL}/{name}/{version}/json")
        if release is None:
            versions_missing += 1
            continue

        # 3) Upload time of the first file listed under "urls"
        files = release.get("urls", [])
        if not files:
            continue
        upload_time = files[0]["upload_time"]  # ISO format, e.g. 2019-01-14T06:10:12
        if oldest is None or upload_time < oldest[0]:
            oldest = (upload_time, name, version)

    print(f"Dependencies checked: {len(lines)}")
    print(f"Packages not on PyPI: {packages_missing}")
    print(f"Versions not on PyPI: {versions_missing}")
    if oldest:
        upload_time, name, version = oldest
        print(f"Oldest pinned release: {name}=={version} ({upload_time[:4]})")
    else:
        print("Oldest pinned release: none")


if __name__ == "__main__":
    main()
