from Plugins.Plugin import PluginDescriptor
import FreePlayer

def main(session, **kwargs):
	reload(FreePlayer)
	session.open(FreePlayer.FreePlayerStart)

def menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("FreePlayer"), main, "FreePlayer", 45)]
	return []

def Plugins(**kwargs):
	return [PluginDescriptor(name = "FreePlayer", description = "Play divx/xvid media files", where = PluginDescriptor.WHERE_MENU, fnc = menu)]

