# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from inits import *
###################################################

###################################################
# FOREIGN import
###################################################
from enigma import getDesktop

from Plugins.Plugin import PluginDescriptor
from Components.config import config
###################################################

####################################################
# Wywołanie wtyczki w roznych miejscach
####################################################
def Plugins(**kwargs):
    screenwidth = getDesktop(0).size().width()
    if screenwidth and screenwidth == 1920: iconFile = "icons/iptvlogohd.png"
    else: iconFile = "icons/iptvlogo.png"
    desc = _("free IPTV services browser for everyone!")
    list = [PluginDescriptor(name="freeIPTV", description=desc, where = [PluginDescriptor.WHERE_PLUGINMENU], icon=iconFile, fnc=main)] # always show in plugin menu
    list.append(PluginDescriptor(name="freeIPTV", description=desc, where = PluginDescriptor.WHERE_MENU, fnc=startIPTVfromMenu))
    if config.plugins.iptvplayer.showinextensions.value:
        list.append (PluginDescriptor(name="freeIPTV", description=desc, where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main))
    return list

####################################################
# Konfiguracja wtyczki
####################################################

#from __init__ import _

def startIPTVfromMenu(menuid, **kwargs):
    if menuid == "system":
        return [(_("Configure freeIPTV"), mainSetup, "iptv_config", None)]
    elif menuid == "mainmenu" and config.plugins.iptvplayer.showinMainMenu.value == True:
        return [("freeIPTV", main, "iptv_main", None)]
    else:
        return []
    
def mainSetup(session,**kwargs):
    from Plugins.Extensions.freeIPTV.components.iptvconfigmenu import ConfigMenu
    session.open(ConfigMenu) 
    
def main(session,**kwargs):
    from Plugins.Extensions.freeIPTV.components.freeIPTVwidget import freeIPTVwidget
    session.open(freeIPTVwidget)
    