#!/usr/bin/python
"""
Main file for running the car simulation.
"""

import os
from optparse import OptionParser
from simulator import *
from protocol import *
from car import *
import util

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

def runAndPlotRoadSimulations(num_cars, num_rounds):
    min_num_roads = 1
    max_num_roads = 50
    costs = {}
    num_roads = xrange(min_num_roads, max_num_roads + 1)
    for context in [{'protocol': 'random', 'car': 'random'}, {'protocol': 'vcg', 'car': 'truthful'}]:
        protocol = getProtocol(context['protocol'])
        CarClass = getCarClass(context['car'])
        curr_costs = []
        for curr_num_roads in num_roads:
            simulator = Simulator(protocol, CarClass, num_cars, num_rounds, curr_num_roads)
            simulator.run()
            curr_costs.append(simulator.getMeanCost())
        costs[context['protocol']] = curr_costs
    util.plotVariableVsCost(num_roads, costs, 'Roads',
                            'roads_vs_cost_%d_%d_%d.png' % (min_num_roads, max_num_roads, num_cars))

def runAndPlotCarSimulations(num_roads, num_rounds):
    min_num_cars = 0
    max_num_cars = 1000
    num_cars_delta = 100
    costs = {}
    num_cars = xrange(min_num_cars, max_num_cars + 1, num_cars_delta)
    for context in [{'protocol': 'random', 'car': 'random'}, {'protocol': 'vcg', 'car': 'truthful'}]:
        protocol = getProtocol(context['protocol'])
        CarClass = getCarClass(context['car'])
        curr_costs = []
        for curr_num_roads in num_cars:
            simulator = Simulator(protocol, CarClass, curr_num_roads, num_rounds, curr_num_roads)
            simulator.run()
            curr_costs.append(simulator.getMeanCost())
        costs[context['protocol']] = curr_costs
    util.plotVariableVsCost(num_cars, costs, 'Cars',
                            'cars_vs_cost_%d_%d_%d.png' % (min_num_cars, max_num_cars, num_roads))

def setRandomSeed(random_seed):
    """
    Sets a seed for the random module and numpy module, if the provided seed is non-negative.
    :param random_seed: Random seed value.
    """
    if random_seed >= 0:
        print 'Setting random seed to %d.' % random_seed
        random.seed(random_seed)

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
    parser.add_option('--plot_road_simulations', dest='plot_road_simulations', action='store_true',
                      help='generate a plot of num_roads vs. total cost')
    parser.add_option('--plot_car_simulations', dest='plot_car_simulations', action='store_true',
                      help='generate a plot of num_cars vs. total cost')
    options, args = parser.parse_args()

    return options, args

def main():
    # Parse the command line arguments.
    options, args = getOptions()

    # Set a program-wide random seed for pseudo-random number generation.
    setRandomSeed(options.random_seed)

    if options.plot_road_simulations:
        runAndPlotRoadSimulations(options.num_cars, options.num_rounds)
    elif options.plot_car_simulations:
        runAndPlotCarSimulations(options.num_roads, options.num_rounds)
    else:
        # Get the protocol and car specified by the command line arguments.
        protocol = getProtocol(options.protocol)
        CarClass = getCarClass(options.car_class_name)

        # Initialize the simulator.
        simulator = Simulator(protocol, CarClass, options.num_cars, options.num_rounds, options.num_roads)

        # Run the simulation.
        simulator.run()

if __name__ == '__main__':
    main()