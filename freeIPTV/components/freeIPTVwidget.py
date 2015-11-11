# -*- coding: utf-8 -*-

from time import sleep as time_sleep
from os import remove as os_remove, path as os_path
from urllib import quote as urllib_quote

from Plugins.Extensions.freeIPTV.inits import *
from Plugins.Extensions.freeIPTV.tools.iptvtools import *
####################################################
#                   E2 components
####################################################
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Tools.BoundFunction import boundFunction
from Tools.LoadPixmap import LoadPixmap
from enigma import getDesktop, eTimer

####################################################
#                   IPTV components
####################################################
from Plugins.Extensions.freeIPTV.iptvdm.iptvdownloadercreator import IsUrlDownloadable
from Plugins.Extensions.freeIPTV.libs.urlparser import urlparser
from Plugins.Extensions.freeIPTV.tools.iptvtypes import strwithmeta
from Plugins.Extensions.freeIPTV.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.freeIPTV.iptvdm.iptvbuffui import freeIPTVBufferingWidget
from Plugins.Extensions.freeIPTV.iptvdm.iptvdmapi import IPTVDMApi, DMItem

from Plugins.Extensions.freeIPTV.components.iptvconfigmenu import ConfigMenu #na razie musi tu byc, pozniej sie zrobi porzadek z hostami
from Plugins.Extensions.freeIPTV.components.confighost import ConfigHostMenu
from Plugins.Extensions.freeIPTV.components.iptvplayer import IPTVStandardMoviePlayer
from Plugins.Extensions.AdvancedFreePlayer.AdvancedFreePlayer import AdvancedFreePlayerStarter
from Plugins.Extensions.freeIPTV.components.iptvlist import IPTVMainNavigatorList
from Plugins.Extensions.freeIPTV.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.freeIPTV.components.iconmenager import IconMenager
from Plugins.Extensions.freeIPTV.components.cover import Cover, Cover3
import Plugins.Extensions.freeIPTV.components.asynccall as asynccall

######################################################
gDownloadManager = None

class freeIPTVwidget(Screen):
    skin =  LoadSkin('freeIPTVwidget')
        
    def __init__(self, session):
        printDBG("freeIPTVwidget.__init__ desktop\n")
        self.session = session
                
        Screen.__init__(self, session)
        self.recorderMode = False #j00zek

        self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
        #self.session.nav.stopService()

        self["key_red"]    = StaticText(_("Exit"))
        self["key_green"]  = StaticText(_("Player > Recorder"))
        self["key_yellow"] = StaticText(_("Refresh"))
        self["key_blue"]   = StaticText(_("More"))

        self["list"] = IPTVMainNavigatorList()
        self["list"].connectSelChanged(self.onSelectionChanged)
        self["statustext"] = Label("Initial Loading...")
        self["actions"] = ActionMap(["freeIPTVListActions", "WizardActions", "DirectionActions", "ColorActions", "NumberActions"],
        {
            "red"     :   self.red_pressed,
            "green"   :   self.green_pressed,
            "yellow"  :   self.yellow_pressed,
            "blue"    :   self.blue_pressed,
            "ok"      :   self.ok_pressed,
            "back"    :   self.back_pressed,
        }, -1)

        self["headertext"] = Label()
        self["console"] = Label()
        
        self["cover"] = Cover()
        self["cover"].hide()
        self["playerlogo"] = Cover()
        
        try:
            for idx in range(5):
                spinnerName = "spinner"
                if idx: spinnerName += '_%d' % idx 
                self[spinnerName] = Cover3()
        except: printExc()

        self.spinnerPixmap = [LoadPixmap(PluginPath + 'icons/' + 'radio_button_on.png'), LoadPixmap(PluginPath + 'icons/' + 'radio_button_off.png')]
        self.useAlternativePlayer = False
        
        self.showMessageNoFreeSpaceForIcon = False
        self.iconMenager = None
        if config.plugins.iptvplayer.showcover.value:
            if not os_path.exists(config.plugins.iptvplayer.SciezkaCache.value):
                mkdirs(config.plugins.iptvplayer.SciezkaCache.value)

            if FreeSpace(config.plugins.iptvplayer.SciezkaCache.value,10):
                self.iconMenager = IconMenager(True)
            else:
                self.showMessageNoFreeSpaceForIcon = True
                self.iconMenager = IconMenager(False)
            self.iconMenager.setUpdateCallBack( self.checkIconCallBack )
        self.showHostsErrorMessage = True
        
        self.onClose.append(self.__onClose)
        #self.onLayoutFinish.append(self.onStart)
        self.onShow.append(self.onStart)
        
        #Defs
        self.searchPattern = CSearchHistoryHelper.loadLastPattern()[1]
        self.searchType = None
        self.workThread = None
        self.host       = None
        self.hostName     = ''
        self.hostFavTypes = []
        
        self.nextSelIndex = 0
        self.currSelIndex = 0
        
        self.prevSelList = []
        self.categoryList = []
      
        self.currList = []
        self.currItem = CDisplayListItem()

        self.visible = True
        self.bufferSize = config.plugins.iptvplayer.requestedBuffSize.value * 1024 * 1024
        
    
        #################################################################
        #                      Inits for Proxy Queue
        #################################################################
       
        # register function in main Queue
        if None == asynccall.gMainFunctionsQueue:
            asynccall.gMainFunctionsQueue = asynccall.CFunctionProxyQueue(self.session)
        asynccall.gMainFunctionsQueue.clearQueue()
        asynccall.gMainFunctionsQueue.setProcFun(self.doProcessProxyQueueItem)

        #main Queue
        self.mainTimer = eTimer()
        self.mainTimer_conn = eConnectCallback(self.mainTimer.timeout, self.processProxyQueue)
        # every 100ms Proxy Queue will be checked  
        self.mainTimer_interval = 100
        self.mainTimer.start(self.mainTimer_interval, True)
        
        # delayed decode cover timer
        self.decodeCoverTimer = eTimer()
        self.decodeCoverTimer_conn = eConnectCallback(self.decodeCoverTimer.timeout, self.doStartCoverDecode) 
        self.decodeCoverTimer_interval = 100
        
        # spinner timer
        self.spinnerTimer = eTimer()
        self.spinnerTimer_conn = eConnectCallback(self.spinnerTimer.timeout, self.updateSpinner) 
        self.spinnerTimer_interval = 200
        self.spinnerEnabled = False
        
        #################################################################
        
        #################################################################
        #                      Inits for IPTV Download Manager
        #################################################################
        global gDownloadManager
        if None == gDownloadManager:
            printDBG('============Initialize Download Menager============')
            gDownloadManager = IPTVDMApi(2, int(config.plugins.iptvplayer.IPTVDMMaxDownloadItem.value))
            if config.plugins.iptvplayer.IPTVDMRunAtStart.value:
                gDownloadManager.runWorkThread() 
        #################################################################
        
        self.activePlayer = None
    #end def __init__(self, session):
        
    def __del__(self):
        printDBG("freeIPTVWidget.__del__ --------------------------")

    def __onClose(self):
        self.session.nav.playService(self.currentService)
        self["list"].disconnectSelChanged(self.onSelectionChanged)
        #self["list"] = None
        #self["actions"] = None
        if None != self.iconMenager:
            self.iconMenager.setUpdateCallBack(None)
            self.iconMenager.clearDQueue()
            self.iconMenager = None
        self.checkUpdateTimer_conn = None
        self.checkUpdateTimer = None
        self.mainTimer_conn = None
        self.mainTimer = None
        self.decodeCoverTimer_conn = None
        self.decodeCoverTimer = None
        self.spinnerTimer_conn = None
        self.spinnerTimer = None

        try:
            asynccall.gMainFunctionsQueue.setProcFun(None)
            asynccall.gMainFunctionsQueue.clearQueue()
            iptv_system('echo 1 > /proc/sys/vm/drop_caches')
        except:
            printExc()
        self.activePlayer = None
            
    def loadSpinner(self):
        try:
            if "spinner" in self:
                self["spinner"].setPixmap(self.spinnerPixmap[0])
                for idx in range(4):
                    spinnerName = 'spinner_%d' % (idx + 1)
                    self[spinnerName].setPixmap(self.spinnerPixmap[1])
        except: printExc()
        
    def showSpinner(self):
        if None != self.spinnerTimer:
            self._setSpinnerVisibility(True)
            self.spinnerTimer.start(self.spinnerTimer_interval, True)
    
    def hideSpinner(self):
        self._setSpinnerVisibility(False)
    
    def _setSpinnerVisibility(self, visible=True):
        self.spinnerEnabled = visible
        try:
            if "spinner" in self:
                for idx in range(5):
                    spinnerName = "spinner"
                    if idx: spinnerName += '_%d' % idx
                    self[spinnerName].visible = visible
        except: printExc()
        
    def updateSpinner(self):
        try:
            if self.spinnerEnabled and None != self.workThread:
                if self.workThread.isAlive():
                    if "spinner" in self:
                        x, y = self["spinner"].getPosition()
                        x   += self["spinner"].getWidth()
                        if x > self["spinner_4"].getPosition()[0]:
                            x = self["spinner_1"].getPosition()[0]
                        self["spinner"].setPosition(x, y)
                    if None != self.spinnerTimer:
                        self.spinnerTimer.start(self.spinnerTimer_interval, True)
                        return
                elif not self.workThread.isFinished():
                    message = _('It seems that the host "%s" has crashed.') % self.hostName
                    self.session.openWithCallback(self.reportHostCrash, MessageBox, text=message, type=MessageBox.TYPE_YESNO)
            self.hideSpinner()
        except: printExc()
        
    def reportHostCrash(self, ret):
        try:
            if ret:
                msg = urllib_quote('%s|%s|%s' % ('HOST_CRASH', self.hostName, self.getCategoryPath()))
                printDBG(msg)
            self.workThread = None
            self.prevSelList = []
            self.back_pressed()
        except: printExc()

    def processProxyQueue(self):
        if None != self.mainTimer:
            asynccall.gMainFunctionsQueue.processQueue()
            self.mainTimer.start(self.mainTimer_interval, True)
        return
        
    def doProcessProxyQueueItem(self, item):
        try:
            if None == item.retValue[0] or self.workThread == item.retValue[0]:
                if isinstance(item.retValue[1], asynccall.CPQParamsWrapper): getattr(self, method)(*item.retValue[1])
                else: getattr(self, item.clientFunName)(item.retValue[1])
            else:
                printDBG('>>>>>>>>>>>>>>> doProcessProxyQueueItem callback from old workThread[%r][%s]' % (self.workThread, item.retValue))
        except: printExc()
            
    def selectHostVideoLinksCallback(self, thread, ret):
        asynccall.gMainFunctionsQueue.addToQueue("selectMainVideoLinks", [thread, ret])
        
    def getResolvedURLCallback(self, thread, ret):
        asynccall.gMainFunctionsQueue.addToQueue("selectResolvedVideoLinks", [thread, ret])
        
    def callbackGetList(self, addParam, thread, ret):
        asynccall.gMainFunctionsQueue.addToQueue("reloadList", [thread, {'add_param':addParam, 'ret':ret}])
        
    # method called from IconMenager when a new icon has been dowlnoaded
    def checkIconCallBack(self, ret):
        asynccall.gMainFunctionsQueue.addToQueue("displayIcon", [None, ret])
        
    def isInWorkThread(self):
        return None != self.workThread and (not self.workThread.isFinished() or self.workThread.isAlive())
 
    def red_pressed(self):
        self.close()
        return

    def green_pressed(self):
        if self.recorderMode and IsExecutable( DMHelper.GET_WGET_PATH() ):
            self.recorderMode = False
            printDBG( "IPTV - tryb Odtwarzacza" )
            self["key_green"].setText(_("Player > Recorder"))
        elif not IsExecutable( DMHelper.GET_WGET_PATH() ):
            self.recorderMode = False
            self["key_green"].setText(_("Player > Recorder"))
        else:
            self.recorderMode = True
            printDBG( "IPTV - tryb Rekordera" )
            self["key_green"].setText(_("Recorder > Player"))
        return

    def yellow_pressed(self):
        self.getRefreshedCurrList()
        return
     
    def blue_pressed(self):       
        options = []
        
        if -1 < self.canByAddedToFavourites()[0]: 
            options.append((_("Add item to favourites"), "ADD_FAV"))
            options.append((_("Edit favourites"), "EDIT_FAV"))
        elif 'favourites' == self.hostName: options.append((_("Edit favourites"), "EDIT_FAV"))
        options.append((_("Create link for Advanced Free Player"), "AFPURL"))
        options.append((_("IPTV download manager"), "IPTVDM"))
        options.append((_("Info"), "info"))
        
        try:
            host = __import__('Plugins.Extensions.freeIPTV.hosts.' + self.hostName, globals(), locals(), ['GetConfigList'], -1)
            if( len( host.GetConfigList() ) > 0 ):
                options.append((_("Configure host"), "HostConfig"))
        except: printExc()
        self.session.openWithCallback(self.blue_pressed_next, ChoiceBox, title = _("Select option"), list = options)

    def blue_pressed_next(self, ret):
        TextMSG = ''
        if ret:
            if ret[1] == "info": #informacje o wtyczce
                TextMSG = _("Autors: samsamsam, zdzislaw22, mamrot, MarcinO, skalita, huball, matzg, tomashj291")
                self.session.open(MessageBox, TextMSG, type = MessageBox.TYPE_INFO, timeout = 10 )
            elif ret[1] == "IPTVDM":
                self.runIPTVDM()
            elif ret[1] == "HostConfig":
                self.runConfigHostIfAllowed()
    
    def editFavouritesCallback(self, ret=False):
        if ret and 'favourites' == self.hostName: # we must reload host
            self.loadHost()
    
    def setActiveMoviePlayer(self, ret):
        if ret: self.activePlayer.set(ret[1])

    def runIPTVDM(self, callback=None):
        global gDownloadManager
        if None != gDownloadManager:
            from Plugins.Extensions.freeIPTV.iptvdm.iptvdmui import IPTVDMWidget
            if None == callback: self.session.open(IPTVDMWidget, gDownloadManager)
            else: self.session.openWithCallback(callback, IPTVDMWidget, gDownloadManager)
        elif None != callback: callback()
        return
        
    def displayIcon(self, ret=None, doDecodeCover=False):
        # check if displays icon is enabled in options
        if not config.plugins.iptvplayer.showcover.value or None == self.iconMenager :
            return
        
        selItem = self.getSelItem()
        # when ret is != None the method is called from IconMenager 
        # and in this variable the url for icon which was downloaded 
        # is returned
        # if icon for other than selected item has been downloaded 
        # the displayed icon will not be changed
        if ret != None and selItem != None and ret != selItem.iconimage:
            return
    
        # Display icon
        if selItem and '' != selItem.iconimage and self.iconMenager:
            # check if we have this icon and get the path to this icon on disk
            iconPath = self.iconMenager.getIconPathFromAAueue(selItem.iconimage)
            printDBG('displayIcon -> getIconPathFromAAueue: ' + selItem.iconimage)
            if '' != iconPath and not self["cover"].checkDecodeNeeded(iconPath):
                self["cover"].show()
                return
            else:
                if doDecodeCover:
                    self["cover"].decodeCover(iconPath, self.updateCover, "cover")
                else:
                    self.decodeCoverTimer.start(self.decodeCoverTimer_interval, True)
        self["cover"].hide()
        
    def doStartCoverDecode(self):
        if self.decodeCoverTimer:
            self.displayIcon(None, doDecodeCover=True)
            
    def updateCover(self, retDict):
        # retDict - return dictionary  {Ident, Pixmap, FileName, Changed}
        printDBG('updateCover')
        if retDict:
            printDBG("updateCover retDict for Ident: %s " % retDict["Ident"])
            updateIcon = False
            if 'cover' == retDict["Ident"]:
                #check if we have icon for right item on list
                selItem = self.getSelItem()
                if selItem and '' != selItem.iconimage:
                    # check if we have this icon and get the path to this icon on disk
                    iconPath = self.iconMenager.getIconPathFromAAueue(selItem.iconimage)
                    
                    if iconPath == retDict["FileName"]:
                        # now we are sure that we have right icon
                        updateIcon = True
                        self.decodeCoverTimer_interval = 100
                    else: self.decodeCoverTimer_interval = 1000
            else: 
                updateIcon = True
            if updateIcon:
                if None != retDict["Pixmap"]:
                    self[retDict["Ident"]].updatePixmap(retDict["Pixmap"], retDict["FileName"])
                    self[retDict["Ident"]].show()
                else:
                    self[retDict["Ident"]].hide()
        else:
            printDBG("updateCover retDict empty")
    #end updateCover(self, retDict):
                
    def changeBottomPanel(self):
        self.displayIcon()
        selItem = self.getSelItem()
        if selItem and selItem.description != '':
            data = selItem.description
            sData = data.replace('\n','')
            self["console"].setText(sData)
        else:
            self["console"].setText('')
    
    def onSelectionChanged(self):
        self.changeBottomPanel()

    def back_pressed(self):
        try:
            if self.isInWorkThread():
                if self.workThread.kill():
                    self.workThread = None
                    self["statustext"].setText("Operation aborted!")
                return
        except: return    
        if self.visible:
                       
            if len(self.prevSelList) > 0:
                self.nextSelIndex = self.prevSelList.pop()
                self.categoryList.pop()
                printDBG( "back_pressed prev sel index %s" % self.nextSelIndex )
                self.requestListFromHost('Previous')
            else:
                self.selectHost()
        else:
            self.showWindow()
    #end back_pressed(self):
    
    def ok_pressed(self, eventFrom='remote', useAlternativePlayer=False):
        self.useAlternativePlayer = useAlternativePlayer
        if self.visible:
            sel = None
            try:
                sel = self["list"].l.getCurrentSelection()[0]
            except:
                printExc
                self.getRefreshedCurrList()
                return
            if sel is None:
                printDBG( "ok_pressed sel is None" )
                self.getInitialList()
                return
            elif len(self.currList) <= 0:
                printDBG( "ok_pressed list is empty" )
                self.getRefreshedCurrList()
                return
            else:
                printDBG( "ok_pressed selected item: %s" % (sel.name) )
                
                item = self.getSelItem()  
                self.currItem = item
                
                #Get current selection
                currSelIndex = self["list"].getCurrentIndex()
                #remember only prev categories
                if item.type in [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_PICTURE]:
                    if CDisplayListItem.TYPE_AUDIO == item.type: 
                        self.bufferSize = config.plugins.iptvplayer.requestedAudioBuffSize.value * 1024
                    else: self.bufferSize = config.plugins.iptvplayer.requestedBuffSize.value * 1024 * 1024
                    # check if separete host request is needed to get links to VIDEO
                    if item.urlSeparateRequest == 1:
                        printDBG( "ok_pressed selected TYPE_VIDEO.urlSeparateRequest" )
                        self.requestListFromHost('ForVideoLinks', currSelIndex)
                    else:
                        printDBG( "ok_pressed selected TYPE_VIDEO.selectLinkForCurrVideo" )
                        self.selectLinkForCurrVideo()
                elif item.type == CDisplayListItem.TYPE_CATEGORY:
                    printDBG( "ok_pressed selected TYPE_CATEGORY" )
                    self.currSelIndex = currSelIndex
                    self.requestListFromHost('ForItem', currSelIndex, '')
                elif item.type == CDisplayListItem.TYPE_MORE:
                    printDBG( "ok_pressed selected TYPE_MORE" )
                    self.currSelIndex = currSelIndex
                    self.requestListFromHost('ForMore', currSelIndex, '')
                else:
                    printDBG( "ok_pressed selected TYPE_SEARCH" )
                    self.currSelIndex = currSelIndex
                    self.startSearchProcedure(item.possibleTypesOfSearch)
        else:
            self.showWindow()
    #end ok_pressed(self):
    
    def selectMainVideoLinks(self, ret):
        printDBG( "selectMainVideoLinks" )
        self["statustext"].setText("")
        self["list"].show()
        
        # ToDo: check ret.status if not OK do something :P
        if ret.status != RetHost.OK:
            printDBG( "++++++++++++++++++++++ selectHostVideoLinksCallback ret.status = %s" % ret.status )
        else:
            # update links in List
            currSelIndex = self.getSelIndex()
            if -1 == currSelIndex: return
            self.currList[currSelIndex].urlItems = ret.value
        self.selectLinkForCurrVideo()
    #end selectMainVideoLinks(self, ret):
    
    def selectResolvedVideoLinks(self, ret):
        printDBG( "selectResolvedVideoLinks" )
        self["statustext"].setText("")
        self["list"].show()
        linkList = []
        if ret.status == RetHost.OK and isinstance(ret.value, list):
            for item in ret.value:
                if isinstance(item, CUrlItem): 
                    item.urlNeedsResolve = 0 # protection from recursion 
                    linkList.append(item)
                elif isinstance(item, basestring): linkList.append(CUrlItem(item, item, 0))
                else: printExc("selectResolvedVideoLinks: wrong resolved url type!")
        else: printExc()
        self.selectLinkForCurrVideo(linkList)
 
    def getSelIndex(self):
        currSelIndex = self["list"].getCurrentIndex()
        if len(self.currList) > currSelIndex:
            return currSelIndex
        return -1

    def getSelItem(self):
        currSelIndex = self["list"].getCurrentIndex()
        if len(self.currList) <= currSelIndex:
            printDBG( "ERROR: getSelItem there is no item with index: %d, listOfItems.len: %d" % (currSelIndex, len(self.currList)) )
            return None
        return self.currList[currSelIndex]
        
    def getSelectedItem(self):
        sel = None
        try:
            sel = self["list"].l.getCurrentSelection()[0]
        except:return None
        return sel
        
    def onStart(self):
        self.onShow.remove(self.onStart)
        #self.onLayoutFinish.remove(self.onStart)
        self.loadSpinner()
        self.hideSpinner()
        self.selectHost()
    
    def selectHost(self):
        self.host = None
        self.hostName = ''
        self.nextSelIndex = 0
        self.prevSelList = []
        self.categoryList = []
        self.currList = []
        self.currItem = CDisplayListItem()

        self.displayHostsList = [] 
        brokenHostList = []
        print GotHostsList
        for hostName in GotHostsList:
            hostEnabled  = False
            try:
                exec('if config.plugins.iptvplayer.host' + hostName + '.value: hostEnabled = True')
            except:
                hostEnabled = False
            if True == hostEnabled:
                if not config.plugins.iptvplayer.devHelper.value:
                    try:
                        _temp = __import__('Plugins.Extensions.freeIPTV.hosts.' + hostName, globals(), locals(), ['gettytul'], -1)
                        title = _temp.gettytul()
                    except:
                        printExc('get host name exception for host "%s"' % hostName)
                        brokenHostList.append('host'+hostName)
                        continue # do not use default name if import name will failed
                else:
                    printDBG('Plugins.Extensions.freeIPTV.hosts.' + hostName)
                    _temp = __import__('Plugins.Extensions.freeIPTV.hosts.' + hostName, globals(), locals(), ['gettytul'], -1)
                    title = _temp.gettytul()
                self.displayHostsList.append((title, hostName))
        self.displayHostsList.append((_("Configuration"), "config"))
        
        # prepare info message when some host or update cannot be used
        errorMessage = ""
        if len(brokenHostList) > 0:
            errorMessage = _("Following host are broken or additional python modules are needed.") + '\n' + '\n'.join(brokenHostList)
                
        try:     import json 
        except:
            try: import simplejson
            except: errorMessage = errorMessage + "\n" + _("JSON module not available!")
        
        if "" != errorMessage and True == self.showHostsErrorMessage:
            self.showHostsErrorMessage = False
            self.session.openWithCallback(self.displayListOfHosts, MessageBox, errorMessage, type = MessageBox.TYPE_INFO, timeout = 10 )
        else:
            self.displayListOfHosts()
        return

    def displayListOfHosts(self, arg = None):
        self.session.openWithCallback(self.selectHostCallback, ChoiceBox, title=_("Select service"), list = self.displayHostsList)
    
    def selectHostCallback(self, ret):
        hasIcon = False
        nextFunction = None
        if ret:
            if ret[1] == "config":
                nextFunction = self.runConfig
            elif ret[1] == "noupdate":
                self.close()
                return
            elif ret[1] == "IPTVDM":
                self.runIPTVDM(self.selectHost)
                return
            else: # host selected
                self.hostName = ret[1] 
                self.loadHost()
                
            if self.showMessageNoFreeSpaceForIcon and hasIcon:
                self.showMessageNoFreeSpaceForIcon = False
                self.session.open(MessageBox, (_("There is no free space on the drive [%s].") % config.plugins.iptvplayer.SciezkaCache.value) + "\n" + _("New icons will not be available."), type = MessageBox.TYPE_INFO, timeout=10)
        else:
            self.close()
            return
            
        if nextFunction:
            nextFunction()

    def runConfig(self):
        self.session.openWithCallback(self.configCallback, ConfigMenu)
        
    def runConfigHostIfAllowed(self):
        self.runConfigHost()

    def runConfigHost(self):
        self.session.openWithCallback(self.runConfigHostCallBack, ConfigHostMenu, hostName = self.hostName)
        
    def runConfigHostCallBack(self, confgiChanged=False):
        if confgiChanged: self.loadHost()

    def loadHost(self):
        self.hostFavTypes = []
        if not config.plugins.iptvplayer.devHelper.value:
            try:
                _temp = __import__('Plugins.Extensions.freeIPTV.hosts.' + self.hostName, globals(), locals(), ['IPTVHost'], -1)
                self.host = _temp.IPTVHost()
                if not isinstance(self.host, IHost):
                    printDBG("Host [%r] does not inherit from IHost" % self.hostName)
                    self.close()
                    return
            except:
                printExc( 'Cannot import class IPTVHost for host [%r]' %  self.hostName)
                self.close()
                return
        else:
            _temp = __import__('Plugins.Extensions.freeIPTV.hosts.' + self.hostName, globals(), locals(), ['IPTVHost'], -1)
            self.host = _temp.IPTVHost()
            
        self.loadHostData();

    def loadHostData(self):
        if None != self.activePlayer: self.activePlayer.save()
        self.activePlayer = CMoviePlayerPerHost(self.hostName)

        # change logo for player
        self["playerlogo"].hide()
        try:
            hRet= self.host.getLogoPath()
            printDBG(hRet)
            if hRet.status == RetHost.OK and  len(hRet.value):
                logoPath = hRet.value[0]
                    
                if logoPath != '':
                    printDBG('Logo Path: ' + logoPath)
                    self["playerlogo"].decodeCover(logoPath, \
                                                   self.updateCover, \
                                                   "playerlogo")
        except: printExc()
        
        # get types of items which can be added as favourites
        self.hostFavTypes = []
        try:
            hRet = self.host.getSupportedFavoritesTypes()
            if hRet.status == RetHost.OK: self.hostFavTypes = hRet.value
        except: printExc('The current host crashed')
        
        # request initial list from host        
        self.getInitialList()
    #end selectHostCallback(self, ret):

    def selectLinkForCurrVideo(self, customUrlItems=None):
        if not self.visible:
            self["statustext"].setText("")
            self.showWindow()
        
        item = self.getSelItem()
        if item.type not in [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_PICTURE]:
            printDBG("Incorrect icon type[%s]" % item.type)
            return
        
        if None == customUrlItems: links = item.urlItems
        else: links = customUrlItems
        
        options = []
        for link in links:
            printDBG("selectLinkForCurrVideo: |%s| |%s|" % (link.name, link.url))
            if type(u'') == type(link.name):
                link.name = link.name.encode('utf-8', 'ignore')
            if type(u'') == type(link.url):
                link.url = link.url.encode('utf-8', 'ignore')
            options.append((link.name, link.url, link.urlNeedsResolve))
        
        #There is no free links for current video
        numOfLinks = len(links)
        if 0 == numOfLinks:
            self.session.open(MessageBox, _("No valid links available."), type=MessageBox.TYPE_INFO, timeout=10 )
            return
        elif 1 == numOfLinks:
            #call manualy selectLinksCallback - start VIDEO without links selection
            arg = []
            arg.append(" ") #name of item - not displayed so empty
            arg.append(links[0].url) #url to VIDEO
            arg.append(links[0].urlNeedsResolve) # if 1 this links should be resolved
            self.selectLinksCallback(arg)
            return

        #options.sort(reverse=True)
        self.session.openWithCallback(self.selectLinksCallback, ChoiceBox, title=_("Select link"), list = options)

        
    def selectLinksCallback(self, retArg):
        # retArg[0] - name
        # retArg[1] - url src
        # retArg[2] - urlNeedsResolve
        if retArg and 3 == len(retArg):
            #check if we have URL
            if isinstance(retArg[1], basestring):
                videoUrl = retArg[1]
                if len(videoUrl) > 3:
                    #check if we need to resolve this URL
                    if str(retArg[2]) == '1':
                        #call resolve link from host
                        self.requestListFromHost('ResolveURL', -1, videoUrl)
                    else:
                        list = []
                        list.append(videoUrl)
                        self.playVideo(RetHost(status = RetHost.OK, value = list))
                    return
            self.playVideo(RetHost(status = RetHost.ERROR, value = []))
    # end selectLinksCallback(self, retArg):
        
    def checkBuffering(self, url):
        # check flag forcing of the using/not using buffering
        if 'iptv_buffering' in url.meta:
            if "required" == url.meta['iptv_buffering']:
                # iptv_buffering was set as required, this is done probably due to 
                # extra http headers needs, at now extgstplayer and exteplayer can handle this headers,
                # so we skip forcing buffering for such links. at now this is temporary 
                # solution we need to add separate filed iptv_extraheaders_need!
                return True
            elif "forbidden" == url.meta['iptv_buffering']:
                return False
        if "|" in url:
            return True
        
        # check based on protocol
        protocol = url.meta.get('iptv_proto', '')
        protocol = url.meta.get('iptv_proto', '')
        if protocol in ['f4m', 'uds']:
            return True # supported only in buffering mode
        elif protocol in ['http', 'https']:
            return config.plugins.iptvplayer.buforowanie.value
        elif 'rtmp' == protocol:
            return config.plugins.iptvplayer.buforowanie_rtmp.value
        elif 'm3u8' == protocol:
            return config.plugins.iptvplayer.buforowanie_m3u8.value
        
    def isUrlBlocked(self, url):
        protocol = url.meta.get('iptv_proto', '')
        if ".wmv" == self.getFileExt(url) and config.plugins.iptvplayer.ZablokujWMV.value :
            return True, _("Format 'wmv' blocked in configuration.")
        elif '' == protocol:
            return True, _("Unknown protocol [%s]") % url
        return False, ''
        
    def getFileExt(self, url):
        format = url.meta.get('iptv_format', '')
        if '' != format: return '.' + format
        protocol = url.meta.get('iptv_proto', '')
        if url.endswith(".wmv"): fileExtension   = '.wmv'
        elif url.endswith(".mp4"): fileExtension = '.mp4'
        elif url.endswith(".flv"): fileExtension = '.flv'
        elif protocol in ['mms', 'mmsh', 'rtsp']: fileExtension = '.wmv'
        elif protocol in ['f4m', 'uds', 'rtmp']: fileExtension = '.flv'
        else: fileExtension = '.mp4' # default fileExtension
        return fileExtension
        
    def getMoviePlayer(self, buffering=False, useAlternativePlayer=False):
        printDBG("getMoviePlayer")
        return GetMoviePlayer(buffering, useAlternativePlayer)

    def playVideo(self, ret):
        printDBG( "playVideo" )
        url = ''
        if RetHost.OK == ret.status:
            if len(ret.value) > 0:
                url = ret.value[0]
        
        self["statustext"].setText("")            
        self["list"].show()
        
        if url != '' and self.currItem.type in [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO]:
            printDBG( "playVideo url[%s]" % url)
            url = urlparser.decorateUrl(url)
            titleOfMovie = self.currItem.name.replace('/','-').replace(':','-').replace('*','-').replace('?','-').replace('"','-').replace('<','-').replace('>','-').replace('|','-')
            fileExtension = self.getFileExt(url)            
                        
            blocked, reaseon = self.isUrlBlocked(url)
            if blocked:
                self.session.open(MessageBox, reaseon, type = MessageBox.TYPE_INFO, timeout = 10)
                return

            isBufferingMode = self.activePlayer.get('buffering', self.checkBuffering(url))
            if not self.recorderMode:
                pathForRecordings = config.plugins.iptvplayer.bufferingPath.value
            else:
                pathForRecordings = config.plugins.iptvplayer.NaszaSciezka.value
            fullFilePath = pathForRecordings + '/' + titleOfMovie + fileExtension
             
            if (self.recorderMode or isBufferingMode) and not FreeSpace(pathForRecordings, 500):
                self.session.open(MessageBox, _("There is no free space on the drive [%s].") % pathForRecordings, type=MessageBox.TYPE_INFO, timeout=10)
            elif self.recorderMode:
                global gDownloadManager
                if None != gDownloadManager:
                    if IsUrlDownloadable(url):
                        ret = gDownloadManager.addToDQueue( DMItem(url, fullFilePath) )
                    else:
                        ret = False
                        self.session.open(MessageBox, _("File can not be downloaded. Protocol [%s] is unsupported") % url.meta.get('iptv_proto', ''), type=MessageBox.TYPE_INFO, timeout=10)
                    if ret:
                        if config.plugins.iptvplayer.IPTVDMShowAfterAdd.value:
                            self.runIPTVDM()
                        else:
                            self.session.open(MessageBox, _("File [%s] was added to downloading queue.") % titleOfMovie, type=MessageBox.TYPE_INFO, timeout=10)
            elif isBufferingMode:
                self.session.nav.stopService()
                self.session.openWithCallback(self.leaveMoviePlayer, freeIPTVBufferingWidget, url, pathForRecordings, titleOfMovie, 'standard', self.bufferSize)
            else:
                self.session.nav.stopService()
                self.session.openWithCallback(self.leaveMoviePlayer, AdvancedFreePlayerStarter, url, self.currItem.name)
        else:
            #There was problem in resolving direct link for video
            self.session.open(MessageBox, _("No valid links available."), type=MessageBox.TYPE_INFO, timeout=10)
    #end playVideo(self, ret):
        
    def leaveMoviePlayer(self, answer = None, lastPosition = None, *args, **kwargs):
        self.session.nav.playService(self.currentService)
    
    def requestListFromHost(self, type, currSelIndex = -1, videoUrl = ''):
        
        if not self.isInWorkThread():
            self["list"].hide()
            
            if type not in ['ForVideoLinks', 'ResolveURL', 'ForArticleContent', 'ForFavItem']:
                #hide bottom panel
                self["cover"].hide()
                self["console"].setText('')
                
            if type == 'ForItem' or type == 'ForSearch':
                self.prevSelList.append(self.currSelIndex)
                if type == 'ForSearch':
                    self.categoryList.append('Search results')
                else:
                    self.categoryList.append(self.currItem.name) 
                #new list, so select first index
                self.nextSelIndex = 0
            
            selItem = None
            if currSelIndex > -1 and len(self.currList) > currSelIndex:
                selItem = self.currList[currSelIndex]
            
            dots = ""#_("...............")
            IDS_DOWNLOADING = _("Downloading") + dots
            IDS_LOADING     = _("Loading") + dots
            IDS_REFRESHING  = _("Refreshing") + dots
            try:
                if type == 'Refresh':
                    self["statustext"].setText(IDS_REFRESHING)
                    self.workThread = asynccall.AsyncMethod(self.host.getCurrentList, boundFunction(self.callbackGetList, {'refresh':1, 'selIndex':currSelIndex}), True)(1)
                elif type == 'ForMore':
                    self["statustext"].setText(IDS_DOWNLOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getMoreForItem, boundFunction(self.callbackGetList, {'refresh':2, 'selIndex':currSelIndex}), True)(currSelIndex)
                elif type == 'Initial':
                    self["statustext"].setText(IDS_DOWNLOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getInitList, boundFunction(self.callbackGetList, {}), True)()
                elif type == 'Previous':
                    self["statustext"].setText(IDS_DOWNLOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getPrevList, boundFunction(self.callbackGetList, {}), True)()
                elif type == 'ForItem':
                    self["statustext"].setText(IDS_DOWNLOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getListForItem, boundFunction(self.callbackGetList, {}), True)(currSelIndex, 0, selItem)
                elif type == 'ForVideoLinks':
                    self["statustext"].setText(IDS_LOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getLinksForVideo, self.selectHostVideoLinksCallback, True)(currSelIndex, selItem)
                elif type == 'ResolveURL':
                    self["statustext"].setText(IDS_LOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getResolvedURL, self.getResolvedURLCallback, True)(videoUrl)
                elif type == 'ForSearch':
                    self["statustext"].setText(IDS_LOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getSearchResults, boundFunction(self.callbackGetList, {}), True)(self.searchPattern, self.searchType)
                else:
                    printDBG( 'requestListFromHost unknown list type: ' + type )
                self.showSpinner()
            except:
                printExc('The current host crashed')
    #end requestListFromHost(self, type, currSelIndex = -1, videoUrl = ''):
        
    def startSearchProcedure(self, searchTypes):
        sts, prevPattern = CSearchHistoryHelper.loadLastPattern()
        if sts: self.searchPattern = prevPattern
        if searchTypes:
            self.session.openWithCallback(self.selectSearchTypeCallback, ChoiceBox, title=_("Search type"), list = searchTypes)
        else:
            self.searchType = None
            self.session.openWithCallback(self.enterPatternCallBack, VirtualKeyBoard, title=(_("Your search entry")), text = self.searchPattern)
    
    def selectSearchTypeCallback(self, ret = None):
        if ret:
            self.searchType = ret[1]
            self.session.openWithCallback(self.enterPatternCallBack, VirtualKeyBoard, title=(_("Your search entry")), text = self.searchPattern)
        else:
            pass
            # zrezygnowal z wyszukiwania

    def enterPatternCallBack(self, callback = None):
        if callback is not None and len(callback):  
            self.searchPattern = callback
            CSearchHistoryHelper.saveLastPattern(self.searchPattern)
            self.requestListFromHost('ForSearch')
        else:
            pass
            # zrezygnowal z wyszukiwania

    def configCallback(self):
        pass

    def reloadList(self, params):
        printDBG( "reloadList" )
        refresh  = params['add_param'].get('refresh', 0)
        selIndex = params['add_param'].get('selIndex', 0)
        ret      = params['ret']
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> IPTVPlayerWidget.reloadList refresh[%s], selIndex[%s]" % (refresh, selIndex))
        if 0 < refresh and 0 < selIndex:
            self.nextSelIndex = selIndex
        # ToDo: check ret.status if not OK do something :P
        if ret.status != RetHost.OK:
            printDBG( "++++++++++++++++++++++ reloadList ret.status = %s" % ret.status )

        self.currList = ret.value
        self["list"].setList([ (x,) for x in self.currList])
        
        ####################################################
        #                   iconMenager
        ####################################################
        iconList = []
        # fill icon List for icon manager 
        # if an user whant to see icons
        if config.plugins.iptvplayer.showcover.value and self.iconMenager:
            for it in self.currList:
                if it.iconimage != '':
                    iconList.append(it.iconimage)
        
        if len(iconList):
            # List has been changed so clear old Queue
            self.iconMenager.clearDQueue()
            # a new list of icons should be downloaded
            self.iconMenager.addToDQueue(iconList)
        #####################################################
        
        self["headertext"].setText(self.getCategoryPath())
        if len(self.currList) <= 0:
            disMessage = _("No item to display. \nPress OK to refresh.\n")
            if ret.message and ret.message != '':
                disMessage += ret.message
            self["statustext"].setText(disMessage)
            self["list"].hide()
        else:
            #restor previus selection
            if len(self.currList) > self.nextSelIndex:
                self["list"].moveToIndex(self.nextSelIndex)
            #else:
            #selection will not be change so manualy call
            self.changeBottomPanel()
            
            self["statustext"].setText("")            
            self["list"].show()
    #end reloadList(self, ret):
    
    def getCategoryPath(self):
        def _getCat(cat, num):
            if '' == cat: return ''
            cat = ' > ' + cat
            if 1 < num: cat += (' (x%d)' % num)
            return cat

        str = self.hostName
        prevCat = ''
        prevNum = 0
        for cat in self.categoryList:
            if prevCat != cat:
                str += _getCat(prevCat, prevNum) 
                prevCat = cat
                prevNum = 1
            else: prevNum += 1
        str += _getCat(prevCat, prevNum) 
        return str

    def getRefreshedCurrList(self):
        currSelIndex = self["list"].getCurrentIndex()
        self.requestListFromHost('Refresh', currSelIndex)

    def getInitialList(self):
        self.nexSelIndex = 0
        self.prevSelList = []
        self.categoryList = []
        self.currList = []
        self.currItem = CDisplayListItem()
        self["headertext"].setText(self.getCategoryPath())
        self.requestListFromHost('Initial')

    def hideWindow(self):
        self.visible = False
        self.hide()

    def showWindow(self):
        self.visible = True
        self.show()

    def createSummary(self):
        return freeIPTVLCDScreen
        
    def canByAddedToFavourites(self):
        try: favouritesHostActive = config.plugins.iptvplayer.hostfavourites.value
        except: favouritesHostActive = False
        cItem = None
        index = -1
        # we need to check if fav is available
        if favouritesHostActive and len(self.hostFavTypes) and self.visible and \
           None != self.getSelectedItem() and \
           self.getSelItem().type in self.hostFavTypes:
            cItem = self.getSelItem()
            index = self.getSelIndex()
        return index, cItem
        
#class IPTVPlayerWidget

class freeIPTVLCDScreen(Screen):
    skin = """
    <screen position="0,0" size="132,64" title="freeIPTV">
        <widget name="text1" position="4,0" size="132,14" font="Regular;12" halign="center" valign="center"/>
         <widget name="text2" position="4,14" size="132,49" font="Regular;10" halign="center" valign="center"/>
    </screen>"""

    def __init__(self, session, parent):
        Screen.__init__(self, session)
        self["text1"] =  Label("freeIPTV")
        self["text2"] = Label("")

    def setText(self, text):
        self["text2"].setText(text[0:39])

