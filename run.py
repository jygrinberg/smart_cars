#!/usr/bin/python
"""
Main file for running the car simulation.
"""

import os
from optparse import OptionParser
from simulator import *
from protocol import *
from car import *

def getProtocol(protocol_name):
    """
    Returns an *instance* of a protocol.
    """
    protocol_name = protocol_name.lower()
    if protocol_name == 'random':
        return RandomProtocol()
    return None

def getCarClass(car_class_name):
    """
    Returns the *class* of a car.
    """
    car_class_name = car_class_name.lower()
    if car_class_name == 'random':
        return RandomCar
    return None

def getOptions():
    '''
    Get command-line options and handle errors.
    :return: Command line options and arguments.
    '''
    parser = OptionParser()

    parser.add_option('-p', '--protocol', dest='protocol',
                      help='name of the protocol to use: random')
    parser.add_option('-c', '--car', dest='car_class_name',
                      help='name of the car to use: random')

    options, args = parser.parse_args()

    return options, args

def main():
    # Parse the command line arguments.
    options, args = getOptions()

    # Get the protocol and car specified by the command line arguments.
    protocol = getProtocol(options.protocol)
    CarClass = getCarClass(options.car_class_name)

    # Initialize the simulator.
    simulator = Simulator(protocol, CarClass)

    # Run the simulation.
    simulator.run()

if __name__ == '__main__':
    main()