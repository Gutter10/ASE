import json
import ssl
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen


def get_pypi_data(url):
    context = ssl.create_default_context()
    if Path("/etc/ssl/cert.pem").exists():
        context.load_verify_locations("/etc/ssl/cert.pem")
    try:
        with urlopen(url, timeout=15, context=context) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404:
            return None
        raise


def main():
    path = Path(__file__).with_name("requirements.txt")
    requirements = []

    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            requirements.append(line)

    missing_packages = []
    missing_versions = []
    oldest_date = None
    oldest_release = None

    for requirement in requirements:
        package, version = requirement.split("==")
        package, version = package.strip(), version.strip()

        try:
            if get_pypi_data(f"https://pypi.org/pypi/{package}/json") is None:
                missing_packages.append(package)
                continue

            release = get_pypi_data(f"https://pypi.org/pypi/{package}/{version}/json")
            if release is None:
                missing_versions.append(requirement)
                continue

            for file in release["urls"]:
                upload_time = file["upload_time_iso_8601"]
                date = datetime.fromisoformat(upload_time.replace("Z", "+00:00"))
                if oldest_date is None or date < oldest_date:
                    oldest_date = date
                    oldest_release = requirement
        except OSError as error:
            raise SystemExit(f"Check failed for {requirement}: {error}")

    print(f"Dependencies checked: {len(requirements)}")
    print(f"Packages not on PyPI: {len(missing_packages)}")
    print(f"Versions not on PyPI: {len(missing_versions)}")
    if oldest_release:
        print(f"Oldest pinned release: {oldest_release} ({oldest_date.date()})")
    else:
        print("Oldest pinned release: no release with an upload date found")


if __name__ == "__main__":
    main()
