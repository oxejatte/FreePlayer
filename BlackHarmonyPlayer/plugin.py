from Plugins.Plugin import PluginDescriptor
import BlackHarmonyPlayer

def main(session, **kwargs):
	reload(BlackHarmonyPlayer)
	session.open(BlackHarmonyPlayer.BlackHarmonyPlayerStart)

def Plugins(path, **kwargs):
	global plugin_path
	plugin_path = path
	return PluginDescriptor(
		name=_("BlackHarmonyPlayer"),
		description=_("Based on FreePlayer"),
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		icon = "BlackHarmonyPlayer.png", fnc = main)

