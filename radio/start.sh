#!/bin/sh
chown mpd:audio /var/lib/mpd
mkdir /var/lib/mpd/playlists
echo -e "http://stream.srg-ssr.ch/m/drs3/mp3_128\nhttps://icecast.omroep.nl/3fm-bb-aac" > /var/lib/mpd/playlists/radio_stations.m3u
chown mpd:audio /var/lib/mpd/playlists
mpc load radio_stations
exec /usr/bin/dumb-init -- $@
