#! /bin/bash
eval $(cat ~/.fehbg)

#urxvtd -q -f -o &
#xcompmgr
nm-applet &
(sleep 500 && dropboxd &)
#blueman-applet &
volumeicon &
xscreensaver -no-splash &
exec qtile



