#!/bin/bash
# Run this script using sudo
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# set working directory
DIRECTORY='/opt/odl'
if [ ! -d "$DIRECTORY" ]; then
  mkdir -p ${DIRECTORY}
fi
cd ${DIRECTORY}

touch /var/log/sdnserverinstall.log

echo "Installing Java 7 JDK and other components..." >> /var/log/sdnserverinstall.log
apt-get -y update
apt-get install -y openjdk-7-jdk 
# installing openvswitch
apt-get install -y openvswitch-switch

# download opendaylight
echo "Downloading opendaylight executable..." >> /var/log/sdnserverinstall.log
wget https://nexus.opendaylight.org/content/repositories/opendaylight.release/org/opendaylight/integration/distribution-karaf/0.3.2-Lithium-SR2/distribution-karaf-0.3.2-Lithium-SR2.zip
unzip distribution-karaf-0.3.2-Lithium-SR2.zip

cd distribution-karaf-0.3.2-Lithium-SR2
echo 'export JAVA_HOME="/usr/lib/jvm/java-7-openjdk-amd64"' >> ./bin/setenv
source ./bin/setenv
# start karaf server
echo "Starting karaf server..." >> /var/log/sdnserverinstall.log
./bin/karaf server & 

# install features
echo "Installing karaf features..." >> /var/log/sdnserverinstall.log
sleep 10 &&
./bin/client -u karaf feature:install odl-dlux-all odl-l2switch-packethandler odl-l2switch-loopremover odl-l2switch-arphandler odl-l2switch-switch-ui odl-restconf-all odl-l2switch-addresstracker odl-l2switch-switch-rest odl-l2switch-switch odl-mdsal-all odl-openflowjava-all odl-mdsal-apidocs odl-openflowplugin-all odl-ovsdb-all &&
echo "Karaf features installed successfully and ready to run!" >> /var/log/sdnserverinstall.log