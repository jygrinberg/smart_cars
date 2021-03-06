#!/usr/bin/python
"""
Main file for running the car simulation. Some sample use cases are listed below:

Basic usage:
python run.py --num_cars=10 --num_roads=5 --num_rounds=10 --protocol=vcg --car=truthful

Load a simulation configuration from a file:
python run.py --config_filename=<path_to_file.txt> --num_rounds=10

Generate a plot (either num_cars vs. total_cost, or num_roads vs. total_cost):
python run.py --plot_road_simulations --num_cars=10 --num_rounds=10
python run.py --plot_car_simulations --num_roads=10 --num_rounds=10

Other flags that can be combined with any of the use cases listed above:
--random_seed=<int value>
--high_cost=<float greater than or equal to 1.0>
--unlimited_reward

"""

import util
from configurer import *
from plotter import *
from simulator import *
from optparse import OptionParser

def getOptions():
    """
    Get command-line options and handle errors.
    :return: Command line options and arguments.
    """
    parser = OptionParser()

    parser.add_option('-p', '--protocol', dest='protocol',
                      help='name of the protocol to use: random, vcg')
    parser.add_option('-c', '--car', dest='car_class_name',
                      help='name of the car to use: random, truthful, greedy')
    parser.add_option('-m', '--my_car', dest='my_car_class_name',
                      help='name of the car to use for agent under investigation: random, truthful, greedy')
    parser.add_option('--num_cars', dest='num_cars', type='int', default=100,
                      help='number of cars on the road')
    parser.add_option('--num_rounds', dest='num_rounds', type='int', default=10,
                      help='number of rounds to simulate')
    parser.add_option('--num_roads', dest='num_roads', type='int', default=5,
                      help='number of up/down or left/right road pairs in the network')
    parser.add_option('--high_cost', dest='high_cost', type='float', default=3.0,
                      help='cost for high priority car per iteration (cost for low priority car per iteration is 1)')
    parser.add_option('--high_priority_probability', dest='high_priority_probability', type='float', default=0.1,
                      help='fixed cost per car per iteration')
    parser.add_option('--config_filename', dest='config_filename', default=None,
                      help='pathname for file specifying the board configuration')
    parser.add_option('--plot', dest='plot', action='store_true',
                      help='generate a plot of variable_name vs. metric_name')
    parser.add_option('--contexts', dest='contexts',
                      help='protocols and car types to plot: b, b_o_r, o_r')
    parser.add_option('--variable_name', dest='variable_name',
                      help='name of the variable to vary when plotting: num_cars, num_roads, high_cost, etc.')
    parser.add_option('--variable_min', dest='variable_min', type='float', default=0.0,
                      help='min value of the variable when plotting')
    parser.add_option('--variable_max', dest='variable_max', type='float', default=1.0,
                      help='max value of the variable when plotting')
    parser.add_option('--variable_step', dest='variable_step', type='float', default=0.1,
                      help='step value of the variable when plotting')
    parser.add_option('--metric_name', dest='metric_name',
                      help='name of the metric to compute when plotting: cost, reward, my_cost, my_reward.')
    parser.add_option('-s', '--random_seed', dest='random_seed', type='int', default=None,
                      help='seed to use a pseud-random generator')
    parser.add_option('-v', '--verbose', dest='verbose', type='int', default=0,
                      help='print the board after each iteration: 0 = lowest verbosity, 2 = highest verbosity')
    parser.add_option('-a', '--animate', dest='animate', action='store_true',
                      help='display an animation of the simulation')
    parser.add_option('--print_board', dest='print_board', action='store_true',
                      help='print the state of the board in each iteration of the simulation')
    parser.add_option('-u', '--force_unlimited_reward', dest='force_unlimited_reward', action='store_true',
                      help='initialize cars with infinite reward so they can signal high priority whenever desired')
    options, args = parser.parse_args()

    # Set the verbosity level.
    util.VERBOSE = options.verbose

    return options, args

def main():
    # Parse the command line arguments.
    options, args = getOptions()

    # Set a program-wide random seed for pseudo-random number generation.
    util.setRandomSeed(options.random_seed)

    if options.plot:
        # Generate a plot by varying the value of variable_name versus metric_name.
        plotter = Plotter(options.variable_name, options.variable_min, options.variable_max, options.variable_step,
                          options.metric_name)
        plotter.runAndPlot(options)
    else:
        # Run the simulation with fixed parameters.
        # Set up the configurer, which can configure the simulation from a config file, or from command-line args and
        # randomly generated car routes.
        configuration = Configurer(util.getProtocolClass(options.protocol), util.getCarClass(options.car_class_name),
                                   util.getCarClass(options.my_car_class_name), options.num_rounds, options.high_cost,
                                   options.force_unlimited_reward, options.animate)
        if options.config_filename:
            configuration.configFromFile(options.config_filename)
        else:
            configuration.configWithArgs(options.num_cars, options.num_roads, options.random_seed,
                                         options.high_priority_probability)

        # Initialize the simulator.
        simulator = Simulator(configuration)

        # Run the simulation.
        simulator.run()

if __name__ == '__main__':
    main()