# -*- coding: utf-8 -*-
PluginInfo='@j00zek 28/11/2015'

#permanent
PluginName = 'AdvancedFreePlayer'
PluginGroup = 'Extensions'

#Plugin Paths
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, SCOPE_PLUGINS
PluginFolder = PluginName
PluginPath = resolveFilename(SCOPE_PLUGINS, '%s/%s/' %(PluginGroup,PluginFolder))
ExtPluginsPath = resolveFilename(SCOPE_PLUGINS, '%s/' %(PluginGroup))

#Current skin
from Components.config import *
SkinPath = resolveFilename(SCOPE_CURRENT_SKIN, '')
if not SkinPath.endswith('/'):
    SkinPath = SkinPath + '/'
CurrentSkinName=config.skin.primary_skin.value.replace('skin.xml', '').replace('/', '')

#translation
PluginLanguageDomain = "plugin-" + PluginName
PluginLanguagePath = resolveFilename(SCOPE_PLUGINS, '%s/%s/locale' % (PluginGroup,PluginFolder))

#DEBUG
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

def ClearMemory(): #avoid GS running os.* (e.g. os.system) on tuners with small RAM
    with open("/proc/sys/vm/drop_caches", "w") as f: f.write("1\n")
    
##################################################### LOAD SKIN DEFINITION #####################################################
def LoadSkin(SkinName):
    printDEBUG("LoadSkin >>> %s" % SkinName)
    from enigma import getDesktop
    model=''
    if os_path.exists("/proc/stb/info/vumodel"):
        with open("/proc/stb/info/vumodel", "r") as f:
            model=f.read().strip()
            f.close()
    
    if SkinName.endswith('.xml'):
        SkinName=SkinName[:-4]
    skinDef=None
    
    if getDesktop(0).size().width() == 1920 and os_path.exists("%sskins/%s%sFHD.xml" % (PluginPath,SkinName,model)):
        with open("%sskins/%s%sFHD.xml" % (PluginPath,SkinName,model),'r') as skinfile:
            skinDef=skinfile.read()
            skinfile.close()
    elif getDesktop(0).size().width() == 1920 and os_path.exists("%sskins/%sFHD.xml" % (PluginPath,SkinName)):
        with open("%sskins/%sFHD.xml" % (PluginPath,SkinName),'r') as skinfile:
            skinDef=skinfile.read()
            skinfile.close()
            
    elif os_path.exists("%sskins/%s%s.xml" % (PluginPath,SkinName,model)):
        with open("%sskins/%s%s.xml" % (PluginPath,SkinName,model),'r') as skinfile:
            skinDef=skinfile.read()
            skinfile.close()
    elif os_path.exists("%sskins/%s.xml" % (PluginPath,SkinName)):
        with open("%sskins/%s.xml" % (PluginPath,SkinName),'r') as skinfile:
            skinDef=skinfile.read()
            skinfile.close()
    else:
        printDEBUG("%s does not exists")
    return skinDef
