import sys


FAILURES = 0


def verify_exit(condition, message):
    if not condition:
        print(f"\033[91m{message}\033[0m")
        sys.exit(1)


def verify(condition, message):
    global FAILURES
    if not condition:
        print(f"\033[91m{message}\033[0m")
        FAILURES += 1


def get_failures():
    global FAILURES
    return FAILURES
