import BlackHarmonyPlayer
from FileList2 import FileList

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

class BlackHarmonyPlayerStart(Screen):

	def __init__(self, session):
		global i1
		self.sortDate = False
		self.openmovie = ""
		self.opensubtitle = ""
		self.skin = """
			<screen name="BlackHarmonyPlayerStart" position="80,80" size="1120,600" title=" ">
				<widget name="filelist" position="15,15" size="1090,450" itemHeight="28" scrollbarMode="showOnDemand" />

				<eLabel position="15,475" size="1090,1" backgroundColor="white" />

				<eLabel text="MOVIE:" position="15,485" size="110,50" font="Regular;20" halign="right" foregroundColor="yellow" backgroundColor="background" transparent="1" />
				<widget name="filemovie" position="130,485" size="970,50" font="Regular;22" backgroundColor="background" transparent="1"/>

				<eLabel text="SUBTITLE:" position="15,515" size="110,50" font="Regular;20" halign="right" foregroundColor="yellow" backgroundColor="background" transparent="1" />
				<widget name="filesubtitle" position="130,515" size="970,50" font="Regular;22" backgroundColor="background" transparent="1"/>

				<eLabel position="15,550" size="1090,1" backgroundColor="white" />

				<ePixmap position="15,560" size="150,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<widget source="key_red" render="Label" position="35,560" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />

				<ePixmap position="160,560" size="150,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<widget source="key_green" render="Label" position="170,560" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />

				<ePixmap position="305,560" size="150,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<widget source="key_yellow" render="Label" position="325,560" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />

				<ePixmap position="450,560" size="150,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget source="key_blue" render="Label" position="475,560" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />

				<widget name="info" position="570,555" size="600,50" valign="center" halign="center" font="Regular;24" backgroundColor="background" transparent="1"/>

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