import zipfile
import os
import json
import jsonschema
import requests


SCHEMA_URL = "https://gitlab.com/kicad/code/kicad/-/raw/master/kicad/pcm/schemas/pcm.v1.schema.json"
SCHEMA = None


def get_package_stats(filename: str) -> tuple:
    from validate.util.getsha import getsha256
    instsize = 0
    z = zipfile.ZipFile(filename, "r")
    for entry in z.infolist():
        if not entry.is_dir():
            instsize += entry.file_size

    return getsha256(filename), os.path.getsize(filename), instsize


def get_schema() -> dict:
    global SCHEMA

    if SCHEMA is None:
        response = requests.get(SCHEMA_URL)
        response.raise_for_status()
        SCHEMA = response.json()
        with open("schema.json", "wb") as f:
            f.write(response.content)

    return SCHEMA


def validate_schema(filename: str):
    from validate import package

    metadata = package.load_json_file(filename)

    try:
        jsonschema.validate(metadata, get_schema())
    except jsonschema.ValidationError as e:
        raise ValueError(f"Metadata doesn't comply with schema\n{e.message}")
    except jsonschema.SchemaError as e:
        raise ValueError(f"Schema is invalid\n{e.message}")


def kicad_validation(filename: str) -> tuple:
    get_schema()

    # monkey patch verify_exit to not exit but raise an exception instead
    from validate import package
    def verify_raise(condition, message):
        if not condition:
            print(message)
            raise RuntimeError("ignore")

    package.verify_exit = verify_raise
    package.TQDM_NCOL = 80

    # monkey patch error count to reset
    from validate.util import verify
    verify.FAILURES = 0

    metadata = package.load_json_file(filename)

    package.main([metadata["identifier"], filename])
