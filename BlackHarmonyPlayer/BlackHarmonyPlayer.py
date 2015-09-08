from __init__ import _

from Screens.Screen import Screen

from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox

from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.ProgressBar import ProgressBar
from Components.config import config, configfile,ConfigSubsection,ConfigInteger
from Components.ServiceEventTracker import ServiceEventTracker
from Components.GUIComponent import GUIComponent
from Components.Converter.ConditionalShowHide import ConditionalShowHide

from enigma import iPlayableService, eTimer
from enigma import eTimer,ePoint,eSize,eLabel,gFont,eConsoleAppContainer,iServiceInformation,eServiceReference,addFont,getDesktop

from skin import parseColor,parseFont

from time import *
from FileList2 import FileList

import subprocess,fcntl,os

i1="BlackHarmonyPlayer 0.9 Beta"
i2=_("KEYMAP:\n\
up/down - position subtitle\n\
left/right - size subtitle\n\
channel up/down - seek+/- subtitle\n\
info - show timer\n\
3/6/9 - seek+ 30sek/2min/5min movie\n\
1/4/7 - seek- 30sek/2min/5min movie\n\
red - play\n\
green - pause\n\
yellow - stop\n\
blue - change color font\n\
text - show/hide subtitle\n\
menu - show about\n\
ok - change type font\n\
audio - change audio track\n\
")

class BlackHarmonyPlayer(Screen):
	def __init__(self, session,openmovie,opensubtitle):
		self.debug = False
		self.conditionalNotVisible = []
		self.frameon = 1 / 24
		self.seeksubtitle = 0
		self.nrsubtitle = 0
		self.enablesubtitle = True
		self.statesubtitle = "Show"
		self.stateplay = ""
		self.stateinfo = "Show"
		self.oldinfo = ""
		self.openmovie = openmovie
		self.opensubtitle = opensubtitle
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

		#current state print
		print "FontPos = ",self.fontpos
		print "FontSize = ",self.fontsize
		print "osdPosX = ",self.osdPosX
		print "osdPosY = ",self.osdPosY
		print "FontType = ",self.fonttype_nr
		print "FontColor = ",self.fontcolor_nr
		print "fontBackgroundState = ",self.fontBackgroundState
		print "OpenMovie : ",self.openmovie
		print "OpenSubtitle : ",self.opensubtitle
		self.skin = """
  <screen name="BlackHarmonyPlayer" position="center,center" size="1920,1080" title="InfoBar" flags="wfNoBorder" backgroundColor="transparent">
    <widget name="InfoBarBG" position="200,10" zPosition="-1" size="1529,213" pixmap="BlackHarmony/bg_design/infobarmovie.png" />
    <widget name="fpSRT_1" position="0,540" size="1920,220" valign="center" halign="center" font="%s;%d" backgroundColor="background" shadowColor="black" shadowOffset="-3,-2" transparent="1" />
    <widget name="fpSRT_2" position="0,540" size="1920,220" valign="center" halign="center" font="%s;%d" backgroundColor="background" shadowColor="black" shadowOffset="-3,-2" transparent="1" />
    <widget name="fpSRT_3" position="0,540" size="1920,220" valign="center" halign="center" font="%s;%d" backgroundColor="background" shadowColor="black" shadowOffset="-3,-2" transparent="1" />
    <widget name="fpSRT_4" position="0,540" size="1920,220" valign="center" halign="center" font="%s;%d" backgroundColor="background" shadowColor="black" shadowOffset="-3,-2" transparent="1" />

	<widget name="fpSRT_bg" position="0,540" size="1920,220" valign="center" halign="center" backgroundColor="transpBlack" zPosition="1"/>
    
	<widget source="session.CurrentService" render="Pixmap" position="1241,143" size="57,20" pixmap="BlackHarmony/icons/ico_dolby_on.png" zPosition="2" alphatest="blend">
      <convert type="ServiceInfo">IsMultichannel</convert>
      <convert type="ConditionalShowHide" />
    </widget>

    <widget render="Pixmap" position="1367,143" size="36,20" pixmap="BlackHarmony/icons/ico_format_off.png" zPosition="1" alphatest="blend"></widget>
    <widget source="session.CurrentService" render="Pixmap" position="1367,143" size="36,20" pixmap="BlackHarmony/icons/ico_format_on.png" zPosition="2" alphatest="blend">
      <convert type="ServiceInfo">IsWidescreen</convert>
      <convert type="ConditionalShowHide" />
    </widget>

	

    <widget render="Pixmap" position="1318,143" size="29,20" pixmap="BlackHarmony/icons/ico_hd_off.png" zPosition="1" alphatest="blend">
    </widget>
    <widget source="session.CurrentService" render="Pixmap" position="1318,143" size="29,20" pixmap="BlackHarmony/icons/ico_hd_on.png" zPosition="2" alphatest="blend">
      <convert type="ServiceInfo">VideoWidth</convert>
      <convert type="ValueRange">721,1980</convert>
      <convert type="ConditionalShowHide" />
    </widget>
	
	
	

    <widget source="session.CurrentService" render="Label" position="265,50" size="1140,45" font="HD_Thin; 32" valign="center" noWrap="1" backgroundColor="black" transparent="1">
      <convert type="ServiceName">Name</convert>
    </widget>

    <widget backgroundColor="black" font="Roboto_HD; 26" halign="center" position="645,140" render="Label" size="320,30" source="global.CurrentTime" transparent="1" valign="center">
      <convert type="ClockToText">Format: %%a, %%d.%%m.%%Y  %%H:%%M:%%S</convert>
    </widget>

    <widget name="currTimeLabel" position="265,138" size="110,30" valign="left" halign="center" font="Roboto_HD; 26" backgroundColor="background" shadowColor="black" shadowOffset="-3,-3" transparent="1" foregroundColor="yellow" />
    <widget name="lengthTimeLabel" position="375,138" size="110,30" valign="left" halign="center" font="Roboto_HD; 26" backgroundColor="background" shadowColor="black" shadowOffset="-3,-3" transparent="1" />
    <widget name="remainedLabel" position="485,138" size="110,30" valign="left" halign="center" font="Roboto_HD; 26" backgroundColor="background" shadowColor="black" shadowOffset="-3,-3" transparent="1" foregroundColor="green" />


 <widget name="progressBar" position="264,113" size="1141,6" zPosition="4" pixmap="BlackHarmony/gfx/progress.png" transparent="1" />

    <widget source="session.CurrentService" render="Label" font="Roboto_HD; 26" position="1012,138" size="70,30" halign="right" backgroundColor="black" transparent="1" foregroundColor="light_yellow">
      <convert type="ServiceInfo">VideoWidth</convert>
    </widget>
	

	    <widget source="static_x" render="Label" font="Roboto_HD; 26" position="1085,137" size="15,30" halign="center" backgroundColor="black" transparent="1"/>
		
    <widget source="session.CurrentService" render="Label" font="Roboto_HD; 26" position="1103,138" size="70,30" halign="left" backgroundColor="black" transparent="1" foregroundColor="light_yellow">
      <convert type="ServiceInfo">VideoHeight</convert>
    </widget>

  </screen>""" % (self.fonttype_list[self.fonttype_nr],self.fontsize,
  				self.fonttype_list[self.fonttype_nr],self.fontsize,
  				self.fonttype_list[self.fonttype_nr],self.fontsize,
  				self.fonttype_list[self.fonttype_nr],self.fontsize)

		Screen.__init__(self, session)
		self["static_x"] = StaticText("x")
		self["InfoBarBG"] = Pixmap()
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

		self["actions"] = ActionMap(["BlackHarmonyPlayerActions"],
			{
				"ok": self.Ok,
				"cancel": self.Exit,
				"up": self.up,
				"down": self.down,
				"left": self.left,
				"right": self.right,
				"stop": self.Exit,
				"pause": self.togglePause,
				"play": self.play,
				"info": self.info,
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
				"green": self.togglePause,
				"yellow": self.Exit,
				"blue": self.color,
				"text": self.text,
				"audio": self.audio,
				"menu": self.menu
			},-2)
		self.onShown.append(self.__LayoutFinish)
		self.onClose.append(self.__onClose)
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		self.autoHideTime = 1000 * 5
		self.hideOSDTimer = eTimer()
		self.hideOSDTimer.callback.append(self.info)
		self.hideOSDTimer.start(self.autoHideTime, True) # singleshot

	def __onClose(self):
		if self.fontpos != self.fontpos_ or self.fontsize != self.fontsize_ or self.fonttype_nr != self.fonttype_nr_ \
		or self.fontcolor_nr != self.fontcolor_nr_ or self.osdPosX != self.osdPosX_ or self.osdPosY != self.osdPosY_ \
		or self.fontBackgroundState != self.fontBackgroundState_:
			print "[FP] write config"
			o = open('/usr/lib/enigma2/python/Plugins/Extensions/BlackHarmonyPlayer/BlackHarmonyPlayer.ini','w')
			o.write(str(self.fontpos)+"\n")
			o.write(str(self.fontsize)+"\n")
			o.write(str(self.fonttype_nr)+"\n")
			o.write(str(self.fontcolor_nr)+"\n")
			o.write(str(self.osdPosX)+"\n")
			o.write(str(self.osdPosY)+"\n")
			o.write(str(self.fontBackgroundState)+"\n")
			o.close()
		self.hideOSDTimer.stop()
		self.session.nav.playService(self.oldService)


	def __LayoutFinish(self):
		print "--> Start of __LayoutFinish"
		self.onShown.remove(self.__LayoutFinish)
		print "--> Loading subtitles"
		self.loadsubtitle()
		tmpOSDPosX = self.osdPosX
		self.osdPosX = 0
		tmpOSDPosY = self.osdPosY
		self.osdPosY = 0
		print "--> Updating osd position"
		self.updateOSDPosition(tmpOSDPosX, tmpOSDPosY)
#		print "--> Calling info"
#		self.info()
		print "--> Setting visible to false"
#		self.setVisibleForAll(False, "OSD")
		print "--> End of __LayoutFinish"

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
		o = open('/usr/lib/enigma2/python/Plugins/Extensions/BlackHarmonyPlayer/font.ini','r')
		self.fonttype_list = []
		self.fonttype_list.append("Regular")
		while True:
			l = o.readline()
			if len(l) == 0: break
			l = l.strip()
			self.fonttype_list.append(l)
			#print l
			addFont("/usr/lib/enigma2/python/Plugins/Extensions/BlackHarmonyPlayer/fonts/"+l, l, 100, False)
		o.close()

	def loadcolor(self):
		o = open('/usr/lib/enigma2/python/Plugins/Extensions/BlackHarmonyPlayer/color.ini','r')
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
		o = open('/usr/lib/enigma2/python/Plugins/Extensions/BlackHarmonyPlayer/BlackHarmonyPlayer.ini','r')
		self.fontpos = int(o.readline())
		self.fontsize = int(o.readline())
		self.fonttype_nr = int(o.readline())
		self.fontcolor_nr = int(o.readline())
		self.osdPosX = int(o.readline())
		self.osdPosY = int(o.readline())
		self.fontBackgroundState = int(o.readline())

		self.fontpos_ = self.fontpos
		self.fontsize_ = self.fontsize
		self.osdPosX_ = self.osdPosX
		self.osdPosY_ = self.osdPosY
		if (self.fonttype_nr+1) > len(self.fonttype_list):
			self.fonttype_nr=0
		if (self.fontcolor_nr+1) > len(self.fontcolor_list):
			self.fontcolor_nr=0
		self.fonttype_nr_ = self.fonttype_nr
		self.fontcolor_nr_ = self.fontcolor_nr
		self.fontBackgroundState_ = self.fontBackgroundState
		o.close()

	def convertTime(self, time):
#		print "convertTime:"+str(time)
		if time is None:
			time=0
		s = "%d:%02d:%02d" % ((time/3600/90000), (time/90000)%3600/60, (time/90000)%60)
		return s

	def timerEvent(self):
		lCurrent = self.GetCurrentPosition()
		if not lCurrent is None:
			self.showsubtitle(lCurrent)

			if self.stateinfo == "Show":
				s = self.convertTime(lCurrent)
				if self.oldinfo != s:
					self.oldinfo = s
					lTotal = self.GetCurrentLength()
					lRemaining = lTotal - lCurrent
#					print "current"+ str(lCurrent)+" -> "+s
					self["currTimeLabel"].setText(s)

					s = self.convertTime(lRemaining)
#					print "remaining:" + str(lRemaining)+" -> "+s
					self["remainedLabel"].setText("-"+s)

					s = self.convertTime(lTotal)
#					print "total:"+ str(lTotal)+" -> "+s
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
		if not self.opensubtitle == "":
			temp = self.opensubtitle[-4:]
			if temp == ".srt":
				self.loadsrt()
				self.go()
			else:
				self.loadtxt_type()
		else:
			self.go()

	def loadtxt_type(self):
		try:
			o = open(self.opensubtitle,'r')
			l = o.readline()
			o.close()
			if l[0] == "{":
				print "[FP] Load subtitle TXT mDVD"
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
					print "Unkown AVI - set manual framerate"
					self.session.openWithCallback(self.framerateCallback, ChoiceBox, \
					title=_("BlackHarmonyPlayer not found framerate in movie.\nPlease select manual framerate !"), \
					list=[["23.0","23.0"],["23.5","23.5"],["23.976","23.976"],["24.0","24.0"],["24.5","24.5"],["25.0","25.0"]])
					return
			elif l[0] == "[":
				print "[FP] Load subtitle TXT mpl2"
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
		except:
			o.close()
			oo.close()
			print "I/O error({0}): {1}".format(e.errno, e.strerror)
			print "Error loadtxt_type"
			self.session.open(MessageBox,"Error load subtitle !!!",  MessageBox.TYPE_ERROR)
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
		except:
			self.subtitle = []
			o.close()
			print "Error loadtxt"
			self.session.open(MessageBox,"Error load subtitle !!!",  MessageBox.TYPE_ERROR)

	def debugPrint(self, text):
		if self.debug:
			print text

	def loadsrt(self):
		try:
			self.subtitle = []
			print "[FP] Load subtitle STR"
			if not self.opensubtitle == "":
				o = open(self.opensubtitle,'r')
				# pomijamy BOM jezeli jest
				while True:
					d = o.read(1)
					if d == "1":
						o.seek(-1,1)
						break
				while True:
					nr = o.readline().replace("\r\n","\n")
					self.debugPrint(nr)
					if len(nr) == 0:break
					if nr == "\n": continue
					nr = nr.strip()
					tim = o.readline().replace("\r\n","\n")
					if len(tim) == 0:break
					tim = tim.strip()
					self.debugPrint(tim)
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
			o.close()
			print "Error loadsrt"
			print str(e)
			self.session.open(MessageBox,"Error load subtitle !!!",  MessageBox.TYPE_ERROR)

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
		seekable = self.getSeek()
		if seekable is None:
			return
		seekable.seekTo(pts)

	def doSeekRelative(self, pts):
		seekable = self.getSeek()
		if seekable is None:
			return
		seekable.seekRelative(pts<0 and -1 or 1, abs(pts))

	def updateChannelChange(self, position):
		self.seeksubtitle = self.seeksubtitle + position
		self.setTextForAllLInes(str(self.seeksubtitle)+" sek")

	def channelup(self):
		updateChannelChange(+0.5)

	def channeldown(self):
		updateChannelChange(-0.5)

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

	def text(self):
		if self.enablesubtitle == True:
			self.enablesubtitle = False
			self.setTextForAllLInes("")
		else:
			self.enablesubtitle = True

	def menu(self):
		global i1,i2
                self.session.open(MessageBox,i1+"\n\n"+i2,  MessageBox.TYPE_INFO)

	def audio(self):
		from Screens.AudioSelection import AudioSelection
		self.session.openWithCallback(self.audioSelected, AudioSelection, infobar=self)

	def audioSelected(self, ret=None):
		print "[BlackHarmonyPlayer infobar::audioSelected]", ret

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
#			print vars(self)
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

	def info(self):
		self.hideOSDTimer.stop()
		if self.stateinfo == "Hide":
			self.stateinfo = "Show"
			self.setVisibleForAll(True, "OSD")
			self.hideOSDTimer.start(self.autoHideTime, True) # singleshot

		else:
			self.stateinfo = "Hide"
			self.setVisibleForAll(False, "OSD")

	def setFontForAll(self):
		for fontLine in self.fontLines:
			self[fontLine].instance.setFont(gFont(self.fonttype_list[self.fonttype_nr], self.fontsize))

	def left(self):
		if self.stateinfo == "Hide":
			self.fontsize = self.fontsize - 2
			print "font size = ",self.fontsize
			self.setFontForAll()
		else:
			self.updateOSDPosition(-5, 0)

	def right(self):
		if self.stateinfo == "Hide":
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

	def updateOSDPosition(self, xPos, yPos ):
		self.osdPosX = self.osdPosX + xPos
		self.osdPosY = self.osdPosY + yPos
		for val in self.values() + self.renderer:
			if isinstance(val, GUIComponent):
				if self.isNotFontLine(val):
					x, y = val.getPosition()
					val.instance.move(ePoint(x + xPos, y + yPos))


	def up(self):
		if self.stateinfo == "Hide":
			self.updateTextMovement(-5)
		else:
			self.updateOSDPosition(0, -5)

	def down(self):
		if self.stateinfo == "Hide":
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


class BlackHarmonyPlayerStart(Screen):

	def __init__(self, session):
		global i1
		self.sortDate = False
		self.openmovie = ""
		self.opensubtitle = ""
		self.skin = """
  <screen name="BlackHarmonyPlayer" position="center,center" size="1920,1080" title="InfoBar" flags="wfNoBorder" backgroundColor="transparent">
    <widget name="InfoBarBG" position="200,10" zPosition="-1" size="1529,213" pixmap="BlackHarmony/bg_design/infobarmovie.png" />
    <widget name="fpSRT_1" position="0,540" size="1920,220" valign="center" halign="center" font="%s;%d" backgroundColor="background" shadowColor="black" shadowOffset="-3,-2" transparent="1" />
    <widget name="fpSRT_2" position="0,540" size="1920,220" valign="center" halign="center" font="%s;%d" backgroundColor="background" shadowColor="black" shadowOffset="-3,-2" transparent="1" />
    <widget name="fpSRT_3" position="0,540" size="1920,220" valign="center" halign="center" font="%s;%d" backgroundColor="background" shadowColor="black" shadowOffset="-3,-2" transparent="1" />
    <widget name="fpSRT_4" position="0,540" size="1920,220" valign="center" halign="center" font="%s;%d" backgroundColor="background" shadowColor="black" shadowOffset="-3,-2" transparent="1" />

	<widget name="fpSRT_bg" position="0,540" size="1920,220" valign="center" halign="center" backgroundColor="transpBlack" zPosition="1"/>
    
	<widget source="session.CurrentService" render="Pixmap" position="1241,143" size="57,20" pixmap="BlackHarmony/icons/ico_dolby_on.png" zPosition="2" alphatest="blend">
      <convert type="ServiceInfo">IsMultichannel</convert>
      <convert type="ConditionalShowHide" />
    </widget>

    <widget render="Pixmap" position="1367,143" size="36,20" pixmap="BlackHarmony/icons/ico_format_off.png" zPosition="1" alphatest="blend"></widget>
    <widget source="session.CurrentService" render="Pixmap" position="1367,143" size="36,20" pixmap="BlackHarmony/icons/ico_format_on.png" zPosition="2" alphatest="blend">
      <convert type="ServiceInfo">IsWidescreen</convert>
      <convert type="ConditionalShowHide" />
    </widget>

	

    <widget render="Pixmap" position="1318,143" size="29,20" pixmap="BlackHarmony/icons/ico_hd_off.png" zPosition="1" alphatest="blend">
    </widget>
    <widget source="session.CurrentService" render="Pixmap" position="1318,143" size="29,20" pixmap="BlackHarmony/icons/ico_hd_on.png" zPosition="2" alphatest="blend">
      <convert type="ServiceInfo">VideoWidth</convert>
      <convert type="ValueRange">721,1980</convert>
      <convert type="ConditionalShowHide" />
    </widget>
	
	
	

    <widget source="session.CurrentService" render="Label" position="265,50" size="1140,45" font="HD_Thin; 32" valign="center" noWrap="1" backgroundColor="black" transparent="1">
      <convert type="ServiceName">Name</convert>
    </widget>

    <widget backgroundColor="black" font="Roboto_HD; 26" halign="center" position="645,140" render="Label" size="320,30" source="global.CurrentTime" transparent="1" valign="center">
      <convert type="ClockToText">Format: %%a, %%d.%%m.%%Y  %%H:%%M:%%S</convert>
    </widget>

    <widget name="currTimeLabel" position="265,138" size="110,30" valign="left" halign="center" font="Roboto_HD; 26" backgroundColor="background" shadowColor="black" shadowOffset="-3,-3" transparent="1" foregroundColor="yellow" />
    <widget name="lengthTimeLabel" position="375,138" size="110,30" valign="left" halign="center" font="Roboto_HD; 26" backgroundColor="background" shadowColor="black" shadowOffset="-3,-3" transparent="1" />
    <widget name="remainedLabel" position="485,138" size="110,30" valign="left" halign="center" font="Roboto_HD; 26" backgroundColor="background" shadowColor="black" shadowOffset="-3,-3" transparent="1" foregroundColor="green" />


 <widget name="progressBar" position="264,113" size="1141,6" zPosition="4" pixmap="BlackHarmony/gfx/progress.png" transparent="1" />

    <widget source="session.CurrentService" render="Label" font="Roboto_HD; 26" position="1012,138" size="70,30" halign="right" backgroundColor="black" transparent="1" foregroundColor="light_yellow">
      <convert type="ServiceInfo">VideoWidth</convert>
    </widget>
	

	    <widget source="static_x" render="Label" font="Roboto_HD; 26" position="1085,138" size="15,30" halign="center" backgroundColor="black" transparent="1"/>
		
    <widget source="session.CurrentService" render="Label" font="Roboto_HD; 26" position="1103,138" size="70,30" halign="left" backgroundColor="black" transparent="1" foregroundColor="light_yellow">
      <convert type="ServiceInfo">VideoHeight</convert>
    </widget>

  </screen> """

		Screen.__init__(self, session)
		self["filemovie"] = Label()
		self["filesubtitle"] = Label()
		self["info"] = Label()
		self["key_red"] = StaticText(_("Play"))
		self["key_green"] = StaticText(_("DMnapi"))
		self["key_yellow"] = StaticText(_("About"))
		self["key_blue"] = StaticText(_("Sort"))
		self["info"].setText(i1)
		self.filelist = FileList(None, matchingPattern = "(?i)^.*\.(avi|txt|srt|mpg|vob|divx|m4v|mkv|mp4|m4a|dat|flac|mov|ts)",sortDate=False)
		self["filelist"] = self.filelist
		self["actions"] = ActionMap(["BlackHarmonyPlayerActions"],
			{
				"ok": self.Ok,
				"cancel": self.Exit,
				"up": self.up,
				"down": self.down,
				"left": self.left,
				"right": self.right,
				"red": self.red,
				"green": self.green,
				"yellow": self.yellow,
				"blue": self.blue
			},-2)
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
#		self.session.nav.stopService()
#		self.onClose.append(self.__onClose)

#	def __onClose(self):
#		self.session.nav.playService(self.oldService)

	def left(self):
		self["filelist"].pageUp()

	def right(self):
		self["filelist"].pageDown()

	def up(self):
		self["filelist"].up()

	def down(self):
		self["filelist"].down()

	def red(self):
		if not self.openmovie == "":
			self.session.open(BlackHarmonyPlayer,self.openmovie,self.opensubtitle)

	def green(self):
		self.DMnapi()
		self["filelist"].refresh()

	def yellow(self):
		global i1,i2
		self.session.open(MessageBox,i1+"\n\n"+i2,  MessageBox.TYPE_INFO)

	def blue(self):
		if self.sortDate:
			#print "sortDate=False"
			self["filelist"].sortDateDisable()
			self.sortDate=False
		else:
			#print "sortDate=True"
			self["filelist"].sortDateEnable()
			self.sortDate=True
		self["filelist"].refresh()

	def DMnapi(self):
		if not self["filelist"].canDescent():
			f = self.filelist.getFilename()
			temp = f[-4:]
			if temp != ".srt" and temp != ".txt":
				curSelFile = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
				from Plugins.Extensions.DMnapi.DMnapi import DMnapi
				self.session.openWithCallback(self.dmnapiCallback, DMnapi, curSelFile)
			else:
				self.session.open(MessageBox,_("Please select movie files !\n\n"),MessageBox.TYPE_INFO)

	def dmnapiCallback(self, answer=False):
		self["filelist"].refresh()

	def Ok(self):
		selection = self["filelist"].getSelection()
		if selection[1] == True: # isDir
			self["filelist"].changeDir(selection[0])
			d = self.filelist.getCurrentDirectory()
			if d is None:
				d=""
			self.title = d
		else:
			d = self.filelist.getCurrentDirectory()
			f = self.filelist.getFilename()
			print ">> ",d + f
			temp = f[-4:]
			print temp
			if temp == ".srt" or temp == ".txt":
				if self.opensubtitle == (d + f):
					d = ""
					f = ""
				self["filesubtitle"].setText(f)
				self.opensubtitle = d + f
			else:
				self["filemovie"].setText(f)
				self.openmovie = d + f
#				self.openmovie="/media/hdd/filmy/Depresja.i.Kumple.2012.PL.720p.HDTV.X264.AC3-TVM4iN/Depresja.i.Kumple.2012.PL.720p.HDTV.X264.AC3-TVM4iN.mkv"


	def Exit(self):
		self.close()
