import subprocess
import sys
import requests
from urllib.parse import quote
import tempfile
import tarfile

REPO_API_URL = "https://api.github.com/repos/mikhailprivalov/l2"


def get_release_info_from_github_by_version(version):
    v = quote(version)
    response = requests.get(f"{REPO_API_URL}/releases/tags/{v}")
    if response.status_code == 200:
        return response.json()
    else:
        print('Error while getting release info from github')
        print(response.url)
        print(response.text)
        sys.exit(1)


def get_current_version():
    try:
        if sys.platform == 'win32':
            v = subprocess.check_output(["powershell", ".\\current-version.ps1"]).decode().strip()
            return f'v{v}'
        return f'v{subprocess.check_output(["./current-version.sh"]).decode().strip()}'
    except subprocess.CalledProcessError as e:
        print("Error: {}".format(e))
        sys.exit(1)


def main():
    print("Webpack bundle precompiled downloader")
    current_version = get_current_version()
    print("Current version: {}".format(current_version))
    webpack_bundle_name = f"webpack_bundles_{current_version}.tar.gz"
    print("Webpack bundle name expected: {}".format(webpack_bundle_name))
    print("Check release info on github")
    release_info = get_release_info_from_github_by_version(current_version)
    print("Release date: {}".format(release_info['published_at']))

    for asset in release_info["assets"]:
        if asset["name"] == webpack_bundle_name:
            print("Found webpack bundle asset")
            print("Downloading asset...")
            with tempfile.NamedTemporaryFile() as f:
                with requests.get(asset["browser_download_url"], stream=True) as response:
                    total_length = int(response.headers.get('content-length'))
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            f.flush()
                            done = int(50 * f.tell() / total_length)
                            sys.stdout.write("\r[%s%s] %s%%" % ('=' * done, ' ' * (50-done), round(100 * f.tell() / total_length, 2)))
                            sys.stdout.flush()
                    print()
                    if response.status_code == 200:
                        print("Extract asset to temp dir with tempfile")
                        with tempfile.TemporaryDirectory() as d:
                            with tarfile.open(f.name) as tar:
                                for member in tar.getmembers():
                                    print("\rExtracting %s" % member.name)
                                    tar.extract(member, d)
                                print("Extracted")
                                print("Remove old webpack bundles")
                                subprocess.run(["rm", "-rf", "assets/webpack_bundles"])
                                print("Copy new webpack bundles")
                                subprocess.run(["mv", f"{d}/assets/webpack_bundles", "assets/"])
                        print("Done")
                        sys.exit(0)
                    else:
                        print("Error while downloading asset")
                        print(response.url)
                        print(response.text)
                        sys.exit(1)


if __name__ == '__main__':
    main()
