import os
from protocol import *
from car import *

VERBOSE = False

def getProtocolClass(protocol_class_name):
    """
    Returns the *class* of a protocol.
    """
    if protocol_class_name is None:
        raise Exception('Must specify a protocol class name.')
    protocol_class_name = protocol_class_name.lower()
    if protocol_class_name == 'random':
        return RandomProtocol
    if protocol_class_name == 'vcg':
        return VCGProtocol
    if protocol_class_name == 'button':
        return ButtonProtocol
    if protocol_class_name == 'optimal':
        return OptimalProtocol
    if protocol_class_name == 'optimal_random':
        return OptimalRandomProtocol
    raise Exception('Unrecognized protocol class name: %s' % protocol_class_name)

def getCarClass(car_class_name):
    """
    Returns the *class* of a car.
    """
    if car_class_name is None:
        return None
    car_class_name = car_class_name.lower()
    if car_class_name == 'random':
        return RandomCar
    if car_class_name == 'truthful':
        return TruthfulCar
    if car_class_name == 'aggressive':
        return AggressiveCar
    if car_class_name == 'statistically_aggressive':
        return StatisticallyAggressiveCar
    raise Exception('Unrecognized car class name: %s' % car_class_name)

def setRandomSeed(random_seed):
    """
    Sets a seed for the random module and numpy module, if the provided seed is non-negative.
    :param random_seed: Random seed value.
    """
    if random_seed >= 0:
        print 'Setting random seed to %d.' % random_seed
        random.seed(random_seed)

def getOutfilePathname(filename):
    """
    Returns the absolute pathname to the provided filename in the outfiles director.
    :param filename: Name of the file (EX: 'plot.png')
    :return: Absolute pathname (EX: '/home/cs269i/cars/outfiles/plot.png')
    """
    outfile_parent_dir = os.getcwd()
    # The outfile dir is in the project root. If the current wording directory is src, set the outfile_parent_dir to the
    # project root (parent directory of src).
    if outfile_parent_dir[-3:] == 'src':
        outfile_parent_dir = outfile_parent_dir[0:-4]
    return '%s/outfiles/%s' % (outfile_parent_dir, filename)

def fixedCostToHighCost(fixed_cost):
    return 1.0 / fixed_cost + 1.0

def highCostToFixedCost(high_cost):
    return 1.0 / (high_cost - 1)