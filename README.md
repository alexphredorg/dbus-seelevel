# dbus-seelevel
Integration of a Seelevel sensor with Victron Cerbo using a custom ESP32 device

# Introduction
This is some hacky code to read a seelevel sensor and publish it on the Cerbo.  The ESP32 device is connected directly to the sensor 
(specifics are in the seelevel.ino file) and then periodically sends sensor data back to the Cerbo over the serial connection.

The Venus OS service in dbus-seelevel reads the serial data, computes the amount of water in the tank, and publishes it to the Venus
databus.

While this is hacky I've been running it for a year with no issues.  

I figured out some of the Venus OS integration by using the code in dbus-serialbattery, and portions of the code in dbus-seelevel
came from that project.  That code can be found here: https://github.com/mr-manuel/venus-os_dbus-serialbattery/
