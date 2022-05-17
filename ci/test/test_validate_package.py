from argparse import Namespace
import io
import json
from requests import HTTPError
import zipfile
from unittest import TestCase
from unittest.mock import ANY, MagicMock, Mock, PropertyMock, patch
from io import StringIO

from validate import package
from munch import munchify


@patch("validate.package.verify_exit")
@patch("validate.package.verify")
class TestValidatePackage(TestCase):
    def setUp(self) -> None:
        with io.open("test/data/metadata_valid.json", encoding="utf-8") as f:
            self.metadata = munchify(json.load(f))

        with io.open("test/data/metadata_valid_old.json",
                     encoding="utf-8") as f:
            self.oldmetadata = munchify(json.load(f))

        with io.open("test/data/package/metadata.json", encoding="utf-8") as f:
            self.pkgmetadata = munchify(json.load(f))

        self.load_json_sideeffect_data = {
            "schema.json": {
                "type": "object"
            },
            "metadata.json": self.metadata,
            "metadata_old.json": self.oldmetadata
        }

        self.args = Namespace(
            identifier="testpackage",
            metadata="metadata.json",
            oldmetadata="metadata_old.json",
            max_icon_width=64,
            max_icon_height=64,
            max_icon_size=20480)

        self.package_files = [
            "metadata.json",
            "plugins/__init__.py",
            "plugins/allowed_no_extension",
            "resources/icon.png"]

    def load_json_sideeffect(self, file):
        return self.load_json_sideeffect_data.get(file)

    def verify_any_call_matcher(self, mock: Mock, *args):
        for call in mock.call_args_list:
            if len(call[0]) != len(args):
                continue

            matches = True
            i = 0

            for arg in call[0]:
                if callable(args[i]):
                    matches = matches and args[i](arg)
                else:
                    matches = matches and args[i] == arg
                i += 1

            if matches:
                return

        raise AssertionError(
            "None of the calls\n{}\nmatch arguments\n{}".format(
                mock.call_args_list, args))

    def verify_no_fails(self, mock: Mock):
        for call in mock.call_args_list:
            if not call[0][0]:
                raise AssertionError(
                    "{} called with failed condition:\n{}".format(mock, call))

    def download_file_sideeffect(self, url: str, path: str) -> bool:
        with zipfile.ZipFile(path, "w") as z:
            for file in self.package_files:
                z.write("test/data/package/" + file, file)
        return True

    @patch("io.open")
    def test_load_json_duplicate_keys(
            self, ioopen, verify, verify_exit):
        ioopen.return_value = io.BytesIO(b'{"a": 1, "a": 2}')

        self.assertRaises(ValueError, package.load_json_file, "foo")

    @patch("validate.package.load_json_file")
    @patch("validate.package.validate_metadata")
    def test_main(self, validate_metadata,
                  load_json_file, verify, verify_exit):
        load_json_file.side_effect = self.load_json_sideeffect

        with patch('sys.stdout', new=StringIO()) as fake_out:
            package.main(
                ["testpackage", "metadata.json", "metadata_old.json"])
            self.assertIn("Validation passed", fake_out.getvalue())

        validate_metadata.assert_called_once_with(
            self.args, ANY, ANY, "testpackage")
        verify_exit.assert_any_call(True, "0 error(s) detected")

    @patch("validate.package.load_json_file")
    @patch("validate.package.validate_metadata")
    def test_main_invalid_schema(self, validate_metadata,
                                 load_json_file, verify, verify_exit):
        load_json_file.side_effect = self.load_json_sideeffect
        self.load_json_sideeffect_data["schema.json"] = {"type": "abracadabra"}

        with patch('sys.stdout', new=StringIO()):
            package.main(
                ["testpackage", "metadata.json", "metadata_old.json"])

        self.verify_any_call_matcher(
            verify_exit, False, lambda msg: ("Schema is invalid" in msg))

    @patch("io.open")
    @patch("validate.package.validate_metadata")
    def test_main_invalid_metadata(
            self, validate_metadata, ioopen, verify, verify_exit):
        def open_sideffect(filename, *args, **kwargs):
            if filename == "metadata.json":
                return io.BytesIO(b'{ nope }')
            else:
                return io.BytesIO(b'{}')

        ioopen.side_effect = open_sideffect

        with patch('sys.stdout', new=StringIO()):
            package.main(["testpackage", "metadata.json"])

        self.verify_any_call_matcher(
            verify_exit, False, lambda msg: (
                "Metadata is invalid json" in msg))

    @patch("validate.package.load_json_file")
    @patch("validate.package.validate_metadata")
    def test_main_metadata_no_compliance(self, validate_metadata,
                                         load_json_file, verify, verify_exit):
        load_json_file.side_effect = self.load_json_sideeffect
        self.load_json_sideeffect_data["schema.json"] = {
            "type": "object", "required": ["somefield"]}

        with patch('sys.stdout', new=StringIO()):
            package.main(
                ["testpackage", "metadata.json", "metadata_old.json"])

        self.verify_any_call_matcher(
            verify_exit, False,
            lambda msg: ("Metadata doesn't comply with schema" in msg))

    @patch("validate.package.validate_version")
    def test_validate_metadata(self, validate_version,
                               verify, verify_exit):
        package.validate_metadata(
            self.args, self.metadata, self.oldmetadata, "testpackage")

        self.verify_no_fails(verify)
        self.verify_no_fails(verify_exit)
        validate_version.assert_called_with(
            self.args, self.metadata, self.metadata.versions[0])

    @patch("validate.package.validate_version")
    def test_validate_metadata_changed_url(self, validate_version,
                                           verify, verify_exit):
        self.oldmetadata.versions[0].download_url = "https://other.com"

        package.validate_metadata(
            self.args, self.metadata, self.oldmetadata, "testpackage")

        self.verify_no_fails(verify)
        self.verify_no_fails(verify_exit)
        validate_version.assert_any_call(
            self.args, self.metadata, self.metadata.versions[0])
        validate_version.assert_any_call(
            self.args, self.metadata, self.metadata.versions[1])

    @patch("validate.package.validate_version")
    def test_validate_metadata_delisted(self, validate_version,
                                        verify, verify_exit):
        self.metadata.versions = []

        package.validate_metadata(
            self.args, self.metadata, self.oldmetadata, "testpackage")

        self.verify_no_fails(verify)
        self.verify_no_fails(verify_exit)
        validate_version.assert_not_called()

    @patch("validate.package.validate_version")
    def test_validate_metadata_wrong_identifier(self, validate_version,
                                                verify, verify_exit):
        self.metadata.identifier = "foo"

        package.validate_metadata(self.args, self.metadata, None, "bar")

        verify_exit.assert_any_call(
            False, "Package identifier must match metadata")

    @patch("validate.package.validate_version")
    def test_validate_metadata_no_versions(self, validate_version,
                                           verify, verify_exit):
        self.metadata.versions = []

        package.validate_metadata(
            self.args, self.metadata, None, "testpackage")

        verify_exit.assert_called_with(
            False,
            "Package should have at least one version "
            "unless it's being delisted.")

    @patch("validate.package.validate_version")
    def test_validate_metadata_duplicate_versions(self, validate_version,
                                                  verify, verify_exit):
        self.metadata.versions[0].version = "1.0"

        package.validate_metadata(
            self.args, self.metadata, None, "testpackage")

        verify.assert_any_call(
            False,
            "Version 1.0: package versions must "
            "have unique version numbers")

    @patch("validate.package.validate_version")
    def test_validate_metadata_no_download_url(self, validate_version,
                                               verify, verify_exit):
        self.metadata.versions[0].pop("download_url")

        package.validate_metadata(
            self.args, self.metadata, None, "testpackage")

        verify.assert_any_call(
            False, "Version 2.0: download url must be specified")

    @patch("validate.package.validate_version")
    def test_validate_metadata_no_download_size(self, validate_version,
                                                verify, verify_exit):
        self.metadata.versions[0].pop("download_size")

        package.validate_metadata(
            self.args, self.metadata, None, "testpackage")

        verify.assert_any_call(
            False, "Version 2.0: download size must be specified")

    @patch("validate.package.validate_version")
    def test_validate_metadata_no_install_size(self, validate_version,
                                               verify, verify_exit):
        self.metadata.versions[0].pop("install_size")

        package.validate_metadata(
            self.args, self.metadata, None, "testpackage")

        verify.assert_any_call(
            False, "Version 2.0: install size must be specified")

    @patch("validate.package.validate_version")
    def test_validate_metadata_download_url_not_http(self, validate_version,
                                                     verify, verify_exit):
        self.metadata.versions[0].download_url = "ftp://example.com/1"

        package.validate_metadata(
            self.args, self.metadata, None, "testpackage")

        verify.assert_any_call(
            False, "Version 2.0: download url must be http(s)")

    @patch("validate.package.validate_version")
    def test_validate_metadata_no_sha(self, validate_version,
                                      verify, verify_exit):
        self.metadata.versions[0].pop("download_sha256")

        package.validate_metadata(
            self.args, self.metadata, None, "testpackage")

        verify.assert_any_call(
            False, "Version 2.0: download sha256 is required")

    @patch("validate.package.validate_version")
    def test_validate_metadata_epoch_change(self, validate_version,
                                            verify, verify_exit):
        self.metadata.versions[1].version_epoch = 1

        package.validate_metadata(
            self.args, self.metadata, self.oldmetadata, "testpackage")

        verify.assert_any_call(
            False, "Version 1.0: version epoch can not change")

    @patch("validate.package.validate_version")
    def test_validate_metadata_sha_change(self, validate_version,
                                          verify, verify_exit):
        self.metadata.versions[1].download_sha256 = "othersha"

        package.validate_metadata(
            self.args, self.metadata, self.oldmetadata, "testpackage")

        verify.assert_any_call(
            False, "Version 1.0: download sha256 can not change")

    @patch("validate.package.validate_version")
    def test_validate_metadata_dl_size_change(self, validate_version,
                                              verify, verify_exit):
        self.metadata.versions[1].download_size = 10

        package.validate_metadata(
            self.args, self.metadata, self.oldmetadata, "testpackage")

        verify.assert_any_call(
            False, "Version 1.0: download size can not change")

    @patch("validate.package.validate_version")
    def test_validate_metadata_inst_size_change(self, validate_version,
                                                verify, verify_exit):
        self.metadata.versions[1].install_size = 10

        package.validate_metadata(
            self.args, self.metadata, self.oldmetadata, "testpackage")

        verify.assert_any_call(
            False, "Version 1.0: install size can not change")

    @patch("validate.package.validate_version")
    def test_validate_metadata_status_change(self, validate_version,
                                             verify, verify_exit):
        # development -> stable
        self.metadata.versions[1].status = "stable"

        package.validate_metadata(
            self.args, self.metadata, self.oldmetadata, "testpackage")

        self.verify_no_fails(verify)

        # stable -> deprecated
        verify.reset_mock()
        self.oldmetadata.versions[0].status = "stable"
        self.metadata.versions[1].status = "deprecated"

        package.validate_metadata(
            self.args, self.metadata, self.oldmetadata, "testpackage")

        self.verify_no_fails(verify)

        # stable -> testing
        verify.reset_mock()
        self.metadata.versions[1].status = "testing"

        package.validate_metadata(
            self.args, self.metadata, self.oldmetadata, "testpackage")

        verify.assert_any_call(
            False,
            "Version 1.0: version status can change from "
            "stable only to deprecated")

        # deprecated -> stable
        verify.reset_mock()
        self.oldmetadata.versions[0].status = "deprecated"
        self.metadata.versions[1].status = "stable"

        package.validate_metadata(
            self.args, self.metadata, self.oldmetadata, "testpackage")

        verify.assert_any_call(
            False,
            "Version 1.0: version status can not change from deprecated")

    @patch("validate.package.verify_image")
    @patch("validate.package.validate_packaged_metadata")
    @patch("validate.package.download_file")
    @patch("validate.package.getsha256")
    def test_validate_version(self, getsha256, download_file,
                              validate_packaged_metadata, verify_image,
                              verify, verify_exit):
        getsha256.return_value = self.metadata.versions[0].download_sha256
        download_file.side_effect = self.download_file_sideeffect

        with patch("validate.package.SCHEMA", new={}):
            package.validate_version(
                self.args, self.metadata, self.metadata.versions[0])

        self.verify_no_fails(verify)
        self.verify_no_fails(verify_exit)

        validate_packaged_metadata.assert_called_with(
            self.pkgmetadata, self.metadata, self.metadata.versions[0])
        verify_image.assert_called_with(self.args, ANY, 2749)

    @patch("validate.package.validate_packaged_metadata")
    @patch("validate.package.download_file")
    @patch("validate.package.getsha256")
    def test_validate_version_platforms(self, getsha256, download_file,
                                        _, verify, verify_exit):
        getsha256.return_value = self.metadata.versions[0].download_sha256
        download_file.side_effect = self.download_file_sideeffect
        self.metadata.type = "library"

        with patch("validate.package.SCHEMA", new={}):
            package.validate_version(
                self.args, self.metadata, self.metadata.versions[0])

        verify.assert_any_call(
            False,
            "Version 2.0: non plugin type packages should not have "
            "platforms field in version entries")

    @patch("validate.package.validate_packaged_metadata")
    @patch("validate.package.download_file")
    @patch("validate.package.getsha256")
    def test_validate_version_extra_file(self, getsha256, download_file,
                                         _, verify, verify_exit):
        getsha256.return_value = self.metadata.versions[0].download_sha256
        download_file.side_effect = self.download_file_sideeffect
        self.package_files.append("extra.txt")
        self.package_files.append("extra_no_extension")

        with patch("validate.package.SCHEMA", new={}):
            package.validate_version(
                self.args, self.metadata, self.metadata.versions[0])

        verify.assert_any_call(
            False, 'Version 2.0: package contains extra file "extra.txt"')
        verify.assert_any_call(
            False, 'Version 2.0: package contains extra file "extra_no_extension"')

    @patch("validate.package.validate_packaged_metadata")
    @patch("validate.package.download_file")
    @patch("validate.package.getsha256")
    def test_validate_version_dl_size(self, getsha256, download_file,
                                      _, verify, verify_exit):
        getsha256.return_value = self.metadata.versions[0].download_sha256
        download_file.side_effect = self.download_file_sideeffect
        self.metadata.versions[0].download_size = 10

        with patch("validate.package.SCHEMA", new={}):
            package.validate_version(
                self.args, self.metadata, self.metadata.versions[0])

        self.verify_any_call_matcher(
            verify, False,
            lambda msg: "Version 2.0: download size does not match" in msg)

    @patch("validate.package.validate_packaged_metadata")
    @patch("validate.package.download_file")
    @patch("validate.package.getsha256")
    def test_validate_version_inst_size(self, getsha256, download_file,
                                        _, verify, verify_exit):
        getsha256.return_value = self.metadata.versions[0].download_sha256
        download_file.side_effect = self.download_file_sideeffect
        self.metadata.versions[0].install_size = 10

        with patch("validate.package.SCHEMA", new={}):
            package.validate_version(
                self.args, self.metadata, self.metadata.versions[0])

        self.verify_any_call_matcher(
            verify, False,
            lambda msg: "Version 2.0: install size does not match" in msg)

    @patch("validate.package.validate_packaged_metadata")
    @patch("validate.package.download_file")
    @patch("validate.package.getsha256")
    def test_validate_version_sha(self, getsha256, download_file,
                                  _, verify, verify_exit):
        getsha256.return_value = self.metadata.versions[0].download_sha256
        download_file.side_effect = self.download_file_sideeffect
        self.metadata.versions[0].download_sha256 = "foo"

        with patch("validate.package.SCHEMA", new={}):
            package.validate_version(
                self.args, self.metadata, self.metadata.versions[0])

        verify.assert_any_call(
            False, "Version 2.0: package sha256 does not match")

    @patch("validate.package.validate_packaged_metadata")
    @patch("validate.package.download_file")
    @patch("validate.package.getsha256")
    def test_validate_version_no_metadata(self, getsha256, download_file,
                                          _, verify, verify_exit):
        getsha256.return_value = self.metadata.versions[0].download_sha256
        download_file.side_effect = self.download_file_sideeffect
        self.package_files = self.package_files[1:]

        with patch("validate.package.SCHEMA", new={}):
            package.validate_version(
                self.args, self.metadata, self.metadata.versions[0])

        verify.assert_any_call(
            False, "Version 2.0: package has no metadata.json")

    @patch("validate.package.validate_packaged_metadata")
    @patch("validate.package.download_file")
    @patch("validate.package.getsha256")
    def test_validate_version_bad_zip(self, getsha256, download_file,
                                      _, verify, verify_exit):
        getsha256.return_value = self.metadata.versions[0].download_sha256

        def not_zip(url, path):
            with io.open(path, "w") as f:
                f.write("this is definitely not a zip")
            return True

        download_file.side_effect = not_zip

        with patch("validate.package.SCHEMA", new={}):
            package.validate_version(
                self.args, self.metadata, self.metadata.versions[0])

        verify.assert_any_call(False, "Version 2.0: bad zip file")

    def test_validate_packaged_metadata(self, verify, verify_exit):
        package.validate_packaged_metadata(
            self.pkgmetadata, self.metadata, self.metadata.versions[0])

        self.verify_no_fails(verify)
        self.verify_no_fails(verify_exit)

    def test_validate_packaged_metadata_identifier(self, verify, verify_exit):
        self.pkgmetadata.identifier = "foo"
        package.validate_packaged_metadata(
            self.pkgmetadata, self.metadata, self.metadata.versions[0])

        verify.assert_any_call(
            False,
            "Version 2.0: metadata in package contains different "
            "package identifier")

    def test_validate_packaged_metadata_version_count(
            self, verify, verify_exit):
        # no versions
        self.pkgmetadata.versions = []

        package.validate_packaged_metadata(
            self.pkgmetadata, self.metadata, self.metadata.versions[0])

        verify.assert_any_call(
            False,
            "Version 2.0: metadata in package "
            "must have exactly one version")

        verify.reset_mock()

        # multiple versions
        self.pkgmetadata.versions = self.metadata.versions

        package.validate_packaged_metadata(
            self.pkgmetadata, self.metadata, self.metadata.versions[0])

        verify.assert_any_call(
            False,
            "Version 2.0: metadata in package "
            "must have exactly one version")

    def test_validate_packaged_metadata_different_version(
            self, verify, verify_exit):
        self.pkgmetadata.versions[0].version = "2.2"
        package.validate_packaged_metadata(
            self.pkgmetadata, self.metadata, self.metadata.versions[0])

        verify.assert_any_call(
            False,
            "Version 2.0: metadata in package "
            "has different version")

    def test_validate_packaged_metadata_with_sha(
            self, verify, verify_exit):
        self.pkgmetadata.versions[0].download_sha256 = "foo"
        package.validate_packaged_metadata(
            self.pkgmetadata, self.metadata, self.metadata.versions[0])

        verify.assert_any_call(
            False,
            "Version 2.0: metadata in package "
            "can not have download_sha256 field")

    def test_validate_packaged_metadata_different(
            self, verify, verify_exit):
        for field in ["status", "kicad_version",
                      "kicad_version_max", "download_url"]:
            tmp = self.pkgmetadata.versions[0].get(field, None)
            self.pkgmetadata.versions[0][field] = "foo"
            package.validate_packaged_metadata(
                self.pkgmetadata, self.metadata, self.metadata.versions[0])

            verify.assert_any_call(
                False,
                f"Version 2.0: metadata in package "
                f"has different {field} field")

            verify.reset_mock()
            if tmp is not None:
                self.pkgmetadata.versions[0][field] = tmp
            else:
                self.pkgmetadata.versions[0].pop(field)

        self.pkgmetadata.versions[0].platforms = ["linux"]
        package.validate_packaged_metadata(
            self.pkgmetadata, self.metadata, self.metadata.versions[0])

        verify.assert_any_call(
            False,
            "Version 2.0: metadata in package "
            "has different platforms field")

    @patch("requests.get")
    @patch("io.open")
    @patch("validate.package.tqdm", new=MagicMock())
    def test_download_file(self, open, get, verify, verify_exit):
        fake_file = MagicMock(spec=io.BytesIO)
        open.return_value = fake_file
        response = MagicMock()
        total = PropertyMock(return_value=4)
        type(response).total = total

        def result_gen(x):
            yield b'abcd'

        response.iter_content.side_effect = result_gen
        get.return_value = response

        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(
                package.download_file("https://testurl.com", "file.txt"))

        get.aesrt_called_with("https://testurl.com", stream=True)
        open.assert_called_with("file.txt", "wb")
        fake_file.__enter__().write.assert_any_call(b'abcd')

    @patch("requests.get")
    @patch("io.open")
    @patch("validate.package.tqdm", new=MagicMock())
    @patch("validate.package.MAX_DOWNLOAD_SIZE", new=2)
    def test_download_file_too_large(self, open, get, verify, verify_exit):
        fake_file = MagicMock(spec=io.BytesIO)
        open.return_value = fake_file
        response = MagicMock()
        total = PropertyMock(return_value=4)
        type(response).total = total

        def result_gen(x):
            yield b'abcd'

        response.iter_content.side_effect = result_gen
        get.return_value = response

        with patch('sys.stdout', new=StringIO()):
            self.assertFalse(
                package.download_file("https://testurl.com", "file.txt"))

        self.verify_any_call_matcher(
            verify,
            False,
            lambda msg: "File is too large" in msg)

    @patch("requests.get")
    @patch("validate.package.tqdm", new=MagicMock())
    def test_download_file_404(self, get, verify, verify_exit):
        response = MagicMock()
        type(response).status_code = 404

        def response_raise():
            raise HTTPError(response=response)

        get.return_value = response
        response.raise_for_status.side_effect = response_raise

        with patch('sys.stdout', new=StringIO()):
            self.assertFalse(
                package.download_file("https://kicad.org/thisurldoesntexist",
                                      "file.txt"))

        self.verify_any_call_matcher(
            verify,
            False,
            lambda msg: "HTTP code: 404" in msg)
