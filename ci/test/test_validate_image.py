from argparse import Namespace
from unittest import TestCase
from unittest.mock import ANY, Mock, call, patch
from validate import image
from io import StringIO, BytesIO


@patch("validate.image.verify_exit")
@patch("validate.image.verify")
class TestValidateImage(TestCase):

    @patch("validate.image.verify_image")
    def test_main_success(self, verify_image, verify, verify_exit):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            image.main(["--max-icon-width", "3", "--max-icon-height",
                        "4", "--max-icon-size", "5",
                        "test/data/package/resources/icon.png"])
            self.assertIn("Validation passed", fake_out.getvalue())
        verify_image.assert_called_once_with(
            Namespace(
                max_icon_width=3,
                max_icon_height=4,
                max_icon_size=5,
                file="test/data/package/resources/icon.png"),
            "test/data/package/resources/icon.png",
            2749)
        verify_exit.assert_called_once_with(True, ANY)

    @patch("validate.image.verify_image")
    @patch("validate.image.get_failures", new=Mock(return_value=1))
    def test_main_failure(self, verify_image, verify, verify_exit):
        with patch('sys.stdout', new=StringIO()):
            image.main(["--max-icon-width", "3", "--max-icon-height",
                        "4", "--max-icon-size", "5",
                        "test/data/package/resources/icon.png"])
        verify_image.assert_called_once_with(
            Namespace(
                max_icon_width=3,
                max_icon_height=4,
                max_icon_size=5,
                file="test/data/package/resources/icon.png"),
            "test/data/package/resources/icon.png",
            2749)
        verify_exit.assert_called_once_with(False, "1 error(s) detected")

    def test_image(self, verify, verify_exit):
        for w in [63, 64]:
            for h in [63, 64]:
                for s in [2104, 2105]:
                    args = Namespace(
                        max_icon_width=w,
                        max_icon_height=h,
                        max_icon_size=s,
                        file="test/data/package/resources/icon.png"
                    )
                    image.verify_image(
                        args, "test/data/package/resources/icon.png", 2105)
                    verify.assert_has_calls(
                        [call(64 <= w, "Image width exceeds maximum"),
                         call(64 <= h, "Image height exceeds maximum"),
                         call(2105 <= s, "Image file size exceeds maximum")])
                    verify.reset_mock()

    def test_image_invalid(self, verify, verify_exit):
        image.verify_image(Namespace(), BytesIO(), 111)
        verify.assert_called_once_with(False, "Image could not be loaded")
