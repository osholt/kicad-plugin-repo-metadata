import io
import json
import re
import sys
import wx

from .packager_gui_base import PackagerFrameBase
from . import util


class PackagerFrame(PackagerFrameBase):
    def __init__(self, parent):
        PackagerFrameBase.__init__(self, parent)

    def OnMetadataLoaded(self, event):
        filename = self.metadataFilePicker.Path
        try:
            with io.open(filename, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            self.packageName.Label = f"Package name: {metadata['name']}"
        except json.JSONDecodeError:
            wx.MessageBox(
                "File does not appear to be valid json file",
                style=wx.ICON_ERROR)
        except KeyError:
            self.packageName.Label = f"Package name: <invalid>"

    def OnSchemaValidationClick(self, event):
        filename = self.metadataFilePicker.Path

        if not filename:
            return

        try:
            util.validate_schema(filename)
            wx.MessageBox(
                "Validation passed",
                "Validation complete",
                style=wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(
                f"Validation failed:\n\n{e}",
                "Error",
                style=wx.ICON_ERROR)

    def OnKicadValidationClick(self, event):
        filename = self.metadataFilePicker.Path

        if not filename:
            return

        try:
            output = OutputWindow(self, "Validation log")
            sys.stdout = output
            sys.stderr = output
            util.kicad_validation(filename)
        except RuntimeError as e:
            if str(e) != "ignore":
                wx.MessageBox(
                    f"Validation failed:\n\n{e}",
                    "Error",
                    style=wx.ICON_ERROR)
        except Exception as e:
            wx.MessageBox(
                f"Validation failed:\n\n{e}",
                "Error",
                style=wx.ICON_ERROR)

    def OnPackageLoaded(self, event):
        filename = self.packageFilePicker.Path
        sha, size, instsize = util.get_package_stats(filename)
        self.pkgSha.Value = sha
        self.pkgSize.Value = str(size)
        self.pkgInstallSize.Value = str(instsize)

    def OnCloseClick(self, event):
        self.Destroy()


class OutputWindow(wx.PyOnDemandOutputWindow):
    def __init__(self, parent, caption):
        super().__init__(caption)
        self.SetParent(parent)
        self.size = (800, 600)
        self.pos = parent.GetPosition()
        self.escape_regex = re.compile("\033\\[\\d+m")
        self.red_style = wx.TextAttr(wx.RED)
        self.green_style = wx.TextAttr(wx.Colour(0, 150, 0))
        self.default_style = wx.TextAttr(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))

    def remove_last_line(self):
        txt = self.text.GetValue()  # type: str
        last_newline = txt.rfind('\n')
        to_delete = len(txt) - last_newline - 1
        last_position = self.text.GetLastPosition()
        self.text.Remove(last_position - to_delete, last_position)

    def write(self, s):
        if self.frame is None:
            self.CreateOutputWindow("")
        if isinstance(s, bytes):
            s = s.decode("utf-8")
        # remove color vt100 escape sequences
        if s.startswith("\033[91m"):
            style = self.red_style
        elif s.startswith("\033[92m"):
            style = self.green_style
        else:
            style = self.default_style
        s = self.escape_regex.sub("", s)
        s = s.replace("\r\n", "\n")
        if '\r' in s:
            s = s[s.rfind('\r') + 1:]
            self.remove_last_line()

        self.text.SetDefaultStyle(style)
        self.text.AppendText(s)
        wx.SafeYield()

    def CreateOutputWindow(self, txt):
        self.frame = wx.Frame(
            self.parent, -1, self.title, self.pos, self.size,
            style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        self.text = wx.TextCtrl(
            self.frame, -1, "", style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        self.text.SetFont(wx.Font(
            10,
            wx.FONTFAMILY_TELETYPE,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL))
        self.text.AppendText(txt)
        self.frame.Show(True)
        self.frame.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
