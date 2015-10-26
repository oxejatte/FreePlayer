from __init__ import *
from translate import _

from Screens.Screen import Screen

from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox

from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
#from Components.ProgressBar import ProgressBar
from Components.config import *
#from Components.ServiceEventTracker import ServiceEventTracker
#from Components.GUIComponent import GUIComponent
#from Components.Converter.ConditionalShowHide import ConditionalShowHide
from Tools.LoadPixmap import LoadPixmap
from os import path, remove, listdir, symlink, system, access, W_OK

from enigma import eTimer,ePoint,eSize,gFont,eConsoleAppContainer,iServiceInformation,eServiceReference, addFont, getDesktop, iPlayableService, fontRenderClass

from skin import parseColor,parseFont

from time import *
from FileList2 import FileList

#import subprocess,fcntl

config.plugins.AdvancedFreePlayer = ConfigSubsection()
myConfig = config.plugins.AdvancedFreePlayer
myConfig.FileListFontSize = ConfigSelectionNumber(20, 32, 2, default = 24)
myConfig.MultiFramework = ConfigSelection(default = "4097", choices = [("4097", "gstreamer (root 4097)"),("4099", "ffmpeg (root 4099)"),("1", "hardware (root 1)"), ("select", _("Select during start"))])
myConfig.StopService = ConfigYesNo(default = True)
myConfig.InfobarTime = ConfigSelectionNumber(2, 9, 1, default = 5)
myConfig.InfobarOnPause = ConfigYesNo(default = True)
myConfig.DeleteFileQuestion = ConfigYesNo(default = True)
myConfig.DeleteWhenPercentagePlayed = ConfigSelectionNumber(0, 100, 5, default = 80)
myConfig.KeyOK = ConfigSelection(default = "unselect", choices = [("unselect", _("Select/Unselect")),("play", _("Select>Play"))])
myConfig.SRTplayer = ConfigSelection(default = "system", choices = [("system", _("System")),("plugin", _("Plugin"))])
myConfig.TXTplayer = ConfigSelection(default = "plugin", choices = [("convert", _("System after conversion to srt")),("plugin", _("Plugin"))])
myConfig.Version = ConfigSelection(default = "public", choices = [("debug", _("every new version (debug)")),("public", _("only checked versions"))])

#
# hidden atributes to store configuration data
#
myConfig.FileListLastFolder = ConfigText(default = "/hdd/movie", fixed_size = False)
myConfig.StoreLastFolder = ConfigYesNo(default = True)
myConfig.Inits = ConfigText(default = "540,60,Regular,0,1,0", fixed_size = False)
myConfig.PlayerOn = NoSave( ConfigYesNo(default = False))
#position,size,type,color,visibility,background

if path.exists('/usr/local/e2/'):
  KeyMapInfo=_("Player KEYMAP:\n\n\
up/down - position subtitle\n\
left/right - size subtitle\n\
channel up/down - seek+/- subtitle\n\
???3/6/9 - seek+ 30sek/2min/5min movie\n\
???1/4/7 - seek- 30sek/2min/5min movie\n\
F1 - pause on/off\n\
F2 - change background color\n\
F3 - change type font\n\
F4 - change color font\n\
T - show/hide subtitle\n\
D - Download subtitles\n\
F5/SPACE - show about\n\
OK - infobar\n\
audio - change audio track\n\
")
else:
  KeyMapInfo=_("Player KEYMAP:\n\n\
up/down - position subtitle\n\
left/right - size subtitle\n\
channel up/down - seek+/- subtitle\n\
3/6/9 - seek+ 30sek/2min/5min movie\n\
1/4/7 - seek- 30sek/2min/5min movie\n\
play/red - pause on/off\n\
green - change background color\n\
yellow - change type font\n\
blue - change color font\n\
TV - show/hide subtitle\n\
text - Download subtitles\n\
menu/info - show about\n\
ok - infobar\n\
audio - change audio track\n\
")

def LoadSkin(SkinName):
    skinDef=None
    if path.exists("%sskins/%s.xml" % (PluginPath,SkinName)):
        with open("%sskins/%s.xml" % (PluginPath,SkinName),'r') as skinfile:
            skinDef=skinfile.read()
            skinfile.close()
    return skinDef

class AdvancedFreePlayerInfobar(Screen):
    skin = LoadSkin('AdvancedFreePlayerInfobar')
    def __init__(self,session, isPause = False):
        Screen.__init__(self, session)
        
        if isPause == False:
            self["actions"] = ActionMap(["AdvancedFreePlayerInfobar"],
            {
                "CloseInfobar": self.CloseInfobar,
            },-2)
            self.onShown.append(self.__LayoutFinish)
        else:
            self["actions"] = ActionMap(["AdvancedFreePlayerPauseInfobar"],
            {
                "unPause": self.CloseInfobar,
            },-2)
            self.onShown.append(self.__PauseLayoutFinish)
        
    def __LayoutFinish(self):
        self.autoHideTime = 1000 * int(myConfig.InfobarTime.value)
        self.hideOSDTimer = eTimer()
        self.hideOSDTimer.callback.append(self.CloseInfobar)
        self.hideOSDTimer.start(self.autoHideTime, True) # singleshot

    def __PauseLayoutFinish(self):
        printDEBUG('AdvancedFreePlayerInfobar in pause')

    def CloseInfobar(self):
        self.close()

class AdvancedFreePlayer(Screen):
    CUT_TYPE_IN = 0
    CUT_TYPE_OUT = 1
    CUT_TYPE_MARK = 2
    CUT_TYPE_LAST = 3
    ENABLE_RESUME_SUPPORT = True
    VISIBLE = 4
    HIDDEN = 5
    SHOWNSUBTITLE = 6
    HIDDENSUBTITLE = 7

    def __init__(self, session,openmovie,opensubtitle, rootID, LastPlayedService, URLlinkName = ''):
        self.conditionalNotVisible = []
        self.URLlinkName = URLlinkName
        self.PercentagePlayed = 0
        self.frameon = 1 / 24
        self.seeksubtitle = 0
        self.resume_point = 0
        self.nrsubtitle = 0
        self.enablesubtitle = True
        self.statesubtitle = self.HIDDENSUBTITLE
        self.stateplay = ""
        self.stateinfo = self.VISIBLE
        self.oldinfo = ""
        self.openmovie = openmovie
        self.opensubtitle = opensubtitle
        self.rootID = int(rootID)
        self.LastPlayedService = LastPlayedService
        self.subtitle = []
        self.fontpos = 540
        self.fontsize = 60
        self.SubtitleLineHeight=66
        self.fontpos_ = self.fontpos
        self.osdPosX = 0
        self.osdPosY = 0
        self.osdPosX_ = self.osdPosX
        self.osdPosY_ = self.osdPosY
        self.fontsize_ = self.fontsize
        self.fonttype_nr = 0
        self.fonttype_nr_ = self.fonttype_nr
        self.fontcolor_nr = 0
        self.fontcolor_nr_ = self.fontcolor_nr
        self.fontbackground_nr = 0
        self.fontbackground_nr_ = self.fontbackground_nr
        self.fontBackgroundState = 1
        self.fontBackgroundState_ = self.fontBackgroundState
        #load
        self.loadfont()
        self.loadcolor()
        self.loadBackgroundColor()
        self.loadconfig()
        if self.opensubtitle == "":
            self.enablesubtitle = False

        isHD = False
        isWideScreen = False
        isDolby = False
        self.skin = """
<screen name="AdvancedFreePlayer" position="0,0" size="1280,720" title="InfoBar" backgroundColor="transparent" flags="wfNoBorder">
    <!-- SubTitles -->
    <widget name="afpSubtitles" position="0,0" size="1,1" valign="center" halign="center" font="Regular;60" backgroundColor="#ff000000" transparent="0" />
  </screen>"""
        Screen.__init__(self, session)
        self["afpSubtitles"] = Label()

        self["actions"] = ActionMap(["AdvancedFreePlayer"],
            {
                "ToggleInfobar": self.ToggleInfobar,
                "HelpScreen": self.HelpScreen,
                
                "ExitPlayer": self.ExitPlayer,
                "MoveSubsUp": self.MoveSubsUp,
                "MoveSubsDown": self.MoveSubsDown,
                "SetSmallerFont": self.SetSmallerFont,
                "SetBiggerFont": self.SetBiggerFont,
                "pause": self.pause,
                "play": self.play,
                "FastF30s": self.FastF30s,
                "FastF120s": self.FastF120s,
                "FastF300s": self.FastF300s,
                "BackF30s": self.BackF30s,
                "BackF120s": self.BackF120s,
                "BackF300s": self.BackF300s,
                "toggleFontBackground": self.toggleFontBackground,
                "SeekUpSubtitles": self.SeekUpSubtitles,
                "SeekDownSubtitles": self.SeekDownSubtitles,
                "togglePause": self.togglePause,
                "ToggleFont": self.ToggleFont,
                "ToggleFontColor": self.ToggleFontColor,
                "ToggleSubtitles": self.ToggleSubtitles,
                "SelectAudio": self.SelectAudio,
                "SelectSubtitles": self.SelectSubtitles,
            },-2)
        self.onShown.append(self.__LayoutFinish)
        self.onClose.append(self.__onClose)
        if not self.LastPlayedService:
            self.LastPlayedService = self.session.nav.getCurrentlyPlayingServiceReference()
            self.session.nav.stopService()
        self.session.nav.stopService()

    def __onClose(self):
        myConfig.Inits.value = str(self.fontpos) + "," + str(self.fontsize) + "," + \
                                                        str(self.fonttype_list[self.fonttype_nr]) + "," + str(self.fontcolor_nr) + "," + \
                                                        str(self.fontBackgroundState) + "," + str(self.fontbackground_nr)
        myConfig.Inits.save()

        if self.LastPlayedService:
            self.session.nav.playService(self.LastPlayedService)

    def __LayoutFinish(self):
        #print "--> Start of __LayoutFinish"
        self.currentHeight= getDesktop(0).size().height()
        self.currentWidth = getDesktop(0).size().width()
        
        self.onShown.remove(self.__LayoutFinish)
        print "--> Loading subtitles"
        self.loadsubtitle()
        print "End of __LayoutFinish"

    def __getCuesheet(self):
        service = self.session.nav.getCurrentService()
        if service is None:
            return None
        return service.cueSheet()

    def resumeLastPlayback(self):
        #printDEBUG("resumeLastPlayback>>>")
        if not self.ENABLE_RESUME_SUPPORT:
            return

        cue = self.__getCuesheet()
        if cue is None:
            return
        cut_list = cue.getCutList()
        print cut_list

        last = None
        for (pts, what) in cut_list:
            if what == self.CUT_TYPE_LAST:
                last = pts
                break
            if last is None:
                return
        
        # only resume if at least 10 seconds ahead, or <10 seconds before the end.
        seekable = self.__getSeekable()
        if seekable is None:
            return  # Should not happen?
        length = seekable.getLength() or (None, 0)
        print "seekable.getLength() returns:", length
        # Hmm, this implies we don't resume if the length is unknown...
        if (last > 900000) and (not length[1]  or (last < length[1] - 900000)):
            self.resume_point = last
            l = last / 90000
            self.playLastCB(True)
    
    def playLastCB(self, answer):
        if answer == True:
            try:
                print "resuming from %d" % (self.resume_point/90000)
                self.doSeek(self.resume_point)
            except:
                pass
#        self.hideAfterResume()

    def go(self):
        self.timer = eTimer()
        self.timer.callback.append(self.timerEvent)
        self.timer.start(200, False)
        printDEBUG("Playing: " + str(self.rootID) + ":0:0:0:0:0:0:0:0:0:" + self.openmovie)
        root = eServiceReference(self.rootID, 0, self.openmovie)
        self.session.nav.playService(root)
        myConfig.PlayerOn.value = True
        self.stateplay = "Play"
        self["afpSubtitles"].instance.move(ePoint(0,self.fontpos))
        self["afpSubtitles"].instance.setForegroundColor(parseColor(self.fontcolor_list[self.fontcolor_nr]))
        self["afpSubtitles"].instance.setBackgroundColor(parseColor(self.backgroundcolor_list[self.fontbackground_nr]))
        self["afpSubtitles"].instance.setFont(gFont(self.fonttype_list[self.fonttype_nr], self.fontsize))
        self.SubtitleLineHeight = int(fontRenderClass.getInstance().getLineHeight(self["afpSubtitles"].instance.getFont()))
        if self.SubtitleLineHeight > self.fontsize:
            printDEBUG("SubtitleLineHeight calculated: %d" % self.SubtitleLineHeight)
        else:
            self.SubtitleLineHeight = int(self.fontsize * 1.1)
            printDEBUG("SubtitleLineHeight assumed: %d" % self.SubtitleLineHeight)
        self.ToggleInfobar()
            
        #print "End of go"

    def loadfont(self):
        self.fonttype_list = []
        self.fonttype_list.append("Regular")
          
        fonts = []
        fonts_paths =[ "/usr/share/fonts/" , PluginPath + "fonts/"]
        for font_path in fonts_paths:
            if path.exists(font_path):
                for file in listdir(font_path):
                    if file.lower().endswith(".ttf") and file not in fonts:
                        fonts.append( (font_path + '/' + file, file))
                        addFont(font_path + '/' + file, file, 100, False)
        fonts.sort()
        for font in fonts:
            self.fonttype_list.append(font[1])  

    def loadcolor(self):
        self.fontcolor_list = []
        self.fontcolor_list.append("white")
        if path.exists(PluginPath + 'colors.ini'):
            o = open(PluginPath + 'colors.ini','r')
            while True:
                l = o.readline()
                if len(l) == 0: break
                l = l.strip()
                #print l
                self.fontcolor_list.append(l)
            o.close()

    def loadBackgroundColor(self):
        self.backgroundcolor_list = []
        self.backgroundcolor_list.append("#ff000000")
        if path.exists(PluginPath + 'backgrounds.ini'):
            with open(PluginPath + 'backgrounds.ini','r') as o:
                for l in o:
                    if len(l) > 0:
                        l = l.strip()
                        #print l
                        self.backgroundcolor_list.append(l)
                o.close()

    def loadconfig(self):
        try:
            configs=myConfig.Inits.value.split(',')
        except:
            return
            
        self.fontpos = int(configs[0])
        self.fontsize = int(configs[1])
        
        self.fonttype_nr = 0
        tmp = configs[2]
        
        self.fontcolor_nr = int(configs[3])
        self.fontBackgroundState = int(configs[4])
        self.fontbackground_nr = int(configs[5])

    def convertTime(self, time):
#        print "convertTime:"+str(time)
        if time is None:
            time=0
        s = "%d:%02d:%02d" % ((time/3600/90000), (time/90000)%3600/60, (time/90000)%60)
        return s

    def timerEvent(self):
        lCurrent = self.GetCurrentPosition() or 0
        #printDEBUG("lCurrent=%d" % lCurrent)
        if not lCurrent is None:
            self.showsubtitle(lCurrent)

    def showsubtitle(self,tim):
        if self.enablesubtitle == False:
            return
        tim = tim + (self.seeksubtitle * 90000) #current position + movement
        for pos in self.subtitle:
            nr=pos[0]
            start=pos[1]
            stop=pos[2]
            text=pos[3]
            if tim >= start and tim < stop and (nr > self.nrsubtitle  or self.nrsubtitle == 0):
                self.nrsubtitle = nr
                self.setTextForAllLInes(text)
                self.statesubtitle = self.SHOWNSUBTITLE
                printDEBUG ("%d Show %d %d --> %d\t%s" %(tim, nr, start, stop, text) )
            elif tim > stop and nr == self.nrsubtitle:
                if self.statesubtitle == self.SHOWNSUBTITLE:
                    self.setTextForAllLInes("")
                    self.statesubtitle = self.HIDDENSUBTITLE
                    printDEBUG ("%d Hide %d %d --> %d\t%s" %(tim, nr, start, stop, text) )

    def usun(self,l):
        if len(l) > 0:
            if l[0] == "{":
                p = l.find("}")
                if p != -1:
                    l = l[p+1:]
                    return l
        return l

    def loadsubtitle(self):
        if path.exists(self.opensubtitle):
            temp = self.opensubtitle[-4:]
            if temp == ".srt":
                self.loadsrt()
                self.go()
            else:
                self.loadtxt_type()
        else:
            self.go()

    def loadtxt_type(self):
        printDEBUG("loadtxt_type>>> '%s'" % self.opensubtitle)
        try:
            o = open(self.opensubtitle,'r')
            l = o.readline()
            o.close()
            if l[0] == "{":
                printDEBUG("[FP] Load subtitle TXT mDVD")
                oo = open(self.openmovie,'r')
                d = oo.read(250)
                oo.close()
                if d[0] == "R" and d.find("strlstrh") != -1:
                    print "AVI RIFF"
                    temp = d.find("strlstrh")
                    l4 = ord(d[temp+32])
                    l3 = ord(d[temp+33])
                    l2 = ord(d[temp+34])
                    l1 = ord(d[temp+35])
                    #print "%x" %l1
                    #print "%x" %l2
                    #print "%x" %l3
                    #print "%x" %l4
                    l1 = l1 << 24
                    l2 = l2 << 16
                    l3 = l3 << 8
                    dwscale = float(l1 + l2 + l3 + l4)
                    #print "%x" % dwscale
                    l4 = ord(d[temp+36])
                    l3 = ord(d[temp+37])
                    l2 = ord(d[temp+38])
                    l1 = ord(d[temp+39])
                    #print "%x" %l1
                    #print "%x" %l2
                    #print "%x" %l3
                    #print "%x" %l4
                    l1 = l1 << 24
                    l2 = l2 << 16
                    l3 = l3 << 8
                    dwrate = float(l1 + l2 + l3 + l4)
                    #print "%x" % dwrate
                    framerate = dwrate / dwscale
                    print "framerate =",framerate
                    self.frameone = 1 / framerate
                else:
                    printDEBUG("Unkown AVI - set manual framerate")
                    self.session.openWithCallback(self.framerateCallback, ChoiceBox, \
                    title=_("AdvancedFreePlayer not found framerate in movie.\nPlease select manual framerate !"), \
                    list=[["23.0","23.0"],["23.5","23.5"],["23.976","23.976"],["24.0","24.0"],["24.5","24.5"],["25.0","25.0"]])
                    return
            elif l[0] == "[":
                printDEBUG("[FP] Load subtitle TXT mpl2")
            elif l[1] == ":":
                print "[FP] Load subtitle TXT tmp 0:00:00"
            elif l[2] == ":":
                print "[FP] Load subtitle TXT tmp 00:00:00"
            else:
                print "[FP] Load subtitle unkown TXT - not load"
                self.go()
                return
            self.loadtxt()
            self.go()
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
            printDEBUG("Error loadtxt_type, I/O error({0}): {1}".format(e.errno, e.strerror) )
            try:
                o.close()
                oo.close()
            except:
                pass
            self.session.open(MessageBox,_("Error load subtitle !!!"),  MessageBox.TYPE_ERROR)
            self.go()

    def framerateCallback(self,val):
        if val is not None:
            print "Manual framerate = ",val[1]
            a = float(val[1])
            self.frameone = 1 / a
        self.loadtxt()
        self.go()

    def loadtxt(self):
        try:
            self.subtitle = []
            o = open(self.opensubtitle,'r')
            nr = 1
            while True:
                l = o.readline()
                if len(l) == 0:break
                if ord(l[0]) == 13: continue
                if l == "\n": continue
                l = l.strip()
                #tmp
                if l[1] == ":": #0:00:00
                    tim1_h = int(l[0:1])
                    tim1_m = int(l[2:4])
                    tim1_s = int(l[5:7])
                    t1 = ((((int(tim1_h) * 3600) + (int(tim1_m) * 60) + int(tim1_s))*1000))*90
                    l = l[8:]
                    if len(l)==0:continue
                    l = l.decode('windows-1250').encode('utf-8')
                    l = l.replace('/','')
                    l = l.replace('|','\n')
                    #ustalenie czasu wyswietlania napisow
                    seek=o.tell()
                    ll = o.readline()
                    if len(ll) == 0:break
                    o.seek(seek)
                    tim2_h = int(ll[0:1])
                    tim2_m = int(ll[2:4])
                    tim2_s = int(ll[5:7])
                    t2 = ((((int(tim2_h) * 3600) + (int(tim2_m) * 60) + int(tim2_s))*1000))*90
                    z = len(l)
                    if z <= 10:
                        z = 1
                    elif z > 10 and z <= 20:
                        z = 3
                    else:
                        z = 5
                    t3 = t1 + (90000 * z)
                    if t3 < t2:
                        t2 = t3
                    #print "-"
                elif l[2] == ":": #00:00:00
                    tim1_h = int(l[0:2])
                    tim1_m = int(l[3:5])
                    tim1_s = int(l[6:8])
                    t1 = ((((int(tim1_h) * 3600) + (int(tim1_m) * 60) + int(tim1_s))*1000))*90
                    l = l[9:]
                    if len(l)==0:continue
                    l = l.decode('windows-1250').encode('utf-8')
                    l = l.replace('/','')
                    l = l.replace('|','\n')
                    #ustalenie czasu wyswietlania napisow
                    seek=o.tell()
                    ll = o.readline()
                    if len(ll) == 0:break
                    o.seek(seek)
                    tim2_h = int(ll[0:1])
                    tim2_m = int(ll[2:4])
                    tim2_s = int(ll[5:7])
                    t2 = ((((int(tim2_h) * 3600) + (int(tim2_m) * 60) + int(tim2_s))*1000))*90
                    z = len(l)
                    if z <= 10:
                        z = 1
                    elif z > 10 and z <= 20:
                        z = 3
                    else:
                        z = 5
                    t3 = t1 + (90000 * z)
                    if t3 < t2:
                        t2 = t3
                    #print "-"
                #mpl2
                elif l[0] == "[":
                    t1 = int(l[1:l.find(']')])
                    l = l[l.find(']')+1:]
                    t2 = int(l[1:l.find(']')])
                    l = l[l.find(']')+1:]
                    if len(l)==0:continue
                    l = l.decode('windows-1250').encode('utf-8')
                    l = l.replace('/','')
                    l = l.replace('|','\n')
                    t1 = t1 * 9000
                    t2 = t2 * 9000
                    #print t1
                    #print t2
                    #print l
                #mdvd
                elif l[0] == "{":
                    t1 = int(l[1:l.find('}')])
                    l = l[l.find('}')+1:]
                    t2 = int(l[1:l.find('}')])
                    l = l[l.find('}')+1:]
                    if len(l)==0:continue
                    l = l.decode('windows-1250').encode('utf-8')
                    l = l.replace('/','')
                    l = l.replace('|','\n')
                    t1 = t1 * self.frameone * 100
                    t2 = t2 * self.frameone * 100
                    t1 = int(t1) * 900
                    t2 = int(t2) * 900
                    #print t1
                    #print t2
                    #print l
                else:
                    continue
                l = self.usun(l)
                l = self.usun(l)
                self.subtitle.append([int(nr),t1,t2,l])
                nr = nr + 1
            o.close()
        except IOError as e:
            self.subtitle = []
            o.close()
            print "Error loadtxt"
            self.session.open(MessageBox,"Error load subtitle !!!",  MessageBox.TYPE_ERROR, timeout=5)

    def loadsrt(self):
        self.subtitle = []
        #printDEBUG("[FP] Load subtitle STR")
        try:
            if path.exists(self.opensubtitle):
                o = open(self.opensubtitle,'r')
                # BOM removal, if exists
                while True:
                    d = o.read(1)
                    if d == "1":
                        o.seek(-1,1)
                        break
                while True:
                    nr = o.readline().replace("\r\n","\n")
                    #printDEBUG(nr)
                    if len(nr) == 0:break
                    if nr == "\n": continue
                    nr = nr.strip()
                    tim = o.readline().replace("\r\n","\n")
                    if len(tim) == 0:break
                    tim = tim.strip()
                    #printDEBUG(tim)
                    l1 = o.readline().replace("\r\n","\n")
                    if len(l1) == 0:break
                    l1 = l1.strip()
                    l2 = o.readline().replace("\r\n","\n")
                    if len(l2) == 0:break
                    if not l2 == "\n":
                        l2 = l2.strip()
                        l = l1 + "\n" + l2
                        l3 = o.readline().replace("\r\n","\n")
                        if len(l3) == 0:break
                        if not l3 == "\n":
                            l3 = l3.strip()
                            l = l1 + "\n " + l2 + "\n" + l3
                            l4 = o.readline().replace("\r\n","\n")
                            if len(l4) == 0:break
                            if not l4 == "\n":
                                l4 = l4.strip()
                                l = l1 + "\n " + l2 + "\n" + l3 + "\n" + l4
                                n = o.readline().replace("\r\n","\n")
                                if len(n) == 0:break
                    else:
                        l = l1
                    l = self.usun(l)
                    l = self.usun(l)
                    tim1=tim[0:12]
                    tim1_h = tim1[0:2]
                    tim1_m = tim1[3:5]
                    tim1_s = tim1[6:8]
                    tim1_ms = tim1[9:12]
                    tim_1 = ((((int(tim1_h) * 3600) + (int(tim1_m) * 60) + int(tim1_s))*1000)+int(tim1_ms))*90
                    tim2=tim[17:29]
                    tim2_h = tim2[0:2]
                    tim2_m = tim2[3:5]
                    tim2_s = tim2[6:8]
                    tim2_ms = tim2[9:12]
                    tim_2 = ((((int(tim2_h) * 3600) + (int(tim2_m) * 60) + int(tim2_s))*1000)+int(tim2_ms))*90
                    self.subtitle.append([int(nr),tim_1,tim_2,l])
                o.close()
        except Exception as e:
            if myConfig.Version == "debug":
                raise
            self.subtitle = []
            printDEBUG("Error loadsrt %s" % str(e) )
            try:
                o.close()
            except:
                pass
            self.session.open(MessageBox,"Error load subtitle !!!",  MessageBox.TYPE_ERROR, timeout=5)

    def __getSeekable(self):
        service = self.session.nav.getCurrentService()
        if service is None:
            return None
        return service.seek()

    def GetCurrentPosition(self):
        seek = self.__getSeekable()
        if seek is None:
            return None
        r = seek.getPlayPosition()
        if r[0]:
            return None
        return long(r[1])

    def GetCurrentLength(self):
        seek = self.__getSeekable()
        if seek is None:
            return None
        r = seek.getLength()
        if r[0]:
            return None
        return long(r[1])

    def getSeek(self):
        service = self.session.nav.getCurrentService()
        if service is None:
            return None
        seek = service.seek()
        if seek is None or not seek.isCurrentlySeekable():
            return None
        return seek

    def doSeek(self, pts):
        print "..- doSeek Start %d" % (pts/90000)
        seekable = self.getSeek()
        if seekable is None:
            return
        print "..- doSeek %d" % (pts/90000)
        seekable.seekTo(pts)

    def doSeekRelative(self, pts):
        print "..- doSeekRelative Start %d" % (pts/90000)
        seekable = self.getSeek()
        if seekable is None:
            return
        print "..- doSeekRelative %d" % (pts/90000)
        seekable.seekRelative(pts<0 and -1 or 1, abs(pts))
        self.nrsubtitle = 0 #reset position

    def SeekSubtitles(self, position):
        self.seeksubtitle = self.seeksubtitle + position
        self.setTextForAllLInes(str(self.seeksubtitle)+" sek")
        self.nrsubtitle = 0 #reset position

    def SeekUpSubtitles(self):
        self.SeekSubtitles(+0.5)

    def SeekDownSubtitles(self):
        self.SeekSubtitles(-0.5)

    def FastF30s(self):
        if self.stateplay == "Play":
            self.doSeekRelative(30 * 90000)

    def FastF120s(self):
        if self.stateplay == "Play":
            self.doSeekRelative(2 * 60 * 90000)

    def FastF300s(self):
        if self.stateplay == "Play":
            self.doSeekRelative(5 * 60 * 90000)

    def BackF30s(self):
        if self.stateplay == "Play":
            self.doSeekRelative(- 30 * 90000)

    def BackF120s(self):
        if self.stateplay == "Play":
            self.doSeekRelative(- 2 * 60 * 90000)

    def BackF300s(self):
        if self.stateplay == "Play":
            self.doSeekRelative(- 5 * 60 * 90000)

    def ToggleSubtitles(self):
        if self.enablesubtitle == True:
            self.enablesubtitle = False
            self.setTextForAllLInes("")
        else:
            self.enablesubtitle = True

    def HelpScreen(self):
        self.session.open(MessageBox,PluginName + ' ' + PluginInfo +"\n\n"+ KeyMapInfo,  MessageBox.TYPE_INFO)

    def SelectAudio(self):
        from Screens.AudioSelection import AudioSelection
        self.session.openWithCallback(self.audioSelected, AudioSelection, infobar=self)

    def audioSelected(self, ret=None):
        print "[AdvancedFreePlayer infobar::audioSelected]", ret

########################################################################################### funkcje START
    def updateTextBackground(self, element, text):
        showBackgroud = self.fontBackgroundState
        if not text:
            showBackgroud = False
        self.setVisible(showBackgroud, element)

    def setTextForAllLInes(self, text):
        textWidth = 0
        text = text.strip()
        if text == '':
            self["afpSubtitles"].setText('')
            self["afpSubtitles"].hide()
        else:
            linesNO = text.count('\n') + 1
            if linesNO == 1:
                textWidth = len(text)
            else:
                for line in text.split('\n'):
                    tempLen = len(line)
                    if tempLen > textWidth:
                        textWidth = tempLen 
                        
            self["afpSubtitles"].setText(text)
            textWidth *= int(self.fontsize * 0.75) # The best would be to calculate real width, but don't know how to do it. :(
            center = int( (self.currentWidth - textWidth) /2 )
            self["afpSubtitles"].instance.resize(eSize(textWidth, linesNO * self.SubtitleLineHeight) )
            self["afpSubtitles"].instance.move(ePoint(center, self.fontpos ) )
            self["afpSubtitles"].show()

    def setVisible(self, visible, component):
        if visible:
            if component not in self.conditionalNotVisible:
                component.show()
        else:
            component.hide()

    def isNotFontLine(self, component):
        if self["afpSubtitles"] is component:
            return False
        return True

    def ExitPlayer(self):
        def DeleteFile(f2d):
            try:
                remove(f2d)
                printDEBUG("Deleting %s" % f2d)
            except:
                printDEBUG("Error deleting %s" % f2d)
                
        self.stateplay = "Stop"
        try:
            self.timer.stop()
        except:
            pass
        self.session.nav.stopService()
        print "Played %d" % self.PercentagePlayed
        if self.URLlinkName == '' and not access(self.openmovie, W_OK):
            printDEBUG("No access to delete %s" % self.openmovie)
        elif self.URLlinkName != '' and not access(self.URLlinkName, W_OK):
            printDEBUG("No access to delete %s" % self.URLlinkName)
        if path.exists('/tmp/afpsubs.srt'):    
            DeleteFile('/tmp/afpsubs.srt')
            
        elif myConfig.DeleteFileQuestion.value == True or (self.PercentagePlayed >= int(myConfig.DeleteWhenPercentagePlayed.value) and int(myConfig.DeleteWhenPercentagePlayed.value) >0):
            def ExitRet(ret):
                if ret:
                    if self.URLlinkName == '':
                        myDir = path.dirname(self.openmovie)
                        myFile = getNameWithoutExtension(path.basename(self.openmovie)) #To delete all files e.g. txt,jpg,eit,etc
                        if path.exists(self.openmovie):
                            DeleteFile(self.openmovie)
                        if path.exists(self.opensubtitle):
                            DeleteFile(self.opensubtitle)
                        if path.exists(myDir + '/' + myFile + ".jpg"):
                            DeleteFile(myDir + '/' + myFile + ".jpg")
                        if path.exists(myDir + '/' + myFile + ".eit"):
                            DeleteFile(myDir + '/' + myFile + ".eit")
                        if path.exists(myDir + '/' + myFile + ".txt"):
                            DeleteFile(myDir + '/' + myFile + ".txt")
                        if self.openmovie.endswith('.ts'):
                            if path.exists(self.openmovie + ".ap"):
                                DeleteFile(self.openmovie + ".ap")
                            if path.exists(self.openmovie + ".meta"):
                                DeleteFile(self.openmovie + ".meta")
                            if path.exists(self.openmovie + ".sc"):
                                DeleteFile(self.openmovie + ".sc")
                        try:
                            printDEBUG("Executing 'rm -f \"%s/%s.*\"'" %(myDir,myFile))
                            ClearMemory() #some tuners (e.g. nbox) with small amount of RAM have problems with next command
                            system('rm -f "%s/%s*"' %(myDir,myFile))
                        except:
                            printDEBUG("Error executing system>delete files engine")
                            
                    else:
                        printDEBUG("Deleting %s" % self.URLlinkName)
                        if path.exists(self.URLlinkName):
                            DeleteFile(self.URLlinkName)

            self.session.openWithCallback(ExitRet, MessageBox, _("Delete this movie?"), timeout=10, default=False)

        self.close()

##################################################################### RELOADING SUBTITLES >>>>>>>>>>
    def dmnapisubsCallback(self, answer=None):
        printDEBUG("SelectSubtitles:dmnapiCallback")
        if answer:
            with open('/tmp/afpsubs.srt','w') as mysrt:
                mysrt.write(answer)
                mysrt.close
            self.opensubtitle = '/tmp/afpsubs.srt'
            self.loadsrt()
            self.enablesubtitle = True
            
        self.play()
        
    def SelectSubtitles(self):
                
        self.pause(False)
        try:
            from Plugins.Extensions.DMnapi.DMnapisubs import DMnapisubs
            self.session.openWithCallback(self.dmnapisubsCallback, DMnapisubs, self.openmovie, save = False)
        except:
            printDEBUG("Exception loading DMnapi!!!")

##################################################################### CHANGE FONT SIZE >>>>>>>>>>
    def setFontSize(self, fontSize):
        self.fontsize = self.fontsize + fontSize
        if self.fontsize < 10:
            self.fontsize = 10
        elif  self.fontsize > 80:
            self.fontsize = 80
        self["afpSubtitles"].instance.setFont(gFont(self.fonttype_list[self.fonttype_nr], self.fontsize))
        self.SubtitleLineHeight= int(fontRenderClass.getInstance().getLineHeight(self["afpSubtitles"].instance.getFont()))
        self.setTextForAllLInes(_("Font %s\nSize %s\nLine3") % (self.fonttype_list[self.fonttype_nr],self.fontsize))

    def SetSmallerFont(self):
        self.setFontSize( -2 )

    def SetBiggerFont(self):
        self.setFontSize(2)

##################################################################### TOGGLE INFOBAR >>>>>>>>>>

    def ToggleInfobar(self): #### old info
        def RetFromInfobar():
            pass
        self.session.openWithCallback(RetFromInfobar,AdvancedFreePlayerInfobar)
        return
##################################################################### TOGGLE FONT BACKGROUND >>>>>>>>>>
    def toggleFontBackground(self):
        self.fontbackground_nr = self.fontbackground_nr + 1
        if self.fontbackground_nr == len(self.backgroundcolor_list):
            self.fontbackground_nr = 0
        self["afpSubtitles"].instance.setBackgroundColor(parseColor(self.backgroundcolor_list[self.fontbackground_nr]))
        self.setTextForAllLInes(_("Background ")+str(self.fontbackground_nr))
      
##################################################################### TOGGLE FONT COLOR >>>>>>>>>>
    def ToggleFontColor(self):
        self.fontcolor_nr = self.fontcolor_nr + 1
        if self.fontcolor_nr == len(self.fontcolor_list):
            self.fontcolor_nr = 0
        self["afpSubtitles"].instance.setForegroundColor(parseColor(self.fontcolor_list[self.fontcolor_nr]))

        self.setTextForAllLInes(_("Color ")+str(self.fontcolor_nr))

##################################################################### TOGGLE FONT  >>>>>>>>>>
    def ToggleFont(self):
        self.fonttype_nr = self.fonttype_nr + 1
        if self.fonttype_nr == len(self.fonttype_list):
            self.fonttype_nr = 0
        self["afpSubtitles"].instance.setFont(gFont(self.fonttype_list[self.fonttype_nr], self.fontsize))

        self.setTextForAllLInes(self.fonttype_list[self.fonttype_nr])

##################################################################### TOGGLE PAUSE >>>>>>>>>>
    def togglePause(self):
        if self.stateplay == "Play":
            self.pause()
        elif self.stateplay == "Pause":
            self.play()

    def pause(self, ShowInfobar = True ):
        if not self.stateplay == "Play":
            return
        cs = self.session.nav.getCurrentService()
        if cs is None:
            return
        pauseable = cs.pause()
        if pauseable is None:
            return
        pauseable.pause()
        self.stateplay = "Pause"
        if myConfig.InfobarOnPause.value == True and ShowInfobar == True:
            self.session.openWithCallback(self.play,AdvancedFreePlayerInfobar,isPause = True)
            return

    def play(self):
        if not self.stateplay == "Pause":
            return
        cs = self.session.nav.getCurrentService()
        if cs is None:
            return
        pauseable = cs.pause()
        if pauseable is None:
            return
        pauseable.unpause()
        self.stateplay = "Play"

##################################################################### MOVE SUBTITLES UP/DOWN >>>>>>>>>>
    def updateSubtitlePosition(self, fotpos):
        self.fontpos = self.fontpos + fotpos
        #print "pos y = ",self.fontpos
        self.setTextForAllLInes(_("Line1\nLine2\nLine3"))

    def MoveSubsUp(self):
        self.updateSubtitlePosition(-5)

    def MoveSubsDown(self):
        self.updateSubtitlePosition(+5)
##################################################################### CLASS END #####################################################################

class AdvancedFreePlayerStart(Screen):

    def __init__(self, session):
        #printDEBUG("AdvancedFreePlayerStart >>>")
        self.sortDate = False
        self.openmovie = ''
        self.opensubtitle = ''
        self.URLlinkName = ''
        self.movietxt = _('Movie: ')
        self.subtitletxt = _('Subtitle: ')
        self.rootID = myConfig.MultiFramework.value
        self.LastPlayedService = None
        self.LastFolderSelected= None
  
        self.skin  = LoadSkin("AdvancedFreePlayerStart")
        
        Screen.__init__(self, session)
        self["info"] = Label()
        self["myPath"] = Label(myConfig.FileListLastFolder.value)
        
        self["filemovie"] = Label(self.movietxt)
        self["filesubtitle"] = Label(self.subtitletxt)
        self["key_red"] = StaticText(_("Play"))
        self["Description"] = Label(KeyMapInfo)
        self["Cover"] = Pixmap()
        
        if path.exists(ExtPluginsPath + '/DMnapi/DMnapi.pyo') or path.exists(ExtPluginsPath +'/DMnapi/DMnapi.pyc') or path.exists(ExtPluginsPath +'/DMnapi/DMnapi.py'):
            self.DmnapiInstalled = True
            self["key_green"] = StaticText(_("DMnapi"))
        else:
            self.DmnapiInstalled = False
            self["key_green"] = StaticText(_("Install DMnapi"))
            
        self["key_yellow"] = StaticText(_("Config"))
        self["key_blue"] = StaticText(_("Sort by name"))
        self["info"].setText(PluginName + ' ' + PluginInfo)
        self.filelist = FileList(myConfig.FileListLastFolder.value, matchingPattern = "(?i)^.*\.(avi|txt|srt|mpg|vob|divx|m4v|mkv|mp4|dat|mov|ts|url)(?!\.(cuts|ap$|meta$|sc$))",sortDate=False)
        self["filelist"] = self.filelist
        self["actions"] = ActionMap(["AdvancedFreePlayerSelector"],
            {
                "selectFile": self.selectFile,
                "ExitPlayer": self.ExitPlayer,
                "lineUp": self.lineUp,
                "lineDown": self.lineDown,
                "pageUp": self.pageUp,
                "pageDown": self.pageDown,
                "PlayMovie": self.PlayMovie,
                "runDMnapi": self.runDMnapi,
                "runConfig": self.runConfig,
                "setSort": self.setSort
            },-2)
        self.setTitle(PluginName + ' ' + PluginInfo)
        if myConfig.StopService.value == True:
            self.LastPlayedService = self.session.nav.getCurrentlyPlayingServiceReference()
            self.session.nav.stopService()

    def pageUp(self):
        self["filelist"].pageUp()

    def pageDown(self):
        self["filelist"].pageDown()

    def lineUp(self):
        self["filelist"].up()

    def lineDown(self):
        self["filelist"].down()

    def PlayMovie(self):
        if not self.openmovie == "":
            myConfig.FileListLastFolder.value =  self["myPath"].getText()
            myConfig.FileListLastFolder.save()
            print self["myPath"].getText()
            if not path.exists(self.openmovie + '.cuts'):
                self.SelectFramework()
            elif path.getsize(self.openmovie + '.cuts') == 0:
                self.SelectFramework()
            else:
                self.session.openWithCallback(self.ClearCuts, MessageBox, _("Do you want to resume this playback?"), timeout=10, default=True)

    def ClearCuts(self, ret):
        if ret == False:
            remove(self.openmovie + '.cuts')
        self.SelectFramework()

    def SelectFramework(self):
        if myConfig.MultiFramework.value == "select":
            from Screens.ChoiceBox import ChoiceBox
            self.session.openWithCallback(self.SelectedFramework, ChoiceBox, title = _("Select Multiframework"), list = [("gstreamer (root 4097)","4097"),("ffmpeg (root 4099)","4099"),])
        else:
            if self.openmovie.endswith('.ts'):
                self.rootID = '1'
            else:
                self.rootID = myConfig.MultiFramework.value
            self.StartPlayer()

    def SelectedFramework(self, ret):
        if ret:
            self.rootID = ret[1]
            printDEBUG("Selected framework: " + ret[1])
        self.StartPlayer()
      
    def StartPlayer(self):
        lastOPLIsetting = None
        lastDMNAPIsetting = None
        
        def EndPlayer():
            if lastOPLIsetting is not None:
                config.subtitles.pango_autoturnon.valu = lastOPLIsetting
            if lastDMNAPIsetting is not None:
                config.plugins.dmnapi.autosrton.value = lastDMNAPIsetting
            self["filelist"].refresh()

        if not path.exists(self.opensubtitle) and not self.opensubtitle.startswith("http://"):
            self.opensubtitle = ""
        if path.exists(self.openmovie) or self.openmovie.startswith("http://"):
            if myConfig.SRTplayer.value =="system":
                try: 
                    lastOPLIsetting = config.subtitles.pango_autoturnon.value
                    config.subtitles.pango_autoturnon.value = True
                except: pass
                if self.DmnapiInstalled == True:
                    try:
                        lastDMNAPIsetting = config.plugins.dmnapi.autosrton.value
                        config.plugins.dmnapi.autosrton.value = True
                        printDEBUG("DMNapi subtitles enabled")
                    except: pass
                self.session.openWithCallback(EndPlayer,AdvancedFreePlayer,self.openmovie,'',self.rootID,self.LastPlayedService,self.URLlinkName)
                return
            else:
                try: 
                    lastOPLIsetting = config.subtitles.pango_autoturnon.value
                    config.subtitles.pango_autoturnon.value = False
                    printDEBUG("OpenPLI subtitles disabled")
                except: printDEBUG("pango_autoturnon non existent, is it VTI?")
                if self.DmnapiInstalled == True:
                    try:
                        lastDMNAPIsetting = config.plugins.dmnapi.autosrton.value
                        config.plugins.dmnapi.autosrton.value = False
                        printDEBUG("DMNapi subtitles disabled")
                    except: pass
                self.session.openWithCallback(EndPlayer,AdvancedFreePlayer,self.openmovie,self.opensubtitle,self.rootID,self.LastPlayedService,self.URLlinkName)
                return
        else:
            printDEBUG("StartPlayer>>> File %s does not exist :(" % self.openmovie)

    def runConfig(self):
        from AdvancedFreePlayerConfig import AdvancedFreePlayerConfig
        self.session.open(AdvancedFreePlayerConfig)
        return

    def setSort(self):
        if self.sortDate:
            #print "sortDate=False"
            self["filelist"].sortDateDisable()
            self.sortDate=False
            self["key_blue"].setText(_("Sort by name"))
        else:
            #print "sortDate=True"
            self["filelist"].sortDateEnable()
            self.sortDate=True
            self["key_blue"].setText(_("Sort by date"))
        self["filelist"].refresh()

    def selectFile(self):
        selection = self["filelist"].getSelection()
        if selection[1] == True: # isDir
            if len(selection[0]) > len(self.filelist.getCurrentDirectory()) or self.LastFolderSelected == None:
                self.LastFolderSelected = selection[0]
                self["filelist"].changeDir(selection[0], "FakeFolderName")
            else:
                print "Folder Down"
                self["filelist"].changeDir(selection[0], self.LastFolderSelected)
            
            d = self.filelist.getCurrentDirectory()
            if d is None:
                d=""
            elif not d.endswith('/'):
                d +='/'
            #self.title = d
            self["myPath"].setText(d)
        else:
            d = self.filelist.getCurrentDirectory()
            f = self.filelist.getFilename()
            printDEBUG("self.selectFile>> " + d + f)
            temp = self.getExtension(f)
            #print temp
            if temp == ".url":
                self.opensubtitle = ''
                self.openmovie = ''
                with open(d + f,'r') as UrlContent:
                    for data in UrlContent:
                        print data
                        if data.find('movieURL=') > -1: #find instead of startswith to avoid BOM issues ;)
                            self.openmovie = data.split('=')[1].strip()
                            self.URLlinkName = d + f
                        elif data.find('srtURL=') > -1:
                            self.opensubtitle = data.split('=')[1].strip()
                if self["filemovie"].getText() != (self.movietxt + self.openmovie):
                    self["filemovie"].setText(self.movietxt + self.openmovie)
                    self["filesubtitle"].setText(self.subtitletxt + self.opensubtitle)
                    global PercentagePlayed
                    PercentagePlayed = 0
                elif myConfig.KeyOK.value == 'play':
                    self.PlayMovie()
                    return
                else:
                    self.openmovie = ''
                    self["filemovie"].setText(self.movietxt)
                    self.opensubtitle = ''
                    self["filesubtitle"].setText(self.subtitletxt + self.opensubtitle)
            elif temp == ".srt" or temp == ".txt":
                #if self.DmnapiInstalled == True:
                if self.opensubtitle == (d + f): #clear subtitles selection
                    self["filesubtitle"].setText(self.subtitletxt)
                    self.opensubtitle = ''
                else:
                    self["filesubtitle"].setText(self.subtitletxt + f)
                    self.opensubtitle = d + f
            else:
                if self.openmovie == (d + f):
                    if myConfig.KeyOK.value == 'play':
                        self.PlayMovie()
                        return
                    else:
                        self.openmovie = ''
                        self["filemovie"].setText(self.movietxt)
                else:
                    global PercentagePlayed
                    PercentagePlayed = 0
                    self.openmovie = d + f
                    self["filemovie"].setText(self.movietxt + f)
                    self.URLlinkName = ''
                
                self.SetDescriptionAndCover(self.openmovie)
                
                #if self.DmnapiInstalled == True:
                temp = f[:-4]
                if path.exists( d + temp + ".srt"):
                    self["filesubtitle"].setText(self.subtitletxt + temp + ".srt")
                    self.opensubtitle = d + temp + ".srt"
                elif path.exists( d + temp + ".txt"):
                    self["filesubtitle"].setText(self.subtitletxt + temp + ".txt")
                    self.opensubtitle = d + temp + ".txt"
                else:
                    self["filesubtitle"].setText(self.subtitletxt)
                    self.opensubtitle = ''
                #else:
                #    self.opensubtitle = ''
      
    def getExtension(self, MovieNameWithExtension):
        return path.splitext( path.basename(MovieNameWithExtension) )[1]
      
    def SetDescriptionAndCover(self, MovieNameWithPath):
        if MovieNameWithPath == '':
            self["Cover"].hide()
            self["Description"].setText('')
            return
        
        temp = getNameWithoutExtension(MovieNameWithPath)
        ### COVER ###
        if path.exists(temp + '.jpg'):
            self["Cover"].instance.setScale(1)
            self["Cover"].instance.setPixmap(LoadPixmap(path=temp + '.jpg'))
            self["Cover"].show()
        else:
            self["Cover"].hide()
            
        ### DESCRIPTION from EIT ###
        if path.exists(temp + '.eit'):
            def parseMJD(MJD):
                # Parse 16 bit unsigned int containing Modified Julian Date,
                # as per DVB-SI spec
                # returning year,month,day
                YY = int( (MJD - 15078.2) / 365.25 )
                MM = int( (MJD - 14956.1 - int(YY*365.25) ) / 30.6001 )
                D  = MJD - 14956 - int(YY*365.25) - int(MM * 30.6001)
                K=0
                if MM == 14 or MM == 15: K=1
                return "%02d/%02d/%02d" % ( (1900 + YY+K), (MM-1-K*12), D)

            def unBCD(byte):
                return (byte>>4)*10 + (byte & 0xf)

            import struct

            with open(temp + '.eit','r') as descrTXT:
                data = descrTXT.read() #[19:].replace('\00','\n')
                ### Below is based on EMC handlers, thanks to author!!!
                e = struct.unpack(">HHBBBBBBH", data[0:12])
                myDescr = _('Recorded: %s %02d:%02d:%02d\n') % (parseMJD(e[1]), unBCD(e[2]), unBCD(e[3]), unBCD(e[4]) )
                myDescr += _('Lenght: %02d:%02d:%02d\n\n') % (unBCD(e[5]), unBCD(e[6]), unBCD(e[7]) )
                extended_event_descriptor = []
                EETtxt = ''
                pos = 12
                while pos < len(data):
                    rec = ord(data[pos])
                    length = ord(data[pos+1]) + 2
                    if rec == 0x4E:
                    #special way to handle CR/LF charater
                        for i in range (pos+8,pos+length):
                            if str(ord(data[i]))=="138":
                                extended_event_descriptor.append("\n")
                            else:
                                if data[i]== '\x10' or data[i]== '\x00' or  data[i]== '\x02':
                                    pass
                                else:
                                    extended_event_descriptor.append(data[i])
                    pos += length

                    # Very bad but there can be both encodings
                    # User files can be in cp1252
                    # Is there no other way?
                EETtxt = "".join(extended_event_descriptor)
                if EETtxt:
                    try:
                        EETtxt.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            EETtxt = EETtxt.decode("cp1250").encode("utf-8")
                        except UnicodeDecodeError:
                            # do nothing, otherwise cyrillic wont properly displayed
                            #extended_event_descriptor = extended_event_descriptor.decode("iso-8859-1").encode("utf-8")
                            pass
                
                self["Description"].setText(myDescr + self.ConvertChars(EETtxt) )
        ### DESCRIPTION from TXT ###
        elif path.exists(temp + '.txt'):
            with open(temp + '.txt','r') as descrTXT:
                myDescr = descrTXT.read()
                if myDescr[0] == "{" or myDescr[0] =="[" or myDescr[1] == ":" or myDescr[2] == ":":
                    self["Description"].setText('')
                else:
                    self["Description"].setText(myDescr)
        else:
            self["Description"].setText('')
    
    def ConvertChars(self, text):
        CharsTable={ '\xC2\xB1': '\xC4\x85','\xC2\xB6': '\xC5\x9b','\xC4\xBD': '\xC5\xba'}
        for i, j in CharsTable.iteritems():
            text = text.replace(i, j)
        return text

    def ExitPlayer(self):
        myConfig.PlayerOn.value = False
        configfile.save()
        self.close()

##################################################################### SUBTITLES >>>>>>>>>>
    def runDMnapi(self):
        if self.DmnapiInstalled == True:
            self.DMnapi()
            self["filelist"].refresh()
        else:
            def doNothing():
                pass
            def goUpdate(ret):
                if ret is True:
                    runlist = []
                    runlist.append( ('chmod 755 %sUpdate*.sh' % PluginPath) )
                    runlist.append( ('cp -a %sUpdateDMnapi.sh /tmp/AFPUpdate.sh' % PluginPath) ) #to have clear path of updating this script too ;)
                    runlist.append( ('/tmp/AFPUpdate.sh %s "%s"' % (config.plugins.AdvancedFreePlayer.Version.value,PluginInfo)) )
                    from AdvancedFreePlayerConfig import AdvancedFreePlayerConsole
                    self.session.openWithCallback(doNothing, AdvancedFreePlayerConsole, title = _("Installing DMnapi plugin"), cmdlist = runlist)
                    return
            self.session.openWithCallback(goUpdate, MessageBox,_("Do you want to install DMnapi plugin?"),  type = MessageBox.TYPE_YESNO, timeout = 10, default = False)
        return

    def DMnapi(self):
        if not self["filelist"].canDescent():
            f = self.filelist.getFilename()
            temp = f[-4:]
            if temp != ".srt" and temp != ".txt":
                curSelFile = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
                try:
                    from Plugins.Extensions.DMnapi.DMnapi import DMnapi
                    self.session.openWithCallback(self.dmnapiCallback, DMnapi, curSelFile)
                except:
                    printDEBUG("Exception loading DMnapi!!!")
            else:
                self.session.open(MessageBox,_("Please select movie files !\n\n"),MessageBox.TYPE_INFO)
                return

    def dmnapiCallback(self, answer=False):
        self["filelist"].refresh()
        
##################################################################### CLASS ENDS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                
def getNameWithoutExtension(MovieNameWithExtension):
    extLenght = len(path.splitext( path.basename(MovieNameWithExtension) )[1])
    return MovieNameWithExtension[: -extLenght]

    