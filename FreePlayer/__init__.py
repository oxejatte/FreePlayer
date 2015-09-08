from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
import os

fonts_path_1 = "/usr/share/fonts/"
fonts_path_2 = resolveFilename(SCOPE_PLUGINS,"Extensions/FreePlayer/fonts/")

if fileExists(fonts_path_1):
	fonts_path = fonts_path_1
else:	
	fonts_path = fonts_path_2

file_name = resolveFilename(SCOPE_PLUGINS,"Extensions/FreePlayer/font.ini")

f = open(file_name,'w')

for file in os.listdir(fonts_path):
    if file.endswith(".ttf") or file.endswith(".TTF"):
        f.write(file+'\n')

f.close()