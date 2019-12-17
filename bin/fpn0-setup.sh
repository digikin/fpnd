#!/bin/bash
# fpn0-setup.sh v0.0
#   Configures outgoing FPN browsing interface/rules on target node
#
# PREREQS:
#   1. zt/iptables/iproute2 plus assoc. kernel modules installed on target node
#   2. network controller has available network with one "exit" node
#   3. target node has been joined and authorized on the above network
#   4. target node has ``zt`` net device with address on the above network
#   5. target node and "exit" node can ping each other on the above network
#
# NOTE you may provide the ZT network ID as the only argument if
#      it does not automatically select the correct FPN0 network ID


#set -x

failures=0
trap 'failures=$((failures+1))' ERR

DATE=$(date +%Y%m%d)
# very simple log capture
exec &> >(tee -ia /tmp/fpn0-setup-${DATE}_output.log)
exec 2> >(tee -ia /tmp/fpn0-setup-${DATE}_error.log)

#VERBOSE="anything"

ZT_UP=$(/etc/init.d/zerotier status | grep -o started)
if [[ $ZT_UP != "started" ]]; then
    echo "FPN zerotier service is not running!!"
    echo "Please start the zerotier service and re-run this script."
    exit 1
fi

echo "Checking kernel rp_filter setting..."
RP_NEED="2"
RP_ORIG="$(sysctl net.ipv4.conf.all.rp_filter | cut -f3 -d' ')"

if [[ ${RP_NEED} = "${RP_ORIG}" ]]; then
    echo "  RP good..."
else
    echo "  RP needs garlic filter..."
    sysctl -w net.ipv4.conf.all.rp_filter=$RP_NEED
fi

while read -r line; do
    echo "Checking network..."
    LAST_OCTET=$(echo "$line" | cut -d"/" -f2 | cut -d"," -f2 | cut -d'.' -f4)
    ZT_NET_ID=$(echo "$line" | cut -d" " -f3)
    if [[ $LAST_OCTET != 1 ]]; then
        ZT_NETWORK="${ZT_NET_ID}"
        echo "  Found $ZT_NETWORK"
        break
    else
        echo "  Skipping gateway network"
    fi
done < <(zerotier-cli listnetworks | grep zt)

ZT_NETWORK=${1:-$ZT_NETWORK}

if [[ -n $ZT_NETWORK ]]; then
    echo "Using FPN0 ID: $ZT_NETWORK"
else
    echo "Please provide the network ID as argument."
fi

ZT_INTERFACE=$(zerotier-cli get "${ZT_NETWORK}" portDeviceName)
ZT_ADDRESS=$(zerotier-cli get "${ZT_NETWORK}" ip4)
ZT_GATEWAY=$(zerotier-cli -j listnetworks | grep "${ZT_INTERFACE}" -A 14 | grep via | awk '{ print $2 }' | tail -n 1 | cut -d'"' -f2)

#ZT_OUT_IFACE="fpn0"
# apparently we stop passing data if names are different on both ends :/
#if [[ -n $ZT_INTERFACE && -n $ZT_ADDRESS && -z $ZT_OUT_IFACE ]]; then
    #echo "Renaming local egress interface to fpn0..."
    #ip link set "$ZT_INTERFACE" down
    #ip link set "$ZT_INTERFACE" name "$ZT_OUT_IFACE"
    #ip link set "$ZT_OUT_IFACE" up
    #ZT_INTERFACE="$ZT_OUT_IFACE"
#fi

TABLE_NAME="fpn0-route"
TABLE_PATH="/etc/iproute2/rt_tables"
FPN_RT_TABLE=$(cat "${TABLE_PATH}" | { grep -o "${TABLE_NAME}" || test $? = 1; })

echo "Checking for FPN routing table..."
if [[ ${FPN_RT_TABLE} = "${TABLE_NAME}" ]]; then
    echo "  RT good..."
else
    echo "  Inserting routing table..."
    echo "200   ${TABLE_NAME}" >> /etc/iproute2/rt_tables
fi

echo "Checking FPN network settings..."
zerotier-cli set "${ZT_NETWORK}" allowGlobal=1 2>&1 | grep allowGlobal

IPV4_INTERFACE=$(ip -o link show up | awk -F': ' '{print $2}' | grep -e 'eth' -e 'en' -e 'wl' -e 'mlan' | head -n 1)
# set this to your "normal" network interface if needed
#IPV4_INTERFACE="eth0"
#IPV4_INTERFACE="wlan0"
[[ -n $IPV4_INTERFACE ]] || IPV4_INTERFACE="mlan0"
INET_ADDRESS=$(ip address show "${IPV4_INTERFACE}" | awk '/inet / {print $2}' | cut -d/ -f1)

if [[ -n $VERBOSE ]]; then
    echo ""
    echo "Found these devices and parameters:"
    echo "  FPN interface: ${ZT_INTERFACE}"
    echo "  FPN address: ${ZT_ADDRESS}"
    echo "  FPN gateway: ${ZT_GATEWAY}"
    echo "  FPN network id: ${ZT_NETWORK}"
    echo ""
    echo "  INET interface: ${IPV4_INTERFACE}"
    echo "  INET address: ${INET_ADDRESS}"
fi

# Populate secondary routing table
ip route add default via ${ZT_GATEWAY} dev ${ZT_INTERFACE} table "${TABLE_NAME}"

# Anything with this fwmark will use the secondary routing table
ip rule add fwmark 0x1 table "${TABLE_NAME}"
sleep 2

# Mark these packets so that ip can route web traffic through fpn0
iptables -A OUTPUT -t mangle -o ${IPV4_INTERFACE} -p tcp --dport 443 -j MARK --set-mark 1
iptables -A OUTPUT -t mangle -o ${IPV4_INTERFACE} -p tcp --dport 80 -j MARK --set-mark 1

# now rewrite the src-addr using snat
iptables -A POSTROUTING -t nat -s ${INET_ADDRESS} -o ${ZT_INTERFACE} -p tcp --dport 443 -j SNAT --to ${ZT_ADDRESS}
iptables -A POSTROUTING -t nat -s ${INET_ADDRESS} -o ${ZT_INTERFACE} -p tcp --dport 80 -j SNAT --to ${ZT_ADDRESS}

echo ""
if ((failures < 1)); then
    echo "Success"
else
    echo "$failures warnings/errors"
    exit 1
fi