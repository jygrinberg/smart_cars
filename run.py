#!/usr/bin/python
"""
Main file for running the car simulation. Some sample use cases are listed below:

Basic usage:
python run.py --num_cars=10 --num_roads=5 --num_rounds=10 --protocol=vcg --car=truthful

Load a simulation configuration from a file:
python run.py --config_filename=<path_to_file.txt> --num_rounds=10

Generate a plot (either num_cars vs. total_cost, or num_roads vs. total_cost):
python run.py --plot_road_simulations num_cars=10 --num_rounds=10 --protocol=vcg --car=truthful
python run.py --plot_car_simulations num_roads=10 --num_rounds=10 --protocol=vcg --car=truthful

Other flags that can be combined with any of the use cases listed above:
--random_seed=<int value>
--fixed_cost=<float in the range [0,1]>
--unlimited_reward

"""

import os
import util
from car import *
from configurer import *
from protocol import *
from simulator import *
from optparse import OptionParser

def getProtocol(protocol_name):
    """
    Returns an *instance* of a protocol.
    """
    protocol_name = protocol_name.lower()
    if protocol_name == 'random':
        return RandomProtocol()
    if protocol_name == 'vcg':
        return VCGProtocol()
    if protocol_name == 'button':
        return ButtonProtocol()
    raise Exception('Unrecognized protocol name: %s' % protocol_name)

def getCarClass(car_class_name):
    """
    Returns the *class* of a car.
    """
    car_class_name = car_class_name.lower()
    if car_class_name == 'random':
        return RandomCar
    if car_class_name == 'truthful':
        return TruthfulCar
    if car_class_name == 'aggressive':
        return AggressiveCar
    raise Exception('Unrecognized car class name: %s' % car_class_name)

def runAndPlotRoadSimulations(options):
    min_num_roads = 1
    max_num_roads = 50
    costs = {}
    num_roads = [curr_num_roads for curr_num_roads in xrange(min_num_roads, max_num_roads + 1) if
                 curr_num_roads < 20 or curr_num_roads % 2 == 0]
    for context in [{'protocol': 'random', 'car': 'random'}, {'protocol': 'vcg', 'car': 'truthful'}]:
        protocol = getProtocol(context['protocol'])
        CarClass = getCarClass(context['car'])
        curr_costs = []
        for curr_num_roads in num_roads:
            config = Configurer()
            config.configWithArgs(options.num_cars, curr_num_roads, options.random_seed,
                                  options.high_priority_probability)
            simulator = Simulator(protocol, CarClass, options.num_rounds, options.fixed_cost, options.unlimited_reward,
                                  False, config)
            simulator.run()
            curr_costs.append(simulator.getMeanCost())
        costs[context['protocol']] = curr_costs
    util.plotVariableVsCost(num_roads, costs, 'Roads',
                            'roads_vs_cost_%d_%d_%d_%.1f.png' % (min_num_roads, max_num_roads, options.num_cars,
                                                                 options.fixed_cost))

def runAndPlotCarSimulations(options):
    min_num_cars = 0
    max_num_cars = 1000
    num_cars_delta = 100
    costs = {}
    num_cars = xrange(min_num_cars, max_num_cars + 1, num_cars_delta)
    for context in [{'protocol': 'random', 'car': 'random'}, {'protocol': 'vcg', 'car': 'truthful'}]:
        protocol = getProtocol(context['protocol'])
        CarClass = getCarClass(context['car'])
        curr_costs = []
        for curr_num_cars in num_cars:
            config = Configurer()
            config.configWithArgs(curr_num_cars, options.num_roads, options.random_seed,
                                  options.high_priority_probability)
            simulator = Simulator(protocol, CarClass, options.num_rounds, options.fixed_cost, options.unlimited_reward,
                                  False, config)
            simulator.run()
            curr_costs.append(simulator.getMeanCost())
        costs[context['protocol']] = curr_costs
    util.plotVariableVsCost(num_cars, costs, 'Cars',
                            'cars_vs_cost_%d_%d_%d_%.1f.png' % (min_num_cars, max_num_cars, options.num_roads,
                                                                options.fixed_cost))

def runAndPlotCheatingCarSimulations(options):
    min_num_cars = 0
    max_num_cars = 1000
    num_cars_delta = 100
    rewards = {}
    num_cars = xrange(min_num_cars, max_num_cars + 1, num_cars_delta)
    for context in [{'protocol': 'random', 'car': 'random'}, {'protocol': 'vcg', 'car': 'truthful'}]:
        protocol = getProtocol(context['protocol'])
        CarClass = getCarClass(context['car'])
        curr_rewards = []
        for curr_num_cars in num_cars:
            config = Configurer()
            config.configWithArgs(curr_num_cars, options.num_roads, options.random_seed,
                                  options.high_priority_probability)
            simulator = Simulator(protocol, CarClass, options.num_rounds, options.fixed_cost, options.unlimited_reward,
                                  False, config)
            simulator.run()
            curr_rewards.append(simulator.getMyCarMeanReward())
        rewards[context['protocol']] = curr_rewards
    util.plotVariableVsCost(num_cars, rewards, 'Cars',
                            'cars_vs_rewards_%d_%d_%d_%.1f.png' % (min_num_cars, max_num_cars, options.num_roads,
                                                                options.fixed_cost))

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
    parser.add_option('--num_cars', dest='num_cars', type='int', default=100,
                      help='number of cars on the road')
    parser.add_option('--num_rounds', dest='num_rounds', type='int', default=10,
                      help='number of rounds to simulate')
    parser.add_option('--num_roads', dest='num_roads', type='int', default=5,
                      help='number of up/down or left/right road pairs in the network')
    parser.add_option('-f', '--fixed_cost', dest='fixed_cost', type='float', default=1.0,
                      help='fixed cost per car per iteration')
    parser.add_option('--high_priority_probability', dest='high_priority_probability', type='float', default=0.1,
                      help='fixed cost per car per iteration')
    parser.add_option('--config_filename', dest='config_filename', default=None,
                      help='pathname for file specifying the board configuration')
    parser.add_option('--plot_road_simulations', dest='plot_road_simulations', action='store_true',
                      help='generate a plot of num_roads vs. total cost')
    parser.add_option('--plot_car_simulations', dest='plot_car_simulations', action='store_true',
                      help='generate a plot of num_cars vs. total cost')
    parser.add_option('--plot_cheating_car_simulations', dest='plot_cheating_car_simulations', action='store_true',
                      help='generate a plot of num_cars vs. total rewards of cheating car')
    parser.add_option('-s', '--random_seed', dest='random_seed', type='int', default=None,
                      help='seed to use a pseud-random generator')
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
                      help='print the board after each iteration')
    parser.add_option('-a', '--animate', dest='animate', action='store_true',
                      help='display an animation of the simulation')
    parser.add_option('-u', '--unlimited_reward', dest='unlimited_reward', action='store_true',
                      help='initialize cars with infinite reward so they can bid 1.0 whenever desired')
    options, args = parser.parse_args()

    # Set the verbose flag.
    if options.verbose:
        util.VERBOSE = True

    return options, args

def main():
    # Parse the command line arguments.
    options, args = getOptions()

    # Set a program-wide random seed for pseudo-random number generation.
    setRandomSeed(options.random_seed)

    if options.plot_road_simulations:
        runAndPlotRoadSimulations(options)
    elif options.plot_car_simulations:
        runAndPlotCarSimulations(options)
    elif options.plot_cheating_car_simulations:
        runAndPlotCheatingCarSimulations(options)
    else:
        # Get the protocol and car specified by the command line arguments.
        protocol = getProtocol(options.protocol)
        CarClass = getCarClass(options.car_class_name)

        # Set up the configurer, which can configure the simulation from a config file, or from command line args and
        # randomly generated car routes.
        config = Configurer()
        if options.config_filename:
            config.configFromFile(options.config_filename)
        else:
            config.configWithArgs(options.num_cars, options.num_roads, options.random_seed,
                                  options.high_priority_probability)

        # Initialize the simulator.
        simulator = Simulator(protocol, CarClass, options.num_rounds, options.fixed_cost, options.unlimited_reward,
                              options.animate, config)

        # Run the simulation.
        simulator.run()

if __name__ == '__main__':
    main()