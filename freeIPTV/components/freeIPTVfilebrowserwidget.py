# -*- coding: utf-8 -*-
from Plugins.Extensions.freeIPTV.inits import *
from Plugins.Extensions.freeIPTV.tools.iptvtools import *
###################################################
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox
from Components.FileList import FileList
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from Components.ActionMap import ActionMap
from Tools.BoundFunction import boundFunction
###################################################
 
class freeIPTVSelectorWidget(Screen):
    skin = LoadSkin('freeIPTVSelectorWidget')
    
    def __init__(self, session, currDir, title="Directory browser", selectFiles = False):
        print("freeIPTVSelectorWidget.__init__ -------------------------------")
        Screen.__init__(self, session)
        self["key_red"]    = Label(_("Cancel"))
        #self["key_yellow"] = Label(_("Refresh"))
        self["key_blue"]   = Label(_("New directory"))
        self["key_green"]  = Label(_("Apply"))
        self["curr_dir"]   = Label(_(" "))
        self.filelist      = FileList(directory=currDir, matchingPattern="", showFiles=selectFiles)
        self["filelist"]   = self.filelist
        self["FilelistActions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "green" : self.use,
                "red"   : self.exit,
                "yellow": self.refresh,
                "blue"  : self.newDir,
                "ok"    : self.ok,
                "cancel": self.exit
            })
        self.title = title
        self.returnFile = selectFiles
        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(self.__onClose)

    def mkdir(newdir):
        """ Wrapper for the os.mkdir function
            returns status instead of raising exception
        """
        try:
            os_mkdir(newdir)
            sts = True
            msg = _('%s directory has been created.') % newdir
        except:
            sts = False
            msg = _('Error creating %s directory.') % newdir
            printExc()
        return sts,msg
    
    def __del__(self):
        print("freeIPTVSelectorWidget.__del__ -------------------------------")

    def __onClose(self):
        print("freeIPTVSelectorWidget.__onClose -----------------------------")
        self.onClose.remove(self.__onClose)
        self.onLayoutFinish.remove(self.layoutFinished)

    def layoutFinished(self):
        print("freeIPTVSelectorWidget.layoutFinished -------------------------------")
        self.setTitle(_(self.title))
        self.currDirChanged()

    def currDirChanged(self):
        self["curr_dir"].setText(_(self.getCurrentDirectory()))
        
    def getCurrentDirectory(self):
        currDir = self["filelist"].getCurrentDirectory()
        if currDir and os_path.isdir( currDir ):
            return currDir
        else:
            return "/"

    def use(self):
        if self.returnFile:
            try:
                print "freeIPTVSelectorWidget: selected file '%s'" % (self.getCurrentDirectory() + self['filelist'].getCurrent()[0][0])
                self.close( self.getCurrentDirectory() + self['filelist'].getCurrent()[0][0] )
            except:
                print "freeIPTVSelectorWidget: no file in %s selected!!!" % ( self.getCurrentDirectory() )
        else:
            self.close( self.getCurrentDirectory() )

    def exit(self):
        self.close(None)

    def ok(self):
        if self.filelist.canDescent():
            self.filelist.descent()
        self.currDirChanged()

    def refresh(self):
        self["filelist"].refresh()

    def newDir(self):
        currDir = self["filelist"].getCurrentDirectory()
        if currDir and os_path.isdir( currDir ):
            self.session.openWithCallback(boundFunction(self.enterPatternCallBack, currDir), VirtualKeyBoard, title = (_("Enter name")), text = "")

    def IsValidFileName(name, NAME_MAX=255):
        prohibited_characters = ['/', "\000", '\\', ':', '*', '<', '>', '|', '"']
        if isinstance(name, basestring) and (1 <= len(name) <= NAME_MAX):
            for it in name:
                if it in prohibited_characters:
                    return False
            return True
        return False
    
    def enterPatternCallBack(self, currDir, newDirName=None):
        if None != currDir and newDirName != None:
            sts = False
            if self.IsValidFileName(newDirName):
                sts,msg = self.mkdir(os_path.join(currDir, newDirName))
            else:
                msg = _("Wrong directory name.")
            if sts:
                self.refresh()
            else:
                self.session.open(MessageBox, msg, type = MessageBox.TYPE_INFO, timeout=5)