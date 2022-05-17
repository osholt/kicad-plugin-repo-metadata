import argparse
import jsonschema
import json
import io
import os
import requests
import pathlib
import zipfile
from jsonschema.exceptions import SchemaError, ValidationError
from requests.exceptions import HTTPError
from tqdm import tqdm
from munch import Munch, munchify
from .util.verify import verify, verify_exit, get_failures
from .util.getsha import getsha256
from .image import add_image_args, verify_image


MAX_DOWNLOAD_SIZE = 100 * 1024 * 1024  # 100 Mb
TQDM_NCOL = None

ALLOWED_FILES = {
    "all": [
        "/metadata.json",
        "/resources/icon.png",
    ],
    "plugin": [
        "/plugins/*",
        "/plugins/**/*",
        # Further recursion is open-coded below
    ],
    "library": [
        "/footprints/*.pretty/*.kicad_mod",
        "/symbols/*.kicad_sym",
        "/3dmodels/*.3dshapes/*.stp",
        "/3dmodels/*.3dshapes/*.step",
        "/3dmodels/*.3dshapes/*.stpz",
        "/3dmodels/*.3dshapes/*.stp.gz",
        "/3dmodels/*.3dshapes/*.step.gz",
        "/3dmodels/*.3dshapes/*.wrl",
        "/3dmodels/*.3dshapes/*.wrz",
        "/3dmodels/*.3dshapes/*.iges",
    ],
    "colortheme": [
        "/colors/*.json",
    ]
}

SCHEMA = None


def raise_on_duplicate_keys(ordered_pairs: list) -> dict:
    """
    Raise ValueError if a duplicate key exists in provided ordered list
    of pairs, otherwise return a dict.
    """
    result = {}
    for key, val in ordered_pairs:
        if key in result:
            raise ValueError(f'Duplicate key: {key}')
        else:
            result[key] = val
    return result


def load_json_file(file_name: str) -> dict:
    with io.open(file_name, encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=raise_on_duplicate_keys)


def path_match(type: str, purepath: pathlib.PurePath) -> bool:
    for pattern in ALLOWED_FILES["all"]:
        if purepath.match(pattern):
            return True

    for pattern in ALLOWED_FILES[type]:
        if purepath.match(pattern):
            return True

    if type == 'plugin':
        strpath = str(purepath)
        if strpath.startswith('/plugins') or strpath.startswith('plugins'):
            return True

    return False


def max_deviation(a: int, b: int, delta: int) -> bool:
    return abs(a - b) < delta


def download_file(url: str, path: str) -> bool:
    print(f"Downloading {url} to {path}")

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total = response.headers.get('Content-length', None)
        if total:
            total = int(total)
        bytes_written = 0

        with io.open(path, "wb") as f:
            progress = tqdm(
                unit="B",
                miniters=1,
                total=total,
                unit_scale=True,
                unit_divisor=1024,
                ncols=TQDM_NCOL)

            for chunk in response.iter_content(1024):
                f.write(chunk)
                bytes_written += len(chunk)
                progress.update(len(chunk))

                if bytes_written > MAX_DOWNLOAD_SIZE:
                    progress.close()
                    raise RuntimeError(
                        "File is too large to download, review manually")

            progress.close()

        return True

    except HTTPError as e:
        verify(
            False,
            f"Error downloading url {url}\n"
            f"HTTP code: {e.response.status_code}")
    except Exception as e:
        verify(
            False,
            f"Error downloading url {url}\n"
            f"Error: {e}")

    return False


def validate_packaged_metadata(
        pkg_metadata: Munch, metadata: Munch, version: Munch):
    msg_prefix = f"Version {version.version}: metadata in package"

    verify(metadata.identifier == pkg_metadata.identifier,
           f"{msg_prefix} contains different package identifier")
    verify(len(pkg_metadata.versions) == 1,
           f"{msg_prefix} must have exactly one version")

    if len(pkg_metadata.versions) == 1:
        v = pkg_metadata.versions[0]

        verify((v.version == version.version and
                v.get("version_epoch", 0) == version.get("version_epoch", 0)),
               f"{msg_prefix} has different version")
        verify("download_sha256" not in v,
               f"{msg_prefix} can not have download_sha256 field")

        def verify_field_equality(field):
            verify(((field not in v and field not in version) or
                    (field in v and field in version and
                     v.get(field) == version.get(field))),
                   f"{msg_prefix} has different {field} field")

        verify_field_equality("status")
        verify_field_equality("kicad_version")
        verify_field_equality("kicad_version_max")

        if "download_url" in v:
            verify_field_equality("download_url")

        # not specified platforms is assumed to be "all platforms"
        if "platforms" not in v:
            v["platforms"] = ["windows", "macos", "linux"]
        if "platforms" not in version:
            version["platforms"] = ["windows", "macos", "linux"]

        verify(sorted(v.platforms) == sorted(version.platforms),
               f"{msg_prefix} has different platforms field")


def validate_version(args: argparse.Namespace,
                     metadata: Munch, version: Munch):
    if not os.path.isdir("tmp"):
        os.mkdir("tmp")
    path = os.path.join(
        "tmp", f"{metadata.identifier}_v{version.version}.zip")

    verify(metadata.type == "plugin" or "platforms" not in version,
           f"Version {version.version}: non plugin type packages "
           f"should not have platforms field in version entries")

    if download_file(version.download_url, path):
        dlsize = os.path.getsize(path)
        instsize = None

        if "download_size" in version:
            verify(max_deviation(version.download_size, dlsize, 1024),
                   f"Version {version.version}: download size does not match, "
                   f"expected {version.download_size}, actual {dlsize}")

        if "download_sha256" in version:
            verify(getsha256(path) == version.download_sha256,
                   f"Version {version.version}: package sha256 does not match")

        z = None
        try:
            z = zipfile.ZipFile(path, "r")
            testzip = z.testzip()
            verify(
                testzip is None,
                f"Version {version.version}: bad zip file, "
                f"checksum error on {testzip}")

            pkg_has_metadata = False
            instsize = 0

            for entry in z.infolist():
                if entry.is_dir():
                    continue

                p = pathlib.PurePath("/" + entry.filename)

                verify(
                    path_match(metadata.type, p),
                    f"Version {version.version}: package contains "
                    f"extra file \"{entry.filename}\"")

                instsize += entry.file_size

                if entry.filename == "resources/icon.png":
                    iconbytes = z.read(entry)
                    verify_image(args, io.BytesIO(iconbytes), len(iconbytes))

                if entry.filename == "metadata.json":
                    pkg_has_metadata = True
                    metadatabytes = z.read(entry)
                    try:
                        pkg_metadata_json = json.load(
                            io.BytesIO(metadatabytes),
                            object_pairs_hook=raise_on_duplicate_keys)
                        global SCHEMA
                        jsonschema.validate(metadata, SCHEMA)
                        pkg_metadata = munchify(pkg_metadata_json)
                        validate_packaged_metadata(
                            pkg_metadata, metadata, version)
                    except ValidationError as e:
                        verify_exit(False,
                                    f"Version {version.version}: metadata "
                                    f"contained in package doesn't comply "
                                    f"with schema\n{e.message}")
                    except ValueError as e:
                        verify(False,
                               f"Version {version.version}: package "
                               f"contains invalid metadata.json.\n{e}")

            verify(pkg_has_metadata,
                   f"Version {version.version}: package has no metadata.json")

        except zipfile.BadZipFile:
            verify(False, f"Version {version.version}: bad zip file")

        if z:
            z.close()

        if "install_size" in version and instsize is not None:
            verify(max_deviation(version.install_size, instsize, 1024),
                   f"Version {version.version}: install size does not match, "
                   f"expected {version.install_size}, actual {instsize}")
    else:
        verify(False, f"Version {version.version}: download failed")

    if os.path.exists(path):
        os.remove(path)


def verify_version_field_changes(old: Munch, new: Munch):
    if "version_epoch" in new or "version_epoch" in old:
        verify(("version_epoch" in old and "version_epoch" in new and
                old.version_epoch == new.version_epoch),
               f"Version {new.version}: version epoch can not change")

    if "download_sha256" in new:
        verify(old.download_sha256 == new.download_sha256,
               f"Version {new.version}: download sha256 can not change")

    if "download_size" in new and "download_size" in old:
        verify(old.download_size == new.download_size,
               f"Version {new.version}: download size can not change")

    if "install_size" in new and "install_size" in old:
        verify(old.install_size == new.install_size,
               f"Version {new.version}: install size can not change")

    if old.status == "stable":
        verify(new.status in ["stable", "deprecated"],
               f"Version {new.version}: version status can change from "
               "stable only to deprecated")

    if old.status == "deprecated":
        verify(new.status == "deprecated",
               f"Version {new.version}: version status can not change "
               "from deprecated")


def validate_metadata(args: argparse.Namespace,
                      metadata: Munch, oldmetadata: Munch,
                      identifier: str):
    verify_exit(metadata.identifier == identifier,
                "Package identifier must match metadata")

    verify_exit(
        oldmetadata is not None or len(metadata.versions) > 0,
        "Package should have at least one version unless it's being delisted.")

    new_versions = {}

    for version in metadata.versions:
        verify(
            version.version not in new_versions,
            f"Version {version.version}: package versions must "
            "have unique version numbers")
        verify("download_url" in version,
               f"Version {version.version}: download url must be specified")
        if "download_url" in version:
            verify(version.download_url[0:4] == "http",
                   f"Version {version.version}: download url must be http(s)")
        verify("download_size" in version,
               f"Version {version.version}: download size must be specified")
        verify("install_size" in version,
               f"Version {version.version}: install size must be specified")
        verify("download_sha256" in version,
               f"Version {version.version}: download sha256 is required")
        new_versions[version.version] = version

    if oldmetadata:
        for old in oldmetadata.versions:
            if old.version in new_versions:
                new = new_versions[old.version]
                verify_version_field_changes(old, new)
                if ("download_url" not in new or
                        old["download_url"] == new["download_url"]):
                    new_versions.pop(old.version)

    for version in new_versions.values():
        validate_version(args, metadata, version)


def main(args):
    parser = argparse.ArgumentParser(
        description='KiCad PCM repository package validator')

    parser.add_argument("identifier", help="Package identifier")
    parser.add_argument("metadata", help="Path to metadata file")
    parser.add_argument(
        "oldmetadata", help="Path to previous version of the metadata",
        nargs='?', default=None)

    add_image_args(parser)

    args = parser.parse_args(args)

    global SCHEMA
    SCHEMA = load_json_file("schema.json")

    metadata = {}
    try:
        metadata = load_json_file(args.metadata)
    except ValueError as e:
        verify_exit(False, f"Metadata is invalid json: {e}")

    oldmetadata = None

    if args.oldmetadata:
        oldmetadata = load_json_file(args.oldmetadata)

    try:
        jsonschema.validate(metadata, SCHEMA)
    except ValidationError as e:
        verify_exit(False, f"Metadata doesn't comply with schema\n{e.message}")
    except SchemaError as e:
        verify_exit(False, f"Schema is invalid\n{e.message}")

    validate_metadata(
        args,
        munchify(metadata),
        munchify(oldmetadata),
        args.identifier)

    failures = get_failures()

    verify_exit(failures == 0, f"{failures} error(s) detected")
    print("\033[92mValidation passed\033[0m")
