import wx
import sys
import os

from app import PackagerFrame

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(current_dir)
sys.path.insert(0, os.path.join(current_dir, "ci"))

app = wx.App()
frame = PackagerFrame(None)
frame.Show()
app.MainLoop()
