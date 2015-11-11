#### from ..inits import *

PluginInfo='@j00zek 10/11/2015'

##### permanents
PluginName = 'freeIPTV'
PluginGroup = 'Extensions'

##### System Imports
from os import path as os_path, environ as os_environ, listdir as os_listdir, chmod as os_chmod, remove as os_remove, mkdir as os_mkdir
import traceback

###### openPLI imports
from Tools.Directories import *
from Components.config import *
config.plugins.iptvplayer = ConfigSubsection()
myConfig=config.plugins.iptvplayer

###### Plugin imports
import ConfigOptions

# Plugin Paths
PluginFolder = PluginName
PluginPath = resolveFilename(SCOPE_PLUGINS, '%s/%s/' %(PluginGroup,PluginFolder))
ExtPluginsPath = resolveFilename(SCOPE_PLUGINS, '%s/' %(PluginGroup))

##################################################### DEBUGING #####################################################
myDEBUG=True
myDEBUGfile = '/tmp/%s.log' % PluginName

append2file=False

def printDEBUG( myText , myFUNC = ''):
    if myFUNC != '':
        myFUNC = ':' + myFUNC
    global append2file
    if myDEBUG:
        print ("[%s%s] %s" % (PluginName,myFUNC,myText))
        try:
            if append2file == False:
                append2file = True
                f = open(myDEBUGfile, 'w')
            else:
                f = open(myDEBUGfile, 'a')
            f.write('[%s%s] %s\n' %(PluginName,myFUNC,myText))
            f.close
        except:
            pass

printDBG=printDEBUG

def printExc(msg=''):
    printDBG("=================== EXCEPTION >>>")
    msg = msg + ': \n%s' % traceback.format_exc()
    printDBG(msg)
    printDBG("<<< EXCEPTION ===================")

##################################################### TRANSLATION #####################################################
try:
    from Components.LanguageGOS import gosgettext as _
    #printDEBUG("LanguageGOS detected")
except:
    #printDEBUG("LanguageGOS not detected")
    PluginLanguageDomain = "plugin-" + PluginName
    PluginLanguagePath = '%s/locale' % PluginPath
    from Components.Language import language
    import gettext
    
    def localeInit():
        lang = language.getLanguage()[:2]
        os_environ["LANGUAGE"] = lang
        gettext.bindtextdomain(PluginLanguageDomain, PluginLanguagePath)

    def _(txt):
        t = gettext.dgettext(PluginLanguageDomain, txt)
        if t == txt:
                t = gettext.gettext(txt)
                print "Lack of translation for '%s'" % t
        return t

    localeInit()
    language.addCallback(localeInit)

##################################################### LOAD SKIN DEFINITION #####################################################
def LoadSkin(SkinName):
    from enigma import getDesktop
    
    if SkinName.endswith('.xml'):
        SkinName=SkinName[:-4]
    skinDef=None
    
    if getDesktop(0).size().width() == 1920:
        SkinName +='FHD'
        
    if os_path.exists("%sskins/%s.xml" % (PluginPath,SkinName)):
        with open("%sskins/%s.xml" % (PluginPath,SkinName),'r') as skinfile:
            skinDef=skinfile.read()
            skinfile.close()
    return skinDef

##################################################### CREATE LIST of HOSTS #####################################################
def GetHostsList():
    printDBG('getHostsList begin')
    lhosts = [] 
    
    try:
        fileList = os_listdir( PluginPath + 'hosts/' )
        for wholeFileName in fileList:
            # separate file name and file extension
            fileName, fileExt = os_path.splitext(wholeFileName)
            nameLen = len( fileName )
            if fileExt in ['.pyo', '.pyc', '.py'] and nameLen >  4 and fileName.find('_blocked_') == -1 and not fileName.startswith('_') and not fileName.startswith('-'):
                #if fileName.startswith('host'):
                #    fileName = fileName[4:]
                
                if fileName not in lhosts:
                    lhosts.append( fileName )
                    #printDBG('getHostsList add host with fileName: "%s"' % fileName)
        #printDBG('getHostsList end')
        lhosts.sort()
    except:
        printDBG('GetHostsList EXCEPTION')
    return lhosts

GotHostsList = GetHostsList() # load hosts only during start, other scripts uses GotHostsList to speedup.

##################################################### CLEAR CACHE - tuners with small amount of memory need it #####################################################
def ClearMemory(): #avoid GS running os.* (e.g. os.system) on tuners with small amount of RAM
    with open("/proc/sys/vm/drop_caches", "w") as f: f.write("1\n")
    
