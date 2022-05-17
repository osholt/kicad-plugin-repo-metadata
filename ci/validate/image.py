import argparse
import os
from PIL import Image, UnidentifiedImageError
from .util.verify import verify, verify_exit, get_failures


def add_image_args(parser):
    parser.add_argument(
        "--max-icon-width", help="Maximum width", type=int, default=64)
    parser.add_argument(
        "--max-icon-height", help="Maximum height", type=int, default=64)
    parser.add_argument(
        "--max-icon-size", help="Maximum file size", type=int, default=20480)


def verify_image(args, file, size):
    try:
        img = Image.open(file, formats=["PNG"])
        verify(img.width <= args.max_icon_width, "Image width exceeds maximum")
        verify(img.height <= args.max_icon_height,
               "Image height exceeds maximum")
        verify(size <= args.max_icon_size,
               "Image file size exceeds maximum")
        img.close()
    except UnidentifiedImageError:
        verify(False, "Image could not be loaded")


def main(args):
    parser = argparse.ArgumentParser(
        description='KiCad PCM repository image validator')

    parser.add_argument("file", help="Path to image file")
    add_image_args(parser)

    args = parser.parse_args(args)

    verify_image(args, args.file, os.path.getsize(args.file))

    failures = get_failures()

    verify_exit(failures == 0, f"{failures} error(s) detected")

    print("\033[92mValidation passed\033[0m")
