#
[ -e /tmp/AFP.tar.gz ] && rm -rf /tmp/AFP.tar.gz
rm -rf /tmp/j00zek-FreePlayer-* 2>/dev/null
sudo rm -rf /tmp/j00zek-FreePlayer-* 2>/dev/null
curl --help 1>/dev/null 2>%1
if [ $? -gt 0 ]; then
  echo "_(Required program 'curl' is not installed. Trying to install it via OPKG.)"
  echo
  opkg install curl 

  curl --help 1>/dev/null 2>%1
  if [ $? -gt 0 ]; then
    echo
    echo "_(Required program 'curl' is not available. Please install it first manually.)"
    exit 0
  fi
fi

echo "_(Checking installation mode...)"
if `opkg list-installed 2>/dev/null | tr '[:upper:]' '[:lower:]'| grep -q 'userskin'`;then
  echo "_(AdvancedFreePlayer controlled by OPKG. Please use it for updates.)"
  exit 0
fi

echo "_(Checking internet connection...)"
ping -c 1 github.com 1>/dev/null 2>%1
if [ $? -gt 0 ]; then
  echo "_(github server unavailable, update impossible!!!)"
  exit 0
fi

echo "_(Downloading latest plugin version...)"
curl -kLs https://api.github.com/repos/j00zek/FreePlayer/tarball/master -o /tmp/AFP.tar.gz
if [ $? -gt 0 ]; then
  echo "_(Archive downloaded improperly"
  exit 0
fi

if [ ! -e /tmp/AFP.tar.gz ]; then
  echo "_(No archive downloaded, check your curl version)"
  exit 0
fi

echo "_(Unpacking new version...)"
#cd /tmp
tar -zxf /tmp/AFP.tar.gz -C /tmp
if [ $? -gt 0 ]; then
  echo "_(Archive unpacked improperly)"
  exit 0
fi

if [ ! -e /tmp/j00zek-FreePlayer-* ]; then
  echo "Archive downloaded improperly)"
  exit 0
fi
rm -rf /tmp/AFP.tar.gz

version=`ls /tmp/ | grep j00zek-FreePlayer-`
if [ -f /usr/lib/enigma2/python/Plugins/Extensions/UserSkin/$version ];then
  echo "_(Latest version already installed)"
  exit 0
fi

echo "_(Installing new version...)"
if [ ! -e /DuckboxDisk ]; then
  rm -rf /usr/lib/enigma2/python/Plugins/Extensions/UserSkin/j00zek-UserSkin-* 2>/dev/null
  touch /tmp/$version/UserSkin/$version 2>/dev/null
  cp -a /tmp/$version/UserSkin/* /usr/lib/enigma2/python/Plugins/Extensions/UserSkin/
else
  echo
  echo "_(github is always up-2-date)"
fi

if [ $? -gt 0 ]; then
  echo
  echo "_(Installation incorrect!!!)"
else
  echo
  echo "_(Success: Restart system to use new plugin version)"
fi

exit 0
