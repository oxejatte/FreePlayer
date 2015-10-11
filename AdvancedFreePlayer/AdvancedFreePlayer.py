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
from Components.ProgressBar import ProgressBar
from Components.config import *
from Components.ServiceEventTracker import ServiceEventTracker
from Components.GUIComponent import GUIComponent
from Components.Converter.ConditionalShowHide import ConditionalShowHide
from Tools.LoadPixmap import LoadPixmap
from os import path, remove

from enigma import eTimer,ePoint,eSize,eLabel,gFont,eConsoleAppContainer,iServiceInformation,eServiceReference,addFont,getDesktop, iPlayableService

from skin import parseColor,parseFont

from time import *
from FileList2 import FileList

import subprocess,fcntl,os

config.plugins.AdvancedFreePlayer = ConfigSubsection()
config.plugins.AdvancedFreePlayer.FileListFontSize = ConfigInteger(24, (20,32))
config.plugins.AdvancedFreePlayer.MultiFramework = ConfigSelection(default = "4097", choices = [("4097", "gstreamer (root 4097)"),("4099", "ffmpeg (root 4099)"), ("select", _("Select during start"))])
config.plugins.AdvancedFreePlayer.StopService = ConfigYesNo(default = True)
config.plugins.AdvancedFreePlayer.InfobarTime = ConfigInteger(5, (2,9))
config.plugins.AdvancedFreePlayer.InfobarOnPause = ConfigYesNo(default = True)
#
# hidden atributes to store configuration data
#
config.plugins.AdvancedFreePlayer.FileListLastFolder = ConfigText(default = "/hdd/movie", fixed_size = False)
config.plugins.AdvancedFreePlayer.StoreLastFolder = ConfigYesNo(default = True)
config.plugins.AdvancedFreePlayer.InfobarConfig = ConfigText(default = "", fixed_size = False)

class AdvancedFreePlayer(Screen):
    CUT_TYPE_IN = 0
    CUT_TYPE_OUT = 1
    CUT_TYPE_MARK = 2
    CUT_TYPE_LAST = 3
    ENABLE_RESUME_SUPPORT = True
    VISIBLE = 4
    HIDDEN = 5

    KeyMapInfo=_("KEYMAP:\n\
up/down - position subtitle\n\
left/right - size subtitle\n\
channel up/down - seek+/- subtitle\n\
3/6/9 - seek+ 30sek/2min/5min movie\n\
1/4/7 - seek- 30sek/2min/5min movie\n\
play/red - play\n\
green - pause\n\
yellow - change type font\n\
blue - change color font\n\
text - show/hide subtitle\n\
menu - show about\n\
ok - infobar\n\
audio - change audio track\n\
")

    def __init__(self, session,openmovie,opensubtitle, rootID, LastPlayedService):
        self.conditionalNotVisible = []
        self.frameon = 1 / 24
        self.seeksubtitle = 0
        self.resume_point = 0
        self.nrsubtitle = 0
        self.enablesubtitle = True
        self.statesubtitle = "Show"
        self.stateplay = ""
        self.stateinfo = self.VISIBLE
        self.oldinfo = ""
        self.openmovie = openmovie
        self.opensubtitle = opensubtitle
        self.rootID = rootID
        self.LastPlayedService = LastPlayedService
        self.subtitle = []
        self.fontpos = 540
        self.fontsize = 60
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
        self.fontBackgroundState = 1
        self.fontBackgroundState_ = self.fontBackgroundState
        #load
        self.loadfont()
        self.loadcolor()
        self.loadconfig()
        if self.opensubtitle == "":
            self.enablesubtitle = False

        isHD = False
        isWideScreen = False
        isDolby = False
        #current state print
        print "FontPos = ", self.fontpos
        print "FontSize = ", self.fontsize
        print "FontType = ", self.fonttype_nr
        print "FontColor = ", self.fontcolor_nr
        print "fontBackgroundState = ", self.fontBackgroundState
        printDEBUG("OpenMovie: '%s'" % self.openmovie)
        printDEBUG("OpenSubtitle: '%s'" % self.opensubtitle)
        self.skin = """
<screen name="AdvancedFreePlayer" position="0,0" size="1280,720" title="InfoBar" backgroundColor="transparent" flags="wfNoBorder">
    <!-- OSD -->
    <widget name="InfoBarBG" position="215,30" zPosition="-5" size="851,134" pixmap="%s/pic/infobar.png" /> 
    <widget source="session.CurrentService" render="Label" position="220,40" size="580,45" font="Regular;24" valign="center" halign="center" noWrap="1" backgroundColor="black" transparent="1">
      <convert type="ServiceName">Name</convert>
    </widget>
    <widget name="progressBar" position="224,86" size="557,10" zPosition="4" pixmap="%s/pic/progress.png" transparent="1" />
    <widget name="currTimeLabel" position="245,120" size="110,30" valign="left" halign="center" font="Regular; 26"  shadowColor="black" shadowOffset="-3,-3" transparent="1" foregroundColor="yellow" />
    <widget name="lengthTimeLabel" position="375,120" size="110,30" valign="left" halign="center" font="Regular; 26" shadowColor="black" shadowOffset="-3,-3" transparent="1" />
    <widget name="remainedLabel" position="485,120" size="110,30" valign="left" halign="center" font="Regular; 26" shadowColor="black" shadowOffset="-3,-3" transparent="1" foregroundColor="green" />
    <!-- SIZE of the VIDEO -->
    <widget source="static_VideoWidth" render="Label" font="Regular; 20" position="870,100" size="60,20" halign="center" foregroundColor="#00fffe9e" transparent="1"/>
    <widget source="static_x" render="Label" font="Regular; 10" position="870,127" size="60,20" halign="center" transparent="1"/>
    <widget source="static_VideoHeight" render="Label" font="Regular; 20" position="870,138" size="60,20" halign="center"  foregroundColor="#00fffe9e" transparent="1"/>
    <!-- ICONS -->
    <widget name="Is_HD_Icon" position="935,35" size="60,60" zPosition="1" alphatest="blend" />
    <widget name="IsMultichannel_Icon" position="1000,35" size="60,60" zPosition="1" alphatest="blend" />
    <widget name="IsWidescreen_Icon" position="870,35" size="60,60" zPosition="1" alphatest="blend" />
    <!-- SubTiles -->
    <widget name="fpSRT_1" position="0,540" size="1920,220" valign="center" halign="center" font="Regular;24" backgroundColor="background" shadowColor="black" shadowOffset="-3,-2" transparent="1" />
    <widget name="fpSRT_2" position="0,540" size="1920,220" valign="center" halign="center" font="Regular;24" backgroundColor="background" shadowColor="black" shadowOffset="-3,-2" transparent="1" />
    <widget name="fpSRT_3" position="0,540" size="1920,220" valign="center" halign="center" font="Regular;24" backgroundColor="background" shadowColor="black" shadowOffset="-3,-2" transparent="1" />
    <widget name="fpSRT_4" position="0,540" size="1920,220" valign="center" halign="center" font="Regular;24" backgroundColor="background" shadowColor="black" shadowOffset="-3,-2" transparent="1" />

    <!--widget name="fpSRT_bg" position="0,540" size="1920,220" valign="center" halign="center" backgroundColor="transpBlack" zPosition="1"/-->
    
  </screen>""" % (PluginPath, PluginPath )

        Screen.__init__(self, session)
        self["static_VideoWidth"] = StaticText("")
        self["static_x"] = StaticText("")
        self["static_VideoHeight"] = StaticText("")
        self["InfoBarBG"] = Pixmap()
        self["Is_HD_Icon"] = Pixmap()
        self["IsMultichannel_Icon"] = Pixmap()
        self["IsWidescreen_Icon"] = Pixmap()
        self["fpSRT_1"] = Label()
        self["fpSRT_2"] = Label()
        self["fpSRT_3"] = Label()
        self["fpSRT_4"] = Label()
        self["fpSRT_bg"] = Label()

        self.fontLines = ["fpSRT_1", "fpSRT_2", "fpSRT_3", "fpSRT_4", "fpSRT_bg"]

        self["currTimeLabel"] = Label()
        self["lengthTimeLabel"] = Label()
        self["remainedLabel"] = Label()
        self["progressBar"] = ProgressBar()

        self["actions"] = ActionMap(["AdvancedFreePlayer"],
            {
                "ToggleInfobar": self.ToggleInfobar,
                "HelpScreen": self.HelpScreen,
                
                "cancel": self.Exit,
                "up": self.up,
                "down": self.down,
                "left": self.left,
                "right": self.right,
                "stop": self.Exit,
                "pause": self.pause,
                "pay": self.play,
                "key3": self.key3,
                "key6": self.key6,
                "key9": self.key9,
                "key1": self.key1,
                "key4": self.key4,
                "key7": self.key7,
                "key5": self.fontBackgroundToggle,
                "channelup": self.channelup,
                "channeldown": self.channeldown,
                "red": self.play,
                "togglePause": self.togglePause,
                "yellow": self.Ok,
                "blue": self.color,
                "text": self.text,
                "audio": self.audio,
            },-2)
        self.onShown.append(self.__LayoutFinish)
        self.onClose.append(self.__onClose)
        if not self.LastPlayedService:
            self.LastPlayedService = self.session.nav.getCurrentlyPlayingServiceReference()
            self.session.nav.stopService()
        self.session.nav.stopService()
        self.autoHideTime = 1000 * config.plugins.AdvancedFreePlayer.InfobarTime.value
        self.hideOSDTimer = eTimer()
        self.hideOSDTimer.callback.append(self.ToggleInfobar)
        self.hideOSDTimer.start(self.autoHideTime, True) # singleshot

        self.__event_tracker = ServiceEventTracker(screen=self, eventmap= {
                                                      iPlayableService.evStart: self.__serviceStarted,
                                                      iPlayableService.evUpdatedInfo: self.__evUpdatedInfo,
                                                      })

    def getIconPath(self, IconName):
        if path.exists('%sicons/%s' % (SkinPath,IconName)):
            myPath = '%sicons/%s' % (SkinPath,IconName)
        else:
            myPath = '%spic/%s' % (PluginPath, IconName)
        #printDEBUG(myPath)
        return myPath

    def __evUpdatedInfo(self, systemcall=True):
        if systemcall==True: printDEBUG('__evUpdatedInfo systemcall')
        else: printDEBUG('__evUpdatedInfo started manually')
        
        service=self.session.nav.getCurrentService()
        if service is not None:
            audio = service.audioTracks()
            if audio:
                n = audio.getNumberOfTracks()
                selectedAudio = audio.getCurrentTrack()
                for x in range(n):
                    i = audio.getTrackInfo(x)
                    description = i.getDescription();
                    if description.find("AC3") != -1 or description.find("DTS") != -1:
                        self["IsMultichannel_Icon"].instance.setPixmap(LoadPixmap(path=self.getIconPath('ico_dolby_on.png') ))
                    else:
                        self["IsMultichannel_Icon"].instance.setPixmap(LoadPixmap(path=self.getIconPath('ico_sound_off.png') ))
                        
    def __serviceStarted(self):
        #self.__evUpdatedInfo(False)
        
        service=self.session.nav.getCurrentService()
        if service is not None:
            info=service.info()
            height = info and info.getInfo(iServiceInformation.sVideoHeight) or -1
            width = info and info.getInfo(iServiceInformation.sVideoWidth) or -1
            if height > 719 : #set HD
                self["Is_HD_Icon"].instance.setPixmap(LoadPixmap(path=self.getIconPath('ico_hd_on.png') ))
            else:
                self["Is_HD_Icon"].instance.setPixmap(LoadPixmap(path=self.getIconPath('ico_hd_off.png') ))
            
            if height >0 and width>0:
                self["static_VideoWidth"].setText(str(width))
                self["static_x"].setText("X")
                self["static_VideoHeight"].setText(str(height))
                if width/float(height) >= 1.5:
                    self["IsWidescreen_Icon"].instance.setPixmap(LoadPixmap(path=self.getIconPath('ico_format_on.png') ))
                else:
                    self["IsWidescreen_Icon"].instance.setPixmap(LoadPixmap(path=self.getIconPath('ico_format_off.png') ))

            self.resumeLastPlayback()
      
    def __onClose(self):
        if self.fontpos != self.fontpos_ or self.fontsize != self.fontsize_ or self.fonttype_nr != self.fonttype_nr_ \
        or self.fontcolor_nr != self.fontcolor_nr_ or self.osdPosX != self.osdPosX_ or self.osdPosY != self.osdPosY_ \
        or self.fontBackgroundState != self.fontBackgroundState_:
            print "[FP] write config"
            o = open(PluginPath + PluginName + '.ini','w')
            o.write(str(self.fontpos)+"\n")
            o.write(str(self.fontsize)+"\n")
            o.write(str(self.fonttype_nr)+"\n")
            o.write(str(self.fontcolor_nr)+"\n")
            o.write(str(self.fontBackgroundState)+"\n")
            o.close()
        self.hideOSDTimer.stop()
        if self.LastPlayedService:
            self.session.nav.playService(self.LastPlayedService)

    def __LayoutFinish(self):
        print "--> Start of __LayoutFinish"
        self.onShown.remove(self.__LayoutFinish)
        print "--> Loading subtitles"
        self.loadsubtitle()
        print "--> Updating osd position"
        try:
            tmpOSD = config.plugins.AdvancedFreePlayer.InfobarConfig.value.split(',')
            tmpOSDPosX = int(tmpOSD[0])
            tmpOSDPosY = int(tmpOSD[1])
            self.updateOSDPosition(tmpOSDPosX, tmpOSDPosY, True)
        except:
            pass
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
        root = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + self.openmovie)
        self.session.nav.playService(root)
        self.stateplay = "Play"
        for fontLine in self.fontLines:
            self[fontLine].instance.move(ePoint(0,self.fontpos))
            self[fontLine].instance.setForegroundColor(parseColor(self.fontcolor_list[self.fontcolor_nr]))
        print "End of go"

    def loadfont(self):
        o = open(PluginPath + 'font.ini','r')
        self.fonttype_list = []
        self.fonttype_list.append("Regular")
        while True:
            l = o.readline()
            if len(l) == 0: break
            l = l.strip()
            self.fonttype_list.append(l)
            #print l
            addFont(PluginPath + 'fonts/'+l, l, 100, False)
        o.close()

    def loadcolor(self):
        o = open(PluginPath + 'color.ini','r')
        self.fontcolor_list = []
        self.fontcolor_list.append("white")
        while True:
            l = o.readline()
            if len(l) == 0: break
            l = l.strip()
            #print l
            self.fontcolor_list.append(l)
        o.close()

    def loadconfig(self):
        o = open(PluginPath + 'AdvancedFreePlayer.ini','r')
        self.fontpos = int(o.readline())
        self.fontsize = int(o.readline())
        self.fonttype_nr = int(o.readline())
        self.fontcolor_nr = int(o.readline())
        self.fontBackgroundState = int(o.readline())

        self.fontpos_ = self.fontpos
        self.fontsize_ = self.fontsize
        if (self.fonttype_nr+1) > len(self.fonttype_list):
            self.fonttype_nr=0
        if (self.fontcolor_nr+1) > len(self.fontcolor_list):
            self.fontcolor_nr=0
        self.fonttype_nr_ = self.fonttype_nr
        self.fontcolor_nr_ = self.fontcolor_nr
        self.fontBackgroundState_ = self.fontBackgroundState
        o.close()

    def convertTime(self, time):
#        print "convertTime:"+str(time)
        if time is None:
            time=0
        s = "%d:%02d:%02d" % ((time/3600/90000), (time/90000)%3600/60, (time/90000)%60)
        return s

    def timerEvent(self):
        lCurrent = self.GetCurrentPosition() or 0
        printDEBUG("lCurrent=%d" % lCurrent)
        if not lCurrent is None:
            self.showsubtitle(lCurrent)

            if self.stateinfo == self.VISIBLE:
                s = self.convertTime(lCurrent)
                if self.oldinfo != s:
                    self.oldinfo = s
                    lTotal = self.GetCurrentLength() or 0
                    printDEBUG("lTotal=%d" % lTotal)
                    lRemaining = lTotal - lCurrent
                    printDEBUG("lRemaining=%d" % lRemaining)
                    self["currTimeLabel"].setText(s)

                    s = self.convertTime(lRemaining)
#                    print "remaining:" + str(lRemaining)+" -> "+s
                    self["remainedLabel"].setText("-"+s)

                    s = self.convertTime(lTotal)
#                    print "total:"+ str(lTotal)+" -> "+s
                    self["lengthTimeLabel"].setText(s)

                    self['progressBar'].range = (0, lTotal/90000)
                    self['progressBar'].value = lCurrent/90000


    def showsubtitle(self,tim):
        if self.enablesubtitle == False:
            return
        tim = tim + (self.seeksubtitle * 90000)
        for pos in self.subtitle:
            nr=pos[0]
            start=pos[1]
            stop=pos[2]
            text=pos[3]
            if self.statesubtitle == "Show":
                if (tim == start or tim > start) and tim < stop:
                    self.nrsubtitle = nr
                    self.statesubtitle = "Hide"
                    self.setTextForAllLInes(text)
                    #print tim," Show ",nr," ",start," --> ",stop,"     ",text
            else:
                if (tim == stop or tim > stop) and nr == self.nrsubtitle:
                    self.statesubtitle = "Show"
                    self.setTextForAllLInes("")
                    #print tim," Hide ",nr," ",start," --> ",stop,"     ",text
                elif tim < start and nr == self.nrsubtitle:
                    self.statesubtitle = "Show"
                    self.setTextForAllLInes("")
                    #print tim," Hide ",nr," ",start," --> ",stop,"     ",text

    def usun(self,l):
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
        printDEBUG("[FP] Load subtitle STR")
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
                    printDEBUG(nr)
                    if len(nr) == 0:break
                    if nr == "\n": continue
                    nr = nr.strip()
                    tim = o.readline().replace("\r\n","\n")
                    if len(tim) == 0:break
                    tim = tim.strip()
                    printDEBUG(tim)
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
            self.subtitle = []
            print "Error loadsrt"
            print str(e)
            printDEBUG("Error loadtxt_type, I/O error({0}): {1}".format(e.errno, e.strerror) )
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

    def updateChannelChange(self, position):
        self.seeksubtitle = self.seeksubtitle + position
        self.setTextForAllLInes(str(self.seeksubtitle)+" sek")

    def channelup(self):
        self.updateChannelChange(+0.5)

    def channeldown(self):
        self.updateChannelChange(-0.5)

    def key3(self):
        if self.stateplay == "Play":
            self.doSeekRelative(30 * 90000)

    def key6(self):
        if self.stateplay == "Play":
            self.doSeekRelative(2 * 60 * 90000)

    def key9(self):
        if self.stateplay == "Play":
            self.doSeekRelative(5 * 60 * 90000)

    def key1(self):
        if self.stateplay == "Play":
            self.doSeekRelative(- 30 * 90000)

    def key4(self):
        if self.stateplay == "Play":
            self.doSeekRelative(- 2 * 60 * 90000)

    def key7(self):
        if self.stateplay == "Play":
            self.doSeekRelative(- 5 * 60 * 90000)

    def togglePause(self):
        if self.stateplay == "Play":
            self.pause()
        elif self.stateplay == "Pause":
            self.play()

    def pause(self):
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
        if config.plugins.AdvancedFreePlayer.InfobarOnPause.value == True:
            self.setVisibleForAll(True, "OSD")

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
        if config.plugins.AdvancedFreePlayer.InfobarOnPause.value == True:
            self.setVisibleForAll(False, "OSD")

    def text(self):
        if self.enablesubtitle == True:
            self.enablesubtitle = False
            self.setTextForAllLInes("")
        else:
            self.enablesubtitle = True

    def HelpScreen(self):
        self.session.open(MessageBox,PluginName + ' ' + PluginInfo +"\n\n"+self.KeyMapInfo,  MessageBox.TYPE_INFO)

    def audio(self):
        from Screens.AudioSelection import AudioSelection
        self.session.openWithCallback(self.audioSelected, AudioSelection, infobar=self)

    def audioSelected(self, ret=None):
        print "[AdvancedFreePlayer infobar::audioSelected]", ret

#Moje funkcje START
    def updateTextBackground(self, element, text):
        showBackgroud = self.fontBackgroundState
        if not text:
            showBackgroud = False
        self.setVisible(showBackgroud, element)

    def isTextBackground(self, element):
        if not "bg" in element:
            return False
        return True

    def setTextForAllLInes(self, text):
        for fontLine in self.fontLines:
            if self.isTextBackground(fontLine):
                self.updateTextBackground(self[fontLine], text)
            else:
                self[fontLine].setText(text)

    def setVisible(self, visible, component):
        if visible:
            if component not in self.conditionalNotVisible:
                component.show()
        else:
            component.hide()

    def isNotFontLine(self, component):
        for fontLine in self.fontLines:
            if self[fontLine] is component:
                return False
        return True

    def setVisibleForAll(self, visible, type):
        if type=="OSD":
#            print vars(self)
            startUp = len(self.conditionalNotVisible)
            for val in self.values() + self.renderer:
                if isinstance(val, GUIComponent):
                    if self.isNotFontLine(val):
                        print "GUIComponent"
                        print str(val)
                        print val.getVisible()
                        if startUp ==0:
                            if hasattr(val, 'sources') and val.sources:
                                for sourceTmp in val.sources:
                                    if isinstance(sourceTmp, ConditionalShowHide):
                                        if not val.getVisible():
                                            print "adding not visible element"
                                            self.conditionalNotVisible.append(val)
                        self.setVisible(visible, val)
        elif type=="TEXT":
            for fontLine in self.fontLines:
                if not self.isTextBackground(fontLine):
                    self.setVisible(visible, self[fontLine])
        elif type=="TEXT_BG":
            for fontLine in self.fontLines:
                if self.isTextBackground(fontLine):
                    self.setVisible(visible, self[fontLine])

    def fontBackgroundToggle(self):
        self.fontBackgroundState = (self.fontBackgroundState+1)%2
        self.setVisibleForAll(self.fontBackgroundState, "TEXT_BG")

    def ToggleInfobar(self): #### old info
        self.hideOSDTimer.stop()
        if self.stateinfo == self.HIDDEN:
            self.stateinfo = self.VISIBLE
            self.setVisibleForAll(True, "OSD")
            self.hideOSDTimer.start(self.autoHideTime, True) # singleshot
        else:
            self.stateinfo = self.HIDDEN
            self.setVisibleForAll(False, "OSD")

    def setFontForAll(self):
        for fontLine in self.fontLines:
            self[fontLine].instance.setFont(gFont(self.fonttype_list[self.fonttype_nr], self.fontsize))

    def left(self):
        if self.stateinfo == self.HIDDEN:
            self.fontsize = self.fontsize - 2
            print "font size = ",self.fontsize
            self.setFontForAll()
        else:
            self.updateOSDPosition(-5, 0)

    def right(self):
        if self.stateinfo == self.HIDDEN:
            self.fontsize = self.fontsize + 2
            print "font size = ",self.fontsize
            self.setFontForAll()
        else:
            self.updateOSDPosition(+5, 0)

    def updateTextMovement(self, fotpos):
        self.fontpos = self.fontpos + fotpos
        print "pos y = ",self.fontpos
        self.setTextForAllLInes("Line1\nLine2\nLine3")
        for fontLine in self.fontLines:
            self[fontLine].instance.move(ePoint(0,self.fontpos))

    def updateOSDPosition(self, xPos, yPos, AbsolutePosition = False ):
        if AbsolutePosition == False:
            self.osdPosX = self.osdPosX + xPos
            self.osdPosY = self.osdPosY + yPos
            config.plugins.AdvancedFreePlayer.InfobarConfig.value = "%s,%s" %(self.osdPosX,self.osdPosY)
            config.plugins.AdvancedFreePlayer.InfobarConfig.save()
        else:
            self.osdPosX = xPos
            self.osdPosY = yPos
        for val in self.values() + self.renderer:
            if isinstance(val, GUIComponent):
                if self.isNotFontLine(val):
                    x, y = val.getPosition()
                    val.instance.move(ePoint(x + xPos, y + yPos))


    def up(self):
        if self.stateinfo == self.HIDDEN:
            self.updateTextMovement(-5)
        else:
            self.updateOSDPosition(0, -5)

    def down(self):
        if self.stateinfo == self.HIDDEN:
            self.updateTextMovement(+5)
        else:
            self.updateOSDPosition(0, +5)

    def color(self):
        self.fontcolor_nr = self.fontcolor_nr + 1
        if self.fontcolor_nr == len(self.fontcolor_list):
            self.fontcolor_nr = 0
        for fontLine in self.fontLines:
            self[fontLine].instance.setForegroundColor(parseColor(self.fontcolor_list[self.fontcolor_nr]))

        self.setTextForAllLInes("Color"+str(self.fontcolor_nr))

    def Ok(self):
        self.fonttype_nr = self.fonttype_nr + 1
        if self.fonttype_nr == len(self.fonttype_list):
            self.fonttype_nr = 0
        self.setFontForAll()

        self.setTextForAllLInes("Font"+str(self.fonttype_nr))


    def Exit(self):
        self.stateplay = "Stop"
        self.timer.stop()
        self.session.nav.stopService()
        self.close()


class AdvancedFreePlayerStart(Screen):

    def __init__(self, session):
        #printDEBUG("AdvancedFreePlayerStart >>>")
        self.sortDate = False
        self.openmovie = ""
        self.opensubtitle = ""
        self.movietxt = _('Movie: ')
        self.subtitletxt = _('Subtitle: ')
        self.rootID = config.plugins.AdvancedFreePlayer.MultiFramework.value
        self.LastPlayedService = None
  
        self.skin  = """
<screen name="AdvancedFreePlayerStart" position="0,0" size="1280,720" title=" " flags="wfNoBorder" backgroundColor="transparent">
  <!-- Template -->
  <eLabel position="0,0"    size="1280,720" zPosition="-15" backgroundColor="#20000000" />
  <eLabel position=" 44, 81" size="725,474" zPosition="-10" backgroundColor="#20606060" />
  <eLabel position="775,251" size="445,376" zPosition="-10" backgroundColor="#20606060" />
  <eLabel position="775, 81" size="445,165" zPosition="-10" backgroundColor="#20606060" />
  <eLabel position=" 45,633" size="290, 55" zPosition="-10" backgroundColor="#20b81c46" />
  <eLabel position="340,633" size="290, 55" zPosition="-10" backgroundColor="#20009f3c" />
  <eLabel position="635,633" size="290, 55" zPosition="-10" backgroundColor="#209ca81b" />
  <eLabel position="930,633" size="290, 55" zPosition="-10" backgroundColor="#202673ec" />
  <widget source="key_red" render="Label" position="60,647" size="260,25" zPosition="1" font="Regular;20" halign="left" transparent="1" />
  <widget source="key_green" render="Label" position="365,647" size="260,25" zPosition="1" font="Regular;20" halign="left" transparent="1" />
  <widget source="key_yellow" render="Label" position="660,647" size="260,25" zPosition="1" font="Regular;20" halign="left" transparent="1" />
  <widget source="key_blue" render="Label" position="955,647" size="260,25" zPosition="1" font="Regular;20" halign="left" transparent="1" />
  <!-- Selected movie -->
  <eLabel position=" 44,561" size="725, 30" zPosition="-10" backgroundColor="#20606060" />
  <widget name="filemovie" position="50,560" size="715,30" font="Regular; 20" transparent="1" valign="center" />
  <!-- Selected subtitle -->
  <eLabel position="44,597" size="725, 30" zPosition="-10" backgroundColor="#20606060" />
  <widget name="filesubtitle" position="50,597" size="715,30" font="Regular; 20" transparent="1" valign="center" />
  
  <widget name="info" position="40,25" size="200,30" font="Regular; 27" backgroundColor="#20606060" transparent="1" />
  <widget name="myPath" position="50,86" size="715,25" font="Regular;20" foregroundColor="#00ffffff" backgroundColor="#004e4e4e" transparent="1" />
  <widget name="filelist" position="60,116" size="690,439" zPosition="1" font="Regular;20" transparent="1" scrollbarMode="showOnDemand" />

  <widget name="Description" render="Label" position="780,256" size="435,366" font="Regular;20" zPosition="1" foregroundColor="foreground" transparent="1" valign="top"/>
  </screen>
"""
        
        Screen.__init__(self, session)
        self["info"] = Label()
        self["myPath"] = Label(config.plugins.AdvancedFreePlayer.FileListLastFolder.value)
        
        self["filemovie"] = Label(self.movietxt)
        self["filesubtitle"] = Label(self.subtitletxt)
        self["key_red"] = StaticText(_("Play"))
        self["Description"] = StaticText("Description")
        
        if path.exists(PluginPath +'../DMnapi/DMnapi.pyo') or path.exists(PluginPath +'../DMnapi/DMnapi.pyc') or path.exists(PluginPath +'../DMnapi/DMnapi.py'):
            self.DmnapiInstalled = True
            self["key_green"] = StaticText(_("DMnapi"))
        else:
            self.DmnapiInstalled = False
            self["key_green"] = StaticText(_("No DMnapi"))
            
        self["key_yellow"] = StaticText(_("Config"))
        self["key_blue"] = StaticText(_("Sort by name"))
        self["info"].setText(PluginName + ' ' + PluginInfo)
        self.filelist = FileList(config.plugins.AdvancedFreePlayer.FileListLastFolder.value, matchingPattern = "(?i)^.*\.(avi$|txt$|srt$|mpg$|vob$|divx$|m4v$|mkv$|mp4$|dat$|mov$|ts$)(?!\.cuts)",sortDate=False)
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
        if config.plugins.AdvancedFreePlayer.StopService.value == True:
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
            config.plugins.AdvancedFreePlayer.FileListLastFolder.value =  self["myPath"].getText()
            config.plugins.AdvancedFreePlayer.FileListLastFolder.save()
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
        if config.plugins.AdvancedFreePlayer.MultiFramework.value == "select":
            from Screens.ChoiceBox import ChoiceBox
            self.session.openWithCallback(self.SelectedFramework, ChoiceBox, title = _("Select Multiframework"), list = [("gstreamer (root 4097)","4097"),("ffmpeg (root 4099)","4099"),])
        else:
            self.StartPlayer()

    def SelectedFramework(self, ret):
        if ret:
            self.rootID = ret[1]
            printDEBUG("Selected framework: " + ret[1])
        self.StartPlayer()
      
    def StartPlayer(self):
        if not path.exists(self.opensubtitle):
            self.opensubtitle = ""
        if path.exists(self.openmovie):
            self.session.open(AdvancedFreePlayer,self.openmovie,self.opensubtitle,self.rootID,self.LastPlayedService)

    def runDMnapi(self):
        if self.DmnapiInstalled == True:
            self.DMnapi()
            self["filelist"].refresh()

    def runConfig(self):
        from AdvancedFreePlayerConfig import AdvancedFreePlayerConfig
        self.session.open(AdvancedFreePlayerConfig)

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

    def dmnapiCallback(self, answer=False):
        self["filelist"].refresh()

    def selectFile(self):
        selection = self["filelist"].getSelection()
        if selection[1] == True: # isDir
            self["filelist"].changeDir(selection[0])
            d = self.filelist.getCurrentDirectory()
            if d is None:
                d=""
            #self.title = d
            self["myPath"].setText(d)
        else:
            d = self.filelist.getCurrentDirectory()
            f = self.filelist.getFilename()
            printDEBUG("self.OK>> " + d + f)
            temp = f[-4:]
            print temp
            if temp == ".srt" or temp == ".txt":
                if self.DmnapiInstalled == True:
                    if self.opensubtitle == (d + f):
                        d = ""
                        f = ""
                    self["filesubtitle"].setText(self.subtitletxt + f)
                    self.opensubtitle = d + f
            else:
                if self.openmovie == (d + f):
                    d = ""
                    f = ""
                self.openmovie = d + f
                self["filemovie"].setText(self.movietxt + f)
                if self.DmnapiInstalled == True:
                    temp = f[:-4]
                    if path.exists( d + temp + ".srt"):
                        self["filesubtitle"].setText(self.subtitletxt + temp + ".srt")
                        self.opensubtitle = d + temp + ".srt"
                    elif path.exists( d + temp + ".txt"):
                        self["filesubtitle"].setText(self.subtitletxt + temp + ".txt")
                        self.opensubtitle = d + temp + ".txt"
                else:
                    self.opensubtitle = ""

    def ExitPlayer(self):
        configfile.save()
        self.close()
