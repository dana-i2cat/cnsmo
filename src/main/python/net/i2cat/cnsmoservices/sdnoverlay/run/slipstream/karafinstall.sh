DIRECTORY='/opt/odl/distribution-karaf-0.3.2-Lithium-SR2'
cd ${DIRECTORY}
source ./bin/setenv
# start karaf server
echo "Starting karaf server..." >> /var/log/sdnserverinstall.log
./bin/karaf server &

# install features
echo "Installing karaf features..." >> /var/log/sdnserverinstall.log
sleep 60

./bin/client -u karaf feature:install odl-restconf-all odl-mdsal-all odl-mdsal-apidocs odl-netconf-all odl-dlux-all odl-openflowjava-all odl-openflowplugin-all odl-ovsdb-all
#./bin/client -u karaf feature:install  odl-l2switch-packethandler odl-l2switch-loopremover odl-l2switch-arphandler odl-l2switch-switch-ui odl-l2switch-addresstracker odl-l2switch-switch-rest odl-l2switch-switchl
echo "Karaf features installed successfully and ready to run!" >> /var/log/sdnserverinstall.log