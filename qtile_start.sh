#! /bin/bash

#urxvtd -q -f -o &
#xcompmgr
nm-applet &
eval $(cat ~/.fehbg)
(sleep 500 && dropbox &)
#blueman-applet &
volumeicon &
xscreensaver -no-splash &
exec qtile



