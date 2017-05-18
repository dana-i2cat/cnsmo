#!/bin/bash
# Run this script using sudo
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit 126
fi

function check_error {
  if [ $? -ne "0" ] ;
    then echo -e "\e[31mError!\033[0m"
    exit 126
  fi
}

function check_preconditions {
  # Checking if ovs is installed
  which ovs-vsctl > /dev/null 2>&1
  if [ $? -ne "0" ] ;
    then echo -e "\e[31mOpenvSwitch not installed!\033[0m"
    exit 127
  fi

  # Checking if the ovs bridge is created, if created exit
  S=$(ifconfig | grep br-ext > /dev/null 2>&1 )
  if [[ $S == *"br-ext"* ]] ;
    then echo -e "\e[31mBridge br-ext already created!\033[0m"
    exit 127
  fi

  # Checking if host is connected to a bridged VPN, otherwise exit
  S=$(ifconfig | grep tap  > /dev/null 2>&1)
  if [[ $S == *"tap"* ]] ;
    then echo -e "\e[31mMachine not connected to a bridged VPN. \033[0m"
    exit 127
  fi
}

function configure_ovs {
  # Configuration values
  NIC="eth0"
  SDN_CTRL_IP="10.8.44.55:6633"
  PROTO_SDN="tcp"
  IP=$(ip addr show $NIC | grep "inet\b" | awk '{print $2}' | cut -d/ -f1)
  GW=$(ip route | grep default | awk '{print $3}')
  MAC=$(ifconfig $NIC | grep "HWaddr\b" | awk '{print $5}')
  MASK=$(ip addr show $NIC | grep "inet\b" | awk '{print $2}' | cut -d/ -f2)

  echo -ne "Creating an OpenvSwitch bridge to the physical interface...\t\t"
  ovs-vsctl add-br br-ext -- set bridge br-ext other-config:hwaddr=$MAC > /dev/null 2>&1
  check_error
  ovs-vsctl set bridge br-ext protocols=OpenFlow10,OpenFlow12,OpenFlow13
  check_error
  echo "Done!"

  echo -ne "Adding the physical interface to the ovs bridge...\t\t\t"
  ovs-vsctl add-port br-ext $NIC > /dev/null 2>&1
  check_error
  echo "Done!"

  echo -ne "Adding the VPN interface to the ovs bridge...\t\t\t\t"
  ovs-vsctl add-port br-ext tap0 > /dev/null 2>&1
  check_error
  echo "Done!"

  echo -ne "Removing IP address from the physical interface...\t\t\t"
  ifconfig $NIC 0.0.0.0 > /dev/null 2>&1
  check_error
  echo "Done!"

  echo -ne "Giving the ovs bridge the host IP address...\t\t\t\t"
  ifconfig br-ext $IP/$MASK > /dev/null 2>&1
  check_error
  echo "Done!"

  echo -ne "Changing the interface MAC address...\t\t\t\t\t"
  LAST_MAC_CHAR=${MAC:(-1)}
  AUX="${MAC:0:${#MAC}-1}"
  if [ "$LAST_MAC_CHAR" -eq "$LAST_MAC_CHAR" ] 2>/dev/null; then
    NL="a"
  else
    NL="1"
  fi
  NEW_MAC="$AUX$NL"
  ifconfig $NIC down
  check_error
  ifconfig $NIC hw ether $NEW_MAC
  check_error
  ifconfig $NIC up
  check_error
  echo "Done!"

  echo -ne "Routing traffic through the new bridge...\t\t\t\t"
  while $(ip route del default > /dev/null 2>&1); do :; done
  ip route add default via $GW dev br-ext
  check_error
  echo "Done!"

  echo -ne "Connecting OVS brige to controller...\t\t\t\t\t"
  ovs-vsctl set-controller br-ext $PROTO_SDN:$SDN_CTRL_IP > /dev/null 2>&1
  check_error
  echo "Done!"

  echo -ne "Updating problematic OpenFlow rules if any...\t\t\t\t"
  sleep 5
  ovs-ofctl mod-flows br-ext "actions:output=1" > /dev/null 2>&1
  ovs-ofctl mod-flows br-ext "in_port=1, actions:output=LOCAL" > /dev/null 2>&1
  echo "Done!"
}

check_preconditions
configure_ovs