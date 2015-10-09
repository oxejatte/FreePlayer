from . import PluginName, PluginInfo
from Plugins.Plugin import PluginDescriptor
import AdvancedFreePlayer

def main(session, **kwargs):
    reload(AdvancedFreePlayer)
    session.open(AdvancedFreePlayer.AdvancedFreePlayerStart)

def Plugins(path, **kwargs):
    return PluginDescriptor( name=PluginName, description=PluginInfo,
    where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
    icon = "AdvancedFreePlayer.png", fnc = main)

