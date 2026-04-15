#!/bin/bash

# remove comment for easier troubleshooting
#set -x

# check if minimum required Venus OS is installed | start
versionRequired="v3.54"

# import functions
source /data/apps/dbus-seelevel/functions.sh

# get current Venus OS version
versionStringToNumber "$(head -n 1 /opt/victronenergy/version)"
venusVersionNumber="$versionNumber"

# minimum required version to install the driver
versionStringToNumber "$versionRequired"

if (( $venusVersionNumber < $versionNumber )); then
    echo
    echo
    echo "Minimum required Venus OS version \"$versionRequired\" not met. Currently version \"$(head -n 1 /opt/victronenergy/version)\" is installed."
    echo
    echo "Please update via \"Remote Console/GUI -> Settings -> Firmware -> Online Update\""
    echo "OR"
    echo "by executing \"/opt/victronenergy/swupdate-scripts/check-updates.sh -update -force\""
    echo
    echo "Install the driver again after Venus OS was updated."
    echo
    echo
    exit 1
fi
# check if minimum required Venus OS is installed | end



# fix permissions
chmod +x /data/apps/dbus-seelevel/*.sh
chmod +x /data/apps/dbus-seelevel/service/run


# check if overlay-fs is active
checkOverlay dbus-seelevel "/opt/victronenergy/service-templates"


if [ -d "/opt/victronenergy/service-templates/dbus-seelevel" ]; then
    rm -rf "/opt/victronenergy/service-templates/dbus-seelevel"
fi
cp -rf "/data/apps/dbus-seelevel/service" "/opt/victronenergy/service-templates/dbus-seelevel"



# check if serial-starter.d was deleted
serialstarter_path="/data/conf/serial-starter.d"
serialstarter_file="${serialstarter_path}/dbus-seelevel.conf"

# check if folder is a file (older versions of this driver < v1.0.0)
if [ -f "$serialstarter_path" ]; then
    rm -f "$serialstarter_path"
fi

# check if folder exists
if [ ! -d "$serialstarter_path" ]; then
    mkdir "$serialstarter_path"
fi

# check if file exists
if [ ! -f "$serialstarter_file" ]; then
    {
        echo "service   seelevel    dbus-seelevel"
    } > "$serialstarter_file"
fi



# add install-script to rc.local to be ready for firmware update
filename=/data/rc.local
if [ ! -f "$filename" ]; then
    echo "#!/bin/bash" > "$filename"
    chmod 755 "$filename"
fi

# add enable script to rc.local
# log the output to a file and run it in the background to prevent blocking the boot process
grep -qxF "bash /data/apps/dbus-seelevel/enable.sh > /data/apps/dbus-seelevel/startup.log 2>&1 &" $filename || echo "bash /data/apps/dbus-seelevel/enable.sh > /data/apps/dbus-seelevel/startup.log 2>&1 &" >> $filename


# TODO: stop BLE, CAN and serial?
echo "Stop all dbus-seelevel services..."
for service in /service/dbus-seelevel.*; do
    [ -e "$service" ] && svc -d "$service"
done

# kill driver, if still running
pkill -f "python .*/dbus-seelevel.py /dev/tty.*"

