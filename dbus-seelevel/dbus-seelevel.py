#!/usr/bin/env python3

import serial
import time
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from vedbus import VeDbusService  # Provided by velib_python on Venus OS
import logging
import tank_calculations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 
# This function parses tank information from a serial port running our ESP32-based tank monitor.
# and publishes status on the Victron D-Bus.
#
# The design is that the ESP32-based tank monitor sends raw information that it reads from the 
# SeeLevel tank monitor.  This script parses those values to convert the tank monitor values 
# into a water height, and then uses some math on the tank shape to figure out the volume of 
# water in the tank.
#
# As written this script only works for the Ronco B171 tank, but it could be modified to work with
# other tanks.  The logic for that is in the tank_calculations.py file.
#
def publish_tank_status_to_dbus(serial_port, baud_rate, service_name):
    # Initialize D-Bus main loop
    DBusGMainLoop(set_as_default=True)

    # Open serial port
    try:
        ser = serial.Serial(serial_port, baud_rate, timeout=None)
        logger.info(f"Connected to serial port {serial_port} at {baud_rate} baud")
    except serial.SerialException as e:
        logger.error(f"Failed to open serial port {serial_port}: {e}")
        return

    # our boat has 2 Ronco B171 tanks in parallel, and each has a 25 gallon capacity
    tank_count = 2
    full_capacity = 0.09463529 * tank_count  # full capacity in m^3 (25 gallons * 2 tanks)
    # the SeeLevel tank monitor produces a value between 0-255 for each segment.  However the
    # useful range is much narrower, and these values specify that range.
    segment_minimum = 20
    segment_maximum = 150
    # This is the height of each segment in inches.  I'm using a SeeLevel 710-ES3 and measured
    # this height.  It is in inches.
    segment_height = 1.375

    # Create D-Bus service
    dbus_service = VeDbusService(service_name, register=False)

    # Define basic paths for a battery monitor (modify as needed)
    # value docs: https://github.com/victronenergy/venus/wiki/dbus#tank-levels
    dbus_service.add_path('/Mgmt/ProcessName', __file__)
    dbus_service.add_path('/Mgmt/ProcessVersion', '1.0')
    dbus_service.add_path('/Mgmt/Connection', f'Serial {serial_port}')
    dbus_service.add_path('/DeviceInstance', 0)  # Unique device instance
    dbus_service.add_path('/ProductId', 0xFFFF)  # Custom product ID
    dbus_service.add_path('/ProductName', 'Seelevel Tank Monitor')
    dbus_service.add_path('/FirmwareVersion', '1.0')
    dbus_service.add_path('/Connected', 1)  # 1 = connected, 0 = disconnected
    dbus_service.add_path('/FluidType', 1)  # 1 = fresh water
    dbus_service.add_path('/Capacity', full_capacity)  # capacity in m^3
    dbus_service.add_path('/HardwareVersion', '1.0')
    dbus_service.register()

    # values that we update for the tank
    dbus_service.add_path('/Level', None, writeable=True)  # Level in percentage
    dbus_service.add_path('/Status', None, writeable=True)  # 0 = OK, 1 = Disconnected, 3 = Unknown
    dbus_service.add_path('/Remaining', None, writeable=True)  # remaining capacity in m^3'

    # This is called every 5 seconds
    def update_values():
        """Callback to read serial data and update D-Bus values."""
        try:
            logger.debug(f"Reading from serial port... ser.in_waiting={ser.in_waiting}")
            if ser.in_waiting > 0:
                # Read a line from the serial port (assumes data is newline-terminated)
                line = ser.readline().decode('utf-8').strip()
                logger.debug(f"Raw serial data: {line}")

                parts = line.split(',')
                tank = parts[0]
                levels = parts[1:11]
                status = parts[13]
                logger.debug(f"tank: {tank}, levels: {levels}, status: {status}")

                status_code = 0
                connected_code = 0

                if status == "DISCONNECTED":
                    logger.warning("Disconnected from tank monitor")
                    status_code = 1  # Disconnected status
                    connected_code = 0
                elif status == "BAD":
                    logger.warning("Bad data from tank monitor")
                    status_code = 3  # Unknown status
                    connected_code = 0
                elif status == "OK":
                    logger.debug("Connected to tank monitor")
                    status_code = 0
                    connected_code = 0

                # Update D-Bus values for status
                dbus_service['/Status'] = status_code  # 0 = OK
                dbus_service['/Connected'] = connected_code

                # Don't do anything else if we got bad data
                if status_code != 0:
                    return

                # the tank levels are sent in reverse order (top first)
                levels.reverse()
                tank_level_height = 0
                found_top = False
                # process the segments to figure out how much water is in the tank
                for level in levels:
                    level = int(level)
                    if level > segment_maximum and not found_top:
                        # full tank segment
                        tank_level_height += segment_height
                    elif level >= segment_minimum and level <= segment_maximum and not found_top:
                        # partial tank segment
                        tank_level_height += (level - segment_minimum) / (segment_maximum - segment_minimum) * segment_height
                    else: # empty tank segment
                        tank_level_height += 0
                        found_top = True
                # do the math to convert to volume
                volume_ci = tank_calculations.B171_tank_volume_at_height(tank_level_height)
                volume_m3 = tank_calculations.cubic_inches_to_meters_cubed(volume_ci) * tank_count
                percent_full = volume_m3 / full_capacity * 100

                # Update D-Bus values
                dbus_service['/Level'] = percent_full
                dbus_service['/Remaining'] = volume_m3  # Remaining capacity in m^3

                logger.info(f"Published: Level={percent_full:.0f}%, Status={status}, Remaining={volume_m3:.3f}m^3, height={tank_level_height:.1f}inches")
        except Exception as e:
            logger.error(f"Error reading or publishing data: {e}")
            #dbus_service['/Connected'] = 0  # Mark as disconnected on error

        return True  # Keep the timeout running

    # Schedule periodic updates (every 1 second)
    GLib.timeout_add(5000, update_values)

    # Start the main loop
    logger.info(f"Starting D-Bus service: {service_name}")
    mainloop = GLib.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        ser.close()
        mainloop.quit()

if __name__ == "__main__":
    # Example usage
    publish_tank_status_to_dbus(
        serial_port='/dev/ttyACM0',
        baud_rate=115200,
        service_name='com.victronenergy.tank.water'
    )