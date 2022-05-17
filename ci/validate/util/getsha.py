import hashlib
import io


READ_SIZE = 65536


def getsha256(filename):
    hash = hashlib.sha256()
    with io.open(filename, "rb") as f:
        data = f.read(READ_SIZE)
        while data:
            hash.update(data)
            data = f.read(READ_SIZE)
    return hash.hexdigest()
