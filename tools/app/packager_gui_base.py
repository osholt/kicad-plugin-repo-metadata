# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-0-g8feb16b3)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class PackagerFrameBase
###########################################################################

class PackagerFrameBase ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"KiCad Packaging Toolkit", pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.CAPTION|wx.CLOSE_BOX|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.Size( 600,-1 ), wx.DefaultSize )

        bSizer16 = wx.BoxSizer( wx.VERTICAL )

        self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer1 = wx.BoxSizer( wx.VERTICAL )

        sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self.m_panel1, wx.ID_ANY, u"Metadata" ), wx.VERTICAL )

        self.metadataFilePicker = wx.FilePickerCtrl( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.EmptyString, u"Select metadata file", u"Json files (*.json)|*.json", wx.DefaultPosition, wx.DefaultSize, wx.FLP_FILE_MUST_EXIST|wx.FLP_OPEN|wx.FLP_USE_TEXTCTRL )
        sbSizer3.Add( self.metadataFilePicker, 0, wx.ALL|wx.EXPAND, 5 )

        self.packageName = wx.StaticText( sbSizer3.GetStaticBox(), wx.ID_ANY, u"Package name:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.packageName.Wrap( -1 )

        sbSizer3.Add( self.packageName, 0, wx.ALL, 5 )

        bSizer23 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_button17 = wx.Button( sbSizer3.GetStaticBox(), wx.ID_ANY, u"Run schema validation", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer23.Add( self.m_button17, 0, wx.ALL, 5 )

        self.m_button18 = wx.Button( sbSizer3.GetStaticBox(), wx.ID_ANY, u"Run Kicad repository validation", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer23.Add( self.m_button18, 0, wx.ALL, 5 )


        sbSizer3.Add( bSizer23, 0, wx.EXPAND, 5 )


        bSizer1.Add( sbSizer3, 0, wx.EXPAND, 5 )

        sbSizer4 = wx.StaticBoxSizer( wx.StaticBox( self.m_panel1, wx.ID_ANY, u"Package stats" ), wx.VERTICAL )

        self.packageFilePicker = wx.FilePickerCtrl( sbSizer4.GetStaticBox(), wx.ID_ANY, wx.EmptyString, u"Select a package file", u"Zip files (*.zip)|*.zip", wx.DefaultPosition, wx.DefaultSize, wx.FLP_FILE_MUST_EXIST|wx.FLP_OPEN|wx.FLP_USE_TEXTCTRL )
        sbSizer4.Add( self.packageFilePicker, 0, wx.ALL|wx.EXPAND, 5 )

        bSizer18 = wx.BoxSizer( wx.HORIZONTAL )


        sbSizer4.Add( bSizer18, 1, wx.EXPAND, 5 )

        bSizer19 = wx.BoxSizer( wx.HORIZONTAL )


        sbSizer4.Add( bSizer19, 1, wx.EXPAND, 5 )

        fgSizer5 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer5.AddGrowableCol( 1 )
        fgSizer5.SetFlexibleDirection( wx.BOTH )
        fgSizer5.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText23 = wx.StaticText( sbSizer4.GetStaticBox(), wx.ID_ANY, u"Package sha", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText23.Wrap( -1 )

        fgSizer5.Add( self.m_staticText23, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.pkgSha = wx.TextCtrl( sbSizer4.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
        fgSizer5.Add( self.pkgSha, 1, wx.ALL|wx.EXPAND, 5 )

        self.m_staticText24 = wx.StaticText( sbSizer4.GetStaticBox(), wx.ID_ANY, u"Package size", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText24.Wrap( -1 )

        fgSizer5.Add( self.m_staticText24, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.pkgSize = wx.TextCtrl( sbSizer4.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
        fgSizer5.Add( self.pkgSize, 1, wx.ALL|wx.EXPAND, 5 )

        self.m_staticText25 = wx.StaticText( sbSizer4.GetStaticBox(), wx.ID_ANY, u"Install size", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText25.Wrap( -1 )

        fgSizer5.Add( self.m_staticText25, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.pkgInstallSize = wx.TextCtrl( sbSizer4.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
        fgSizer5.Add( self.pkgInstallSize, 1, wx.ALL|wx.EXPAND, 5 )


        sbSizer4.Add( fgSizer5, 1, wx.EXPAND, 5 )


        bSizer1.Add( sbSizer4, 0, wx.EXPAND, 5 )

        bSizer2 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer2.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.closeBtn = wx.Button( self.m_panel1, wx.ID_CANCEL, u"Close", wx.DefaultPosition, wx.DefaultSize, 0 )

        self.closeBtn.SetDefault()
        bSizer2.Add( self.closeBtn, 0, wx.ALL, 5 )


        bSizer1.Add( bSizer2, 0, wx.EXPAND, 5 )


        self.m_panel1.SetSizer( bSizer1 )
        self.m_panel1.Layout()
        bSizer1.Fit( self.m_panel1 )
        bSizer16.Add( self.m_panel1, 1, wx.EXPAND, 5 )


        self.SetSizer( bSizer16 )
        self.Layout()
        bSizer16.Fit( self )

        self.Centre( wx.BOTH )

        # Connect Events
        self.metadataFilePicker.Bind( wx.EVT_FILEPICKER_CHANGED, self.OnMetadataLoaded )
        self.m_button17.Bind( wx.EVT_BUTTON, self.OnSchemaValidationClick )
        self.m_button18.Bind( wx.EVT_BUTTON, self.OnKicadValidationClick )
        self.packageFilePicker.Bind( wx.EVT_FILEPICKER_CHANGED, self.OnPackageLoaded )
        self.closeBtn.Bind( wx.EVT_BUTTON, self.OnCloseClick )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def OnMetadataLoaded( self, event ):
        event.Skip()

    def OnSchemaValidationClick( self, event ):
        event.Skip()

    def OnKicadValidationClick( self, event ):
        event.Skip()

    def OnPackageLoaded( self, event ):
        event.Skip()

    def OnCloseClick( self, event ):
        event.Skip()


