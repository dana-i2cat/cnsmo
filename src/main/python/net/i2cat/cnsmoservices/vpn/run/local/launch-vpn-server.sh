#!/bin/sh
# Run this script using sudo
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi
ALREADY_RUNNING=$(docker ps -a --filter "name=server-vpn" | grep server-vpn | awk '{print $1}')
if [ ! -z "$ALREADY_RUNNING" ]; then
  echo "VPN server container already running, stoping it now..."
  docker stop "$ALREADY_RUNNING"
  echo "Removing container..."
  docker rm "$ALREADY_RUNNING"
fi
docker rmi vpn-server

STARTING_DIR=$(pwd)
echo "Please, select the network interface connected to the Internet:"
cd /sys/class/net && select foo in *;
do
  NIC=$foo;
  echo $foo selected;
  break;
done
cd $STARTING_DIR

IP=$(ip addr show "$NIC" | grep "inet\b" | awk '{print $2}' | cut -d/ -f1)

echo "Running VPN services in background..."

python src/main/python/net/i2cat/cnsmo/run/systemstate.py &
python src/main/python/net/i2cat/cnsmoservices/vpn/run/orchestrator.py -r 0.0.0.0:6379 &
python src/main/python/net/i2cat/cnsmoservices/vpn/run/configurator.py -a $IP -p 9093 -r 0.0.0.0:6379 -s VPNConfigurator --vpn-server-ip $IP --vpn-server-port 1194 --vpn-address 10.10.10.0 --vpn-mask 255.255.255.0 &
python src/main/python/net/i2cat/cnsmoservices/vpn/run/server.py -a $IP -p 9092 -r $IP:6379 -s VPNServer &
