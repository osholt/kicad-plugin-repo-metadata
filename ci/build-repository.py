import argparse
import io
import json
import os
from datetime import datetime
from validate.util.getsha import getsha256


ARTIFACTS_URL = os.environ["CI_JOB_URL"] + "/artifacts/raw/artifacts"
JOB_ID = os.environ["CI_JOB_ID"]


def load_json_file(file_name: str) -> dict:
    with io.open(file_name, encoding="utf-8") as f:
        return json.load(f)


def update(json, file):
    mtime = os.path.getmtime(file)
    dt = datetime.fromtimestamp(mtime)
    sha = getsha256(file)

    json["url"] = ARTIFACTS_URL + "/" + os.path.basename(file)
    json["sha256"] = sha
    json["update_timestamp"] = int(mtime)
    json["update_time_utc"] = dt.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="KiCad PCM test repository builder")

    parser.add_argument("metadata", help="Package metadata file", nargs="*")

    args = parser.parse_args()
    packages = []

    for file in args.metadata:
        packages.append(load_json_file(file))

    with io.open("artifacts/packages.json", "w", encoding="utf-8") as f:
        json.dump({"packages": packages}, f, indent=4)

    repo = load_json_file("ci/repository.json")
    repo["name"] = "Test PCM repository for ci job {}".format(JOB_ID)
    update(repo["packages"], "artifacts/packages.json")

    if os.path.exists("artifacts/resources.zip"):
        update(repo["resources"], "artifacts/resources.zip")
    else:
        del repo["resources"]

    with io.open("artifacts/repository.json", "w", encoding="utf-8") as f:
        json.dump(repo, f, indent=4)

    print(f"Repository should be available at {ARTIFACTS_URL}/repository.json")
