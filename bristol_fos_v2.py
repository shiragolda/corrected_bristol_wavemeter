"""
Code to control the Bristol Fiber Optic Switch from linux
Shira Jackson 2019

The Bristol Fiber Optic Switch uses USB-DIO24/37 from Measurement Computing
The pins used from the USB/DIO board are 35, 36, 37 corresponding to FIRSTPORTA

requires uldaq: https://github.com/mccdaq/uldaq
Be sure to install the prerequisites! uldaq requires UL for Linux C API

The device connects as hidraw. Check the port and give permissions.
sudo chmod 777 /dev/hidraw*

"""
from __future__ import print_function
import time
from os import system
from sys import stdout

from uldaq import (get_daq_device_inventory, DaqDevice, InterfaceType,
                   DigitalDirection, DigitalPortIoType)



class FOS:
    def __init__(self):
        devices = get_daq_device_inventory(InterfaceType.USB)
        number_of_devices = len(devices)
        if number_of_devices == 0:
            raise Exception('Error: No DAQ devices found')

        print('Found', number_of_devices, 'DAQ device(s):')
        for i in range(number_of_devices):
            print('  ', devices[i].product_name, ' (', devices[i].unique_id, ')', sep='')

        # Create the DAQ device object associated with the specified descriptor index.
        daq_device = DaqDevice(devices[0]) #if more than one device, change this to the one you want
        daq_device.connect() ##
        self.daq_device = daq_device

        # Get the DioDevice object and verify that it is valid.
        dio_device = daq_device.get_dio_device()

        if dio_device is None:
            raise Exception('Error: The device does not support digital output')
        self.dio_device = dio_device

        self.connect()  ##
        # self.port_to_write = self.dio_device.get_info().get_port_types()[0]

    def connect(self):
        # Establish a connection to the DAQ device.
        descriptor = self.daq_device.get_descriptor()
        print('\nConnecting to', descriptor.dev_string, '- please wait...')
        # self.daq_device.connect() #NEED sudo chmod 777 /dev/hidraw# for this to work! It won't give you an error related to permissions, but if it says "Device not found' this is probably the problem!

        # Get the port types for the device(AUXPORT, FIRSTPORTA, ...)
        dio_info = self.dio_device.get_info()

        port_types = dio_info.get_port_types()

        self.port_to_write = port_types[0] #FIRSTPORTA is used for the Brifos/stol switch

        # Get the port I/O type and the number of bits for the first port.
        port_info = dio_info.get_port_info(self.port_to_write)
        print(self.port_to_write)
        # If the port is bit configurable, then configure the individual bits for output; otherwise, configure the entire port for output.
        if port_info.port_io_type == DigitalPortIoType.BITIO:
            # Configure all of the bits for output for the first port.
            for bit_number in range(port_info.number_of_bits):
                dio_device.d_config_bit(port_to_write, bit_number,
                                        DigitalDirection.OUTPUT)
        elif port_info.port_io_type == DigitalPortIoType.IO:
        # else:
            # Configure the entire port for output.
            self.dio_device.d_config_port(self.port_to_write, DigitalDirection.OUTPUT)  #....
            print("here")  ##



        print('Active DAQ device: ', descriptor.dev_string, ' (',
                descriptor.unique_id, ')\n', sep='')



    def change_channel(self,channel):
        """ Change the fiber optic channel - choose 0,1,2,3"""
        if channel in [0,1,2,3]:
            self.dio_device.d_out(self.port_to_write,channel) #....
        else:
            print("Invalid channel")

    def close(self):
        if self.daq_device:
            if self.daq_device.is_connected():
                self.daq_device.disconnect()
        self.daq_device.release()



if __name__ == '__main__':
    fos = FOS()
    # print(fos.change_channel(0))
    # fos.close()

