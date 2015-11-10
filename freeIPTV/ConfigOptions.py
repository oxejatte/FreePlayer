from Components.config import *
from os import path
from inits import myConfig

def getPlatform():
    fc=''
    with open('/proc/cpuinfo', 'r') as f:
        fc=f.read()
        f.close()
    if fc.find('sh4') > -1:
        return 'sh4'
    elif fc.find('BMIPS') > -1:
        return 'mipsel'
    elif fc.find('GenuineIntel') > -1:
        return 'i686'
    else:
       return 'unknown'
###################################################
# Required packages
#opkg install rtmpdump
#opkg install wget

###################################################
# Config options
###################################################
if path.exists('/usr/bin/wget') and not path.islink('/usr/bin/wget'):
    myConfig.wgetpath      = ConfigText(default = '/usr/bin/wget', fixed_size = False)
else:
    myConfig.wgetpath      = ConfigText(default = '', fixed_size = False)
    printDBG('No full version of wget found. :( Try to install it running opkg install wget')

if path.exists('/usr/bin/rtmpdump') and not path.islink('/usr/bin/rtmpdump'):
    myConfig.rtmpdumppath  = ConfigText(default = '/usr/bin/rtmpdump', fixed_size = False)
else:
    myConfig.rtmpdumppath  = ConfigText(default = '', fixed_size = False)
    printDBG('No full version of rtmpdump found. :( Try to install it running opkg install rtmpdump')

myConfig.f4mdumppath   = ConfigText(default = '', fixed_size = False)

myConfig.plarform      = ConfigSelection(default = getPlatform(), choices = [("mipsel", _("mipsel")),("sh4", _("sh4")),("i686", _("i686")),("unknown", _("unknown"))])

myConfig.showcover          = ConfigYesNo(default = True)
myConfig.deleteIcons        = ConfigSelection(default = "3", choices = [("0", _("after closing")),("1", _("after day")),("3", _("after three days")),("7", _("after a week"))]) 
myConfig.showinextensions   = ConfigYesNo(default = True)
myConfig.showinMainMenu     = ConfigYesNo(default = False)
myConfig.NaszaSciezka       = ConfigDirectory(default = "/hdd/movie/") #, fixed_size = False)
myConfig.bufferingPath      = ConfigDirectory(default = myConfig.NaszaSciezka.value) #, fixed_size = False)
myConfig.buforowanie        = ConfigYesNo(default = False)
myConfig.buforowanie_m3u8   = ConfigYesNo(default = True)
myConfig.buforowanie_rtmp   = ConfigYesNo(default = False)
myConfig.requestedBuffSize  = ConfigInteger(5, (1,120))

myConfig.IPTVDMRunAtStart      = ConfigYesNo(default = False)
myConfig.IPTVDMShowAfterAdd    = ConfigYesNo(default = True)
myConfig.IPTVDMMaxDownloadItem = ConfigSelection(default = "1", choices = [("1", "1"),("2", "2"),("3", "3"),("4", "4")])

myConfig.sortuj = ConfigYesNo(default = True)
myConfig.devHelper = ConfigYesNo(default = False)

myConfig.SciezkaCache = ConfigDirectory(default = "/hdd/IPTVCache/") #, fixed_size = False)
myConfig.NaszaTMP = ConfigDirectory(default = "/tmp/") #, fixed_size = False)
myConfig.ZablokujWMV = ConfigYesNo(default = True)

myConfig.hd3d_login    = ConfigText(default="", fixed_size = False)
myConfig.hd3d_password = ConfigText(default="", fixed_size = False)

myConfig.debugprint = ConfigSelection(default = "", choices = [("", _("no")),("console", _("yes, to console")),("debugfile", _("yes, to file /hdd/iptv.dbg"))]) 

myConfig.httpssslcertvalidation = ConfigYesNo(default = True)

#PROXY
myConfig.proxyurl = ConfigText(default = "http://PROXY_IP:PORT", fixed_size = False)
myConfig.german_proxyurl = ConfigText(default = "http://PROXY_IP:PORT", fixed_size = False)

# Hosts lists to enable hosts config screen
myConfig.fakeHostsList = ConfigSelection(default = "fake", choices = [("fake", "  ")])
