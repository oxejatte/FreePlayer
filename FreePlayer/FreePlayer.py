from Components.LanguageGOS import gosgettext as _

from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from FileList2 import FileList
from Components.config import config, configfile, ConfigSubsection, ConfigInteger
from Screens.MessageBox import MessageBox
from Components.ServiceEventTracker import ServiceEventTracker
from enigma import iPlayableService
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from ServiceReference import ServiceReference

from Components.AVSwitch import AVSwitch
from os import system

from enigma import eTimer,ePoint,eSize,eLabel,gFont,eConsoleAppContainer,iServiceInformation,eServiceReference,addFont,getDesktop
from skin import parseColor,parseFont

from time import *
import subprocess,fcntl,os

seek1 = 30
seek1t = "30sek"
seek2 = 120
seek2t = "2min"
seek3 = 300
seek3t = "5min"

i1="FreePlayer v1.63 OpenPLI by plfreebox@gmail.com"

def _genHelp():
	global i2
	i2=_("KEYMAP:\n\
up/down - subtitle position\n\
left/right - subtitle size\n\
CH +/- - subtitle time correction\n\
INFO - show time\n\
3/6/9 - seek forward %s/%s/%s\n\
1/4/7 - seek backward %s/%s/%s\n\
red - play\n\
green - pause\n\
yellow - stop\n\
blue - change font color\n\
TEXT - show/hide subtitle\n\
SETUP - show about\n\
OK - change font type\n\
0 - font border width\n\
@ - aspect ratio\n\
OPT - change audiotrack\n\
") % (seek1t, seek2t, seek3t, seek1t, seek2t, seek3t)

ffmpeg_bin_1 = "/usr/bin/ffmpeg"
ffmpeg_bin_2 = resolveFilename(SCOPE_PLUGINS,"Extensions/FreePlayer/bin/ffmpeg")

if fileExists(ffmpeg_bin_1):
	ffmpeg_bin = ffmpeg_bin_1
else:
	ffmpeg_bin = ffmpeg_bin_2

fonts_path_1 = "/usr/share/fonts/"
fonts_path_2 = resolveFilename(SCOPE_PLUGINS,"Extensions/FreePlayer/fonts/")

if fileExists(fonts_path_1):
	fonts_path = fonts_path_1
else:	
	fonts_path = fonts_path_2

class FreePlayer(Screen):

	def __init__(self, session,openmovie,opensubtitle,media):
		self.media = media
		self.session = session
		self.frameon = 1 / 24
		self.seeksubtitle = 0
		self.nrsubtitle = 0
		self.enablesubtitle = True
		self.statesubtitle = "Show"
		self.stateplay = "Stop"
		self.stateinfo = "Hide"
		#self.stateinfo = "Time1"
		self.oldinfo = ""
		self.openmovie = openmovie
		self.opensubtitle = opensubtitle
		self.subtitle = []
		self.fontpos = 540
		self.fontsize = 60
		self.fontpos_ = self.fontpos
		self.fontsize_ = self.fontsize
		self.fonttype_nr = 0
		self.fonttype_nr_ = self.fonttype_nr
		self.fontcolor_nr = 0
		self.fontcolor_nr_ = self.fontcolor_nr
		self.borderWidth = 3
		self.borderWidth_ = self.borderWidth
		self.loadfont()
		self.loadcolor()
		self.loadconfig()
		if self.opensubtitle == "": self.enablesubtitle = False
		print "FontPos = ",self.fontpos
		print "FontSize = ",self.fontsize
		print "FontType = ",self.fonttype_nr
		print "FontColor = ",self.fontcolor_nr
		print "borderWidth = ",self.borderWidth
		print "OpenMovie : ",self.openmovie
		print "OpenSubtitle : ",self.opensubtitle
		self.skin = """
				<screen name="FreePlayer" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="transparent">
					<widget name="i1" position="0,540" size="1280,300" valign="bottom" halign="center" font="%s;%d" backgroundColor="transparent"/>
					<widget name="info1" position="15,15" size="825,50" halign="left" valign="top" font="Regular;40" backgroundColor="transparent"/>
					<widget name="info2" position="845,15" size="420,50" halign="right" valign="top" font="Regular;40" backgroundColor="transparent"/>
				</screen>""" % (self.fonttype_list[self.fonttype_nr],self.fontsize)
		Screen.__init__(self, session)
		self["i1"] = Label()
		self["info1"] = Label()
		self["info2"] = Label()
		self["actions"] = ActionMap(["FreePlayerActions"],
			{
				"ok": self.Ok,
				"cancel": self.Exit,
				"up": self.up,
				"down": self.down,
				"left": self.left,
				"right": self.right,
				"stop": self.Exit,
				"pause": self.pause,
				"play": self.play,
				"info": self.info,
				"key3": self.key3,
				"key6": self.key6,
				"key9": self.key9,
				"key1": self.key1,
				"key4": self.key4,
				"key7": self.key7,
				"channelup": self.channelup,
				"channeldown": self.channeldown,
				"red": self.play,
				"green": self.pause,
				"yellow": self.Exit,
				"blue": self.color,
				"text": self.text,
				"key0": self.bWidth,
				"star": self.av,
				"audio": self.audioselect,
				"menu": self.menu
			},-2)
		self.ServiceName = ""
		self.onShown.append(self.__LayoutFinish)
		self.onClose.append(self.__onClose)
		self.old_policy = self.getPolicy()
		self.tout = eTimer()
		self.tout.callback.append(self.toutEvent)
#		self.tout.start(2000,false)
		self.tinfo = eTimer()
		self.tinfo.callback.append(self.tinfoEvent)

	def toutEvent(self):
		self.tout.stop()
		self["i1"].setText("")

	def tinfoEvent(self):
		self.tinfo.stop()
		if self.stateinfo == "TimeOn" or self.stateinfo == "InfoOn":
			self.stateinfo = "Hide"
			self["info2"].setText("")
		self["info1"].setText("")

	def __onClose(self):
		if self.fontpos != self.fontpos_ or self.fontsize != self.fontsize_ or self.fonttype_nr != self.fonttype_nr_ \
		or self.fontcolor_nr != self.fontcolor_nr_ or self.borderWidth != self.borderWidth_:
			print "[FP] write config"
			o = open(resolveFilename(SCOPE_PLUGINS,"Extensions/FreePlayer/FreePlayer.ini"),'w')
			o.write(str(self.fontpos)+"\n")
			o.write(str(self.fontsize)+"\n")
			o.write(str(self.fonttype_nr)+"\n")
			o.write(str(self.fontcolor_nr)+"\n")
			o.write(str(self.borderWidth)+"\n")
			o.close()
		self.setPolicy(self.old_policy)

	def __LayoutFinish(self):
		self.onShown.remove(self.__LayoutFinish)
		self.__eLabelHasBorderParams = hasattr(self["i1"].instance, 'setBorderWidth') and hasattr(self["i1"].instance, 'setBorderColor')
		if self.__eLabelHasBorderParams:
			self["i1"].instance.setBorderWidth(self.borderWidth)
			self["info1"].instance.setBorderWidth(2)
			self["info2"].instance.setBorderWidth(2)
		self.loadsubtitle()

	def go(self):
		self.timer = eTimer()
		self.timer.callback.append(self.timerEvent)
		self.timer.start(200, False)	#200ms
		temp = self.openmovie[-3:]
		if temp == ".ts":
			root = eServiceReference("1:0:0:0:0:0:0:0:0:0:" + self.openmovie)
		else:
			if self.media == 1:
				root = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + self.openmovie)
			else:
				root = eServiceReference("4099:0:0:0:0:0:0:0:0:0:" + self.openmovie)
		self.session.nav.playService(root)

		currentServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
		if currentServiceRef is not None:
			ref = currentServiceRef.toString()
			self.ServiceName = ServiceReference(ref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')

		self.stateplay = "Play"
		self["i1"].instance.move(ePoint(0,self.fontpos))
		self["i1"].instance.setForegroundColor(parseColor(self.fontcolor_list[self.fontcolor_nr]))
		
		self.stateinfo = "InfoOn"
		self["info1"].setText(self.ServiceName)
		self.tinfo.start(8000)

	def loadfont(self):
		global fonts_path
		o = open(resolveFilename(SCOPE_PLUGINS,"Extensions/FreePlayer/font.ini"),'r')
		self.fonttype_list = []
		self.fonttype_list.append("Regular")
		while True:
			l = o.readline()
			if len(l) == 0: break
			l = l.strip()
			if fileExists(fonts_path+l):
				self.fonttype_list.append(l)
				#print l
				addFont(fonts_path+l, l, 100, False)
		o.close()

	def loadcolor(self):
		o = open(resolveFilename(SCOPE_PLUGINS,"Extensions/FreePlayer/color.ini"),'r')
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
		o = open(resolveFilename(SCOPE_PLUGINS,"Extensions/FreePlayer/FreePlayer.ini"),'r')
		self.fontpos = int(o.readline())
		self.fontsize = int(o.readline())
		self.fonttype_nr = int(o.readline())
		self.fontcolor_nr = int(o.readline())
		self.borderWidth = int(o.readline())
		self.fontpos_ = self.fontpos
		self.fontsize_ = self.fontsize
		self.fonttype_nr_ = self.fonttype_nr
		self.fontcolor_nr_ = self.fontcolor_nr
		self.borderWidth_ = self.borderWidth
		if (self.fonttype_nr+1) > len(self.fonttype_list):
			self.fonttype_nr=0
		if (self.fontcolor_nr+1) > len(self.fontcolor_list):
			self.fontcolor_nr=0
		o.close()

	def timerEvent(self):
		if not self.stateplay == "Play":
			return
		l = self.GetCurrentPosition()
		if not l is None:
			self.showsubtitle(l)
			if self.stateinfo == "Time1" or self.stateinfo == "TimeOn":
				s = "%d:%02d:%02d" % ((l/3600/90000), (l/90000)%3600/60, (l/90000)%60)
				if self.oldinfo != s:
					self.oldinfo = s
					self["info2"].setText(s)
			elif self.stateinfo == "Time2":
				ll = self.GetCurrentLength()
				l = ll - l
				s = "-%d:%02d:%02d" % ((l/3600/90000), (l/90000)%3600/60, (l/90000)%60)
				if self.oldinfo != s:
					self.oldinfo = s
					self["info2"].setText(s)
			elif self.stateinfo == "InfoOn":
				ll = self.GetCurrentLength()
				s = "%d:%02d:%02d/%d:%02d:%02d" % ((l/3600/90000), (l/90000)%3600/60, (l/90000)%60, (ll/3600/90000), (ll/90000)%3600/60, (ll/90000)%60)
				if self.oldinfo != s:
					self.oldinfo = s
					self["info2"].setText(s)

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
					self["i1"].setText(text)
					#print tim," Show ",nr," ",start," --> ",stop,"     ",text
			else:
				if (tim == stop or tim > stop) and nr == self.nrsubtitle:
					self.statesubtitle = "Show"
					self["i1"].setText("")
					#print tim," Hide ",nr," ",
					start," --> ",stop,"     ",text
				elif tim < start and nr == self.nrsubtitle:
					self.statesubtitle = "Show"
					self["i1"].setText("")
					#print tim," Hide ",nr," ",start," --> ",stop,"     ",text

	def usun(self,l):
		if l[0] == "{":
			p = l.find("}")
			if p != -1:
				l = l[p+1:]
				return l
		return l

	def get_codepage(self,sub):
		if sub.startswith('\xef\xbb\xbf'):
			codec = "utf-8-sig"
		else:
			licz = 0
			codec = "windows-1250"
			for uniq, scodec in [((161, 166, 172, 177, 182, 188), "iso-8859-2"),((140, 143, 156, 159, 165, 185),"windows-1250"),((195, 196, 197),"utf-8")]:
				ile = sum([sub.count(chr(i)) for i in uniq])
				if ile > licz:
					licz = ile
					codec = scodec
		return codec
	
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
		global ffmpeg_bin
		try:
			o = open(self.opensubtitle,'r')

			# pomijamy BOM jezeli jest
			while True:
				d = o.read(1)
				if (d == "[") or (d == "{"):
					o.seek(-1,1)
					break

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
					import commands
					ff = self.openmovie
					ff = ff.replace(' ','\ ')
					#cmd = ffmpeg_bin+" -i "+self.openmovie
					cmd = ffmpeg_bin + " -i " + ff
					print cmd
					st,out = commands.getstatusoutput(cmd)
					if out:
						poz = out.find('fps')
						if poz > -1:
							out = out[poz-10:poz]
							poz = out.find(',')
							out = out[poz+1:].strip(' ')
							print "found ffmpeg fps = ",out
							self.frameone = 1 / float(out)
						else:
							self.frameone = 0
					else:
						self.frameone = 0

					if self.frameone == 0:
						print "Unkown AVI - set manual framerate"
						self.session.openWithCallback(self.framerateCallback, ChoiceBox, \
						title=_("FreePlayer not found framerate in movie.\nPlease select manual framerate !"), \
						list=[["23.0","23.0"],["23.5","23.5"],["23.976","23.976"],["24.5","24.5"],["25.0","25.0"]])
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
			print "Error loadtxt_type"
			self.session.open(MessageBox,"Error loading subtitle!",  MessageBox.TYPE_ERROR)
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
			sub_cp = self.get_codepage(open(self.opensubtitle).read().replace('\r',''))
			print "detected codepage: ",sub_cp

			self.subtitle = []
			o = open(self.opensubtitle,'r')

			# pomijamy BOM jezeli jest
			# utf8 = 0
			while True:
				d = o.read(1)
				# if ord(d) == 239: utf8 = utf8 + 1
				# if ord(d) == 187: utf8 = utf8 + 1
				# if ord(d) == 191: utf8 = utf8 + 1
				if (d == "[") or (d == "{"):
					o.seek(-1,1)
					break

			# if utf8 == 3:
			# 	print "Detect BOM UTF8"
			# else:
			# 	utf8 = 0

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
					# if utf8 == 0:l = l.decode('windows-1250').encode('utf-8')
					l = l.decode(sub_cp, 'ignore').encode('utf-8')
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
					# if utf8 == 0:l = l.decode('windows-1250').encode('utf-8')
					l = l.decode(sub_cp, 'ignore').encode('utf-8')
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
					# if utf8 == 0:l = l.decode('windows-1250').encode('utf-8')
					l = l.decode(sub_cp, 'ignore').encode('utf-8')
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
					# if utf8 == 0:l = l.decode('windows-1250').encode('utf-8')
					l = l.decode(sub_cp, 'ignore').encode('utf-8')
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
			self.session.open(MessageBox,_("Error loading subtitle!"),  MessageBox.TYPE_ERROR)

	def loadsrt(self):
		try:
			self.subtitle = []
			print "[FP] Load subtitle SRT"
			if not self.opensubtitle == "":

				o = open(self.opensubtitle,'r')

				sub_cp = self.get_codepage(open(self.opensubtitle).read().replace('\r',''))
				print "detected codepage: ",sub_cp
				
				# pomijamy BOM jezeli jest
				# utf8 = 0

				while True:
					d = o.read(1)
					# if ord(d) == 239: utf8 = utf8 + 1
					# if ord(d) == 187: utf8 = utf8 + 1
					# if ord(d) == 191: utf8 = utf8 + 1
					if d == "1":
						o.seek(-1,1)
						break

				# if utf8 == 3:
				# 	print "Detect BOM UTF8"
				# else:
				# 	utf8 = 0

				while True:
					#print ">"
					nr = o.readline()
					nr = nr.strip("\r")
					#print nr
					if len(nr) == 0:break
					if nr == "\n": continue
					#if (ord(nr[0])<0x30)or(ord(nr[0])>0x39): continue
					#print int(nr[0])
					nr = nr.strip()

					tim = o.readline()
					if len(tim) == 0:break
					tim = tim.strip()
					#print tim

					l1 = o.readline()
					if len(l1) == 0:break
					l1 = l1.strip()
					#print l1

					l2 = o.readline()
					if len(l2) == 0:break
					l2 = l2.strip("\r")
					#print l2
					if not l2 == "\n":
						l2 = l2.strip()
						l = l1 + "\n" + l2
						l3 = o.readline()
						if len(l3) == 0:break
						l3 = l3.strip("\r")
						#print l3
						if not l3 == "\n":
							l3 = l3.strip()
							l = l1 + "\n " + l2 + "\n" + l3
							l4 = o.readline()
							if len(l4) == 0:break
							l4 = l4.strip("\r")
							#print l4
							if not l4 == "\n":
								l4 = l4.strip()
								l = l1 + "\n " + l2 + "\n" + l3 + "\n" + l4
								n = o.readline()
								if len(n) == 0:break
					else:
						l = l1
					# if utf8 == 0: l = l.decode('windows-1250').encode('utf-8')
					l = l.decode(sub_cp, 'ignore').encode('utf-8')
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
		except:
			self.subtitle = []
			o.close()
			print "Error loadsrt"
			self.session.open(MessageBox,_("Error loading subtitle!"),  MessageBox.TYPE_ERROR)

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
		if self.stateinfo == "Hide":
			self.stateinfo = "TimeOn"
			self.tinfo.start(6000)
		# self["info1"].setText(self.ServiceName
		# self.tname.start(8000)

	def channelup(self):
		self.seeksubtitle = self.seeksubtitle + 0.5
		self["i1"].setText(str(self.seeksubtitle)+" sek")
		self.tout.start(2000)

	def channeldown(self):
		self.seeksubtitle = self.seeksubtitle - 0.5
		self["i1"].setText(str(self.seeksubtitle)+" sek")
		self.tout.start(2000)

	def key3(self):
		if self.stateplay == "Play":
			self.doSeekRelative((seek1-10) * 90000)

	def key6(self):
		if self.stateplay == "Play":
			self.doSeekRelative((seek2-10) * 90000)

	def key9(self):
		if self.stateplay == "Play":
			self.doSeekRelative((seek3-10) * 90000)

	def key1(self):
		if self.stateplay == "Play":
			self.doSeekRelative(-(seek1+10) * 90000)

	def key4(self):
		if self.stateplay == "Play":
			self.doSeekRelative(-(seek2+10) * 90000)

	def key7(self):
		if self.stateplay == "Play":
			self.doSeekRelative(-(seek3+10) * 90000)

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
			self["i1"].setText("")
		else:
			self.enablesubtitle = True

	def menu(self):
		global i1, i2
		self.session.open(MessageBox,i1+"\n\n"+i2,  MessageBox.TYPE_INFO)

	def audioselect(self):
		service = self.session.nav.getCurrentService()
		if service is not None:
			audio = service.audioTracks()
			if audio:
				n = audio.getNumberOfTracks()
				w = audio.getCurrentTrack()
				#print "current nr:",w
				idx = 0
				lista = []
				while idx < n:
					i = audio.getTrackInfo(idx)
					languages = i.getLanguage().split('/')
					description = i.getDescription();
					opis = description + " " + languages[0]
					if w == idx:
						opis = opis + "      x"
					print idx,"  ",opis
					lista.append([opis,str(idx)])
					idx += 1
				print lista
				self.session.openWithCallback(self.audioselect_, ChoiceBox,title=_("Please select AudioTrack"),list = lista)

	def audioselect_(self,val):
		if val is not None:
			print "AudioSelect = ",val[1]
			id = int(val[1])
			service = self.session.nav.getCurrentService()
			audio = service and service.audioTracks()
			if audio is not None and service is not None:
				if audio.getNumberOfTracks() > id and id >= 0:
					audio.selectTrack(id)
					print "SelectTrack"


	def info(self):
		if self.stateinfo == "Hide":
			self.stateinfo = "InfoOn"
			self["info1"].setText(self.ServiceName)
			self.tinfo.start(6000)
		elif self.stateinfo == "InfoOn":
			self.stateinfo = "Time1"
			#self["info1"].setText(self.ServiceName)
			#self.tinfo.start(6000)
		elif self.stateinfo == "Time1":
			self.stateinfo = "Time2"
			#self["info1"].setText(self.ServiceName)
			#self.tinfo.start(6000)
		else:
			self.stateinfo = "Hide"
			self.tinfo.stop()
			self["info1"].setText("")
			self["info2"].setText("")

	def left(self):
		self.fontsize = self.fontsize - 2
		print "font size = ",self.fontsize
		self["i1"].instance.setFont(gFont(self.fonttype_list[self.fonttype_nr], self.fontsize))
		self["i1"].setText("Line1\nLine2\nLine3")
		self.tout.start(2000)

	def right(self):
		self.fontsize = self.fontsize + 2
		print "font size = ",self.fontsize
		self["i1"].instance.setFont(gFont(self.fonttype_list[self.fonttype_nr], self.fontsize))
		self["i1"].setText("Line1\nLine2\nLine3")
		self.tout.start(2000)

	def up(self):
		self.fontpos = self.fontpos - 5
		print "pos y = ",self.fontpos
		self["i1"].setText("Line1\nLine2\nLine3")
		self["i1"].instance.move(ePoint(0,self.fontpos))
		self.tout.start(2000)

	def down(self):
		self.fontpos = self.fontpos + 5
		print "pos y = ",self.fontpos
		self["i1"].setText("Line1\nLine2\nLine3")
		self["i1"].instance.move(ePoint(0,self.fontpos))
		self.tout.start(2000)

	def bWidth(self):
		self.borderWidth = self.borderWidth + 1
		if self.borderWidth == 6:
			self.borderWidth = 0
		print "borderWidth = ",self.borderWidth
		self["i1"].setText("borderWidth:"+str(self.borderWidth))
		if self.__eLabelHasBorderParams:
			self["i1"].instance.setBorderWidth(self.borderWidth)
		self.tout.start(2000)

	def color(self):
		self.fontcolor_nr = self.fontcolor_nr + 1
		if self.fontcolor_nr == len(self.fontcolor_list):
			self.fontcolor_nr = 0
		self["i1"].instance.setForegroundColor(parseColor(self.fontcolor_list[self.fontcolor_nr]))
		self["i1"].setText("Color"+str(self.fontcolor_nr))
		self.tout.start(2000)

	def Ok(self):
		self.fonttype_nr = self.fonttype_nr + 1
		if self.fonttype_nr == len(self.fonttype_list):
			self.fonttype_nr = 0
		self["i1"].instance.setFont(gFont(self.fonttype_list[self.fonttype_nr], self.fontsize))
		self["i1"].setText("Font"+str(self.fonttype_nr))
		self.tout.start(2000)

	def Exit(self):
		self.stateplay = "Stop"
		self.timer.stop()
		self.session.nav.stopService()
		self.close()

	def getAspect(self):
		return AVSwitch().getAspectRatioSetting()

	def getAspectString(self,aspectnum):
		return {0: _("4:3 Letterbox"), 1: _("4:3 PanScan"), 2: _("16:9"), 3: _("16:9 always"), 4: _("16:10 Letterbox"), 5: _("16:10 PanScan"), 6: _("16:9 Letterbox")}[aspectnum]

	def setAspect(self,aspect):
		map = {0: "4_3_letterbox", 1: "4_3_panscan", 2: "16_9", 3: "16_9_always", 4: "16_10_letterbox", 5: "16_10_panscan",  6: "16_9_letterbox"}
		config.av.aspectratio.setValue(map[aspect])
		AVSwitch().setAspectRatio(aspect)

	def getPolicy(self):
		try:
			re  = open("/proc/stb/video/policy", "r").read()
			print "getPolicy : ",re
			return re
		except IOError:
			return ""

	def getPolicyChoices(self):
		try:
			re = open("/proc/stb/video/policy_choices", "r").read().strip().split(' ')
			print "getPolicyChoices : ",re
			return re,len(re)
		except IOError:
			return None,0

	def setPolicy(self,p):
		try:
			open("/proc/stb/video/policy", "w").write(p)
			print "setPolicy : ",p
		except IOError:
			pass

	def av(self):
		temp = int(self.getAspect())
		print self.getAspectString(temp)
		temp = temp + 1
		if temp > 6:
			temp=0
		self.setAspect(temp)
		print self.getAspectString(temp)
		self["i1"].setText(self.getAspectString(temp))
		self.tout.start(2000)

class FreePlayerStart(Screen):

	def __init__(self, session):
		global i1
		self.media = 1	#1 = gstreamer
		self.sortDate = 1
		self.openmovie = ""
		self.opensubtitle = ""
		self.skin = """
			<screen name="FreePlayer" position="center,90" size="1120,580" title=" ">
				<widget name="filelist" position="15,5" size="1090,450" itemHeight="28" scrollbarMode="showOnDemand" />

				<eLabel position="15,460" size="1090,1" backgroundColor="white" />

				<eLabel text="MOVIE:" position="15,470" size="140,50" font="Regular;22" halign="right" foregroundColor="yellow" backgroundColor="background" transparent="1" />
				<widget name="filemovie" position="160,470" size="960,50" font="Regular;22" backgroundColor="background" transparent="1"/>

				<eLabel text="SUBTITLE:" position="15,500" size="140,50" font="Regular;22" halign="right" foregroundColor="yellow" backgroundColor="background" transparent="1" />
				<widget name="filesubtitle" position="160,500" size="960,50" font="Regular;22" backgroundColor="background" transparent="1"/>

				<eLabel position="15,530" size="1090,1" backgroundColor="white" />

				<ePixmap position="15,540" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="15,540" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />

				<ePixmap position="160,540" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<widget source="key_green" render="Label" position="160,540" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />

				<ePixmap position="305,540" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" /> 
				<widget source="key_yellow" render="Label" position="305,540" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" /> 

				<ePixmap position="450,540" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" /> 
				<widget source="key_blue" render="Label" position="450,540" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" /> 

				<widget name="info2" position="555,525" size="600,50" valign="center" halign="center" font="Regular;16" backgroundColor="background" transparent="1"/>
				<widget name="info" position="555,545" size="600,50" valign="center" halign="center" font="Regular;16" backgroundColor="background" transparent="1"/>

			</screen> """

		Screen.__init__(self, session)
		self["filemovie"] = Label()
		self["filesubtitle"] = Label()
		self["info"] = Label()
		self["info2"] = Label()
		self["key_red"] = StaticText(_("Play"))
		self["key_green"] = StaticText(_("DMnapi"))
		self["key_yellow"] = StaticText(_("LibMedia"))
		self["key_blue"] = StaticText(_("Sort"))
		self["info"].setText(i1)
		self.load()
		self.showinfo2()
		self.filelist = FileList(None, matchingPattern = "(?i)^.*\.(avi|txt|srt|mpg|vob|divx|m4v|mkv|mp4|m4a|dat|flac|mov|ts)",sortDate=False)
		self["filelist"] = self.filelist
		self.sort()
		self["actions"] = ActionMap(["FreePlayerActions"],
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
				"blue": self.blue,
				"info": self.info,
				"play": self.red,
				"menu": self.menu
			},-2)
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		self.onClose.append(self.__onClose)

	def showinfo2(self):
		s_ = ""
		if self.sortDate == 1:
			s_ = s_+_("Sort by: A-Z")
		else:
			s_ = s_+_("Sort by: Date")
		s_ = s_ + "   "
		if self.media == 1:
			s_ = s_+_("Multimedia Framework: GStreamer")
		else:
			s_ = s_+_("Multimedia Framework: EPlayer3")
		self["info2"].setText(s_)

	def save(self):
		o = open(resolveFilename(SCOPE_PLUGINS,"Extensions/FreePlayer/config.ini"),'w')
		o.write(str(self.media)+"\n")
		o.write(str(self.sortDate)+"\n")
		o.write(str(seek1)+"\n")
		o.write(str(seek2)+"\n")
		o.write(str(seek3)+"\n")
		o.close()

	def load(self):
		global seek1, seek2, seek3, seek1t, seek2t, seek3t
		o = open(resolveFilename(SCOPE_PLUGINS,"Extensions/FreePlayer/config.ini"),'r')
		try:
			self.media = int(o.readline())
			self.sortDate = int(o.readline())
			seek1 = int(o.readline())
			seek2 = int(o.readline())
			seek3 = int(o.readline())
		except ValueError:
			self.media = 1
			self.sortDate = 1
			seek1 = 30
			seek2 = 120
			seek3 = 300
		o.close()
		if seek1 % 60:
			seek1t = "%dsek" % seek1
		else:
			seek1t = "%dmin" % (seek1/60)
		if seek2 % 60:
			seek2t = "%dsek" % seek2
		else:
			seek2t = "%dmin" % (seek2/60)
		if seek3 % 60:
			seek3t = "%dsek" % seek3
		else:
			seek3t = "%dmin" % (seek3/60)
		_genHelp()

	def __onClose(self):
		self.session.nav.playService(self.oldService)

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
			self.session.open(FreePlayer,self.openmovie,self.opensubtitle,self.media)

	def green(self):
		self.DMnapi()
		self["filelist"].refresh()

	def yellow(self):
		if self.media == 1:
			self.media = 2
		else:
			self.media = 1
		self.showinfo2()
		self.save()

	def info(self):
		global ffmpeg_bin
		selection = self["filelist"].getSelection()
		if selection[1] == False: # isDir
			d = self.filelist.getCurrentDirectory()
			f = self.filelist.getFilename()
			temp = f[-4:]
#			print temp
			if temp != ".srt" or temp != ".txt":
#				print ">> ",d + f
				ff = d + f
				ff = ff.replace(' ','\ ');
				print ff
				cmd = ffmpeg_bin + " -i " + ff
				from Screens.Console import Console
				self.session.open(Console,"MediaInfo",[cmd])

	def menu(self):
		global i1, i2
		self.session.open(MessageBox,i1+"\n\n"+i2,  MessageBox.TYPE_INFO)

	def blue(self):
		if self.sortDate == 1:
			self.sortDate = 2
		else:
			self.sortDate = 1
		self.sort()
		self.showinfo2()
		self.save()

	def sort(self):
		if self.sortDate == 1:
			self["filelist"].sortDateDisable()
		else:
			self["filelist"].sortDateEnable()
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
				self.session.open(MessageBox,_("Please select movie file!\n\n"),MessageBox.TYPE_INFO)

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


	def Exit(self):
		self.close()
