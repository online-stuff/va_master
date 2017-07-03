#!/bin/bash
set -e
IMAGE=$(lxc image list|grep -i va-master| cut -d '|' -f 3)
PROFILE=default
CONTAINER=$1
BRANCH=$2
INIT_OPTS="${@:3}"
ZONE="va.mk"
LXD="knet-1"
BIND_SERVER="192.168.50.10"
lxc launch $IMAGE $CONTAINER -p $PROFILE
lxc exec $CONTAINER -- bash -c "sleep 5 && cd /opt/va_master; git pull && git checkout $BRANCH"
lxc exec $CONTAINER -- bash -c "cd /opt/va_master; python -m va_master init $INIT_OPTS"
lxc exec $CONTAINER -- salt-call --local state.apply openvpn.config
lxc exec $CONTAINER -- bash -c "cd /opt/va_master/va_dashboard; npm install --no-bin-links && node build.js"
IPADDRESS=$(lxc list|grep $CONTAINER |grep -o -E "[0-9]*[.][0-9]*[.][0-9]*[.][0-9]*")
sed -e s/CONTAINER/$CONTAINER/g -e s/IPADDRESS/$IPADDRESS/g -e s/ZONE/$ZONE/g ~/.lva/nginx.conf > /etc/nginx/sites-available/"$CONTAINER".master.$ZONE
ln -s /etc/nginx/sites-available/"$CONTAINER".master.$ZONE /etc/nginx/sites-enabled/
systemctl reload nginx
sed -e "s/BINDIP/$BIND_SERVER/g" -e "s/ZONE/$ZONE/g" -e "s/LXD/$LXD.master/g" -e "s/CONTAINER/$CONTAINER.master/g" ~/.lva/bind-update > $CONTAINER.master.$ZONE.txt
nsupdate $CONTAINER.$ZONE.txt
