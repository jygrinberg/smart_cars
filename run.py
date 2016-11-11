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
    if protocol_name == 'vcg':
        return VCGProtocol()
    return None

def getCarClass(car_class_name):
    """
    Returns the *class* of a car.
    """
    car_class_name = car_class_name.lower()
    if car_class_name == 'random':
        return RandomCar
    if car_class_name == 'truthful':
        return TruthfulCar
    return None

def getOptions():
    '''
    Get command-line options and handle errors.
    :return: Command line options and arguments.
    '''
    parser = OptionParser()

    parser.add_option('-p', '--protocol', dest='protocol',
                      help='name of the protocol to use: random, vcg')
    parser.add_option('-c', '--car', dest='car_class_name',
                      help='name of the car to use: random, truthful')
    parser.add_option('-n', '--num_cars', dest='num_cars', type='int', default=100,
                      help='number of cars on the road')
    parser.add_option('-r', '--num_rounds', dest='num_rounds', type='int', default=10,
                      help='number of rounds to simulate')
    parser.add_option('-g', '--num_roads', dest='num_roads', type='int', default=5,
                      help='number of up/down or left/right road pairs in the network')
    parser.add_option('-s', '--random_seed', dest='random_seed', type='int', default=None,
                      help='seed to use a pseud-random generator')
    options, args = parser.parse_args()

    return options, args

def main():
    # Parse the command line arguments.
    options, args = getOptions()

    # Get the protocol and car specified by the command line arguments.
    protocol = getProtocol(options.protocol)
    CarClass = getCarClass(options.car_class_name)

    # Initialize the simulator.
    simulator = Simulator(protocol, CarClass, options.num_cars, options.num_rounds, options.num_roads,
                          options.random_seed)

    # Run the simulation.
    simulator.run()

if __name__ == '__main__':
    main()