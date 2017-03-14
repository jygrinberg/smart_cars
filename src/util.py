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
    if protocol_class_name == 'generalized_optimal':
        return GeneralizedOptimalProtocol
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

##################
# Board helpers. #
##################
# The road network is modeled as a grid of one-way streets.
# Street ids 1, 5, 9, etc. go down/right.
# Street ids 3, 7, 11, etc. go up/left.

def getPositionDirection(x, y):
    if x % 4 == 1:
        # Car is moving down.
        return 0, 1
    elif x % 4 == 3:
        # Car is moving up.
        return 0, -1
    elif y % 4 == 1:
        # Car is moving right.
        return 1, 0
    else:
        # Car is moving left.
        return -1, 0

def getUpcomingQueue(x, y, num_intersections=1):
    dx, dy = getPositionDirection(x, y)
    return x + 2 * dx * num_intersections, y + 2 * dy * num_intersections

def getNextIntersection(x, y, num_intersections=1):
    dx, dy = getPositionDirection(x, y)
    return x + dx * num_intersections, y + dy * num_intersections

def isInBounds(x, y, board):
    return 0 <= x < len(board) and 0 <= y < len(board[0])

def isDestination(x, y, board):
    if x == 0 or y == 0 or x == len(board) - 1 or y == len(board[0]):
        return True
    return False

def isIntersection(x, y, board):
    if x % 2 == 1 and y % 2 == 1:
        return True
    return False

def getCompetingQueuePosition(x, y):
    dx, dy = getPositionDirection(x, y)

    intersection_x = x + dx
    intersection_y = y + dy
    if abs(dx) == 1:
        # Car is moving horizontally.
        if intersection_x % 4 == 1:
            # Intersecting road is moving down.
            return intersection_x, intersection_y - 1
        else:
            # Intersecting road is moving up.
            return intersection_x, intersection_y + 1
    else:
        # Car is moving vertically.
        if intersection_y % 4 == 1:
            # Intersecting road is moving right.
            return intersection_x - 1, intersection_y
        else:
            # Intersecting road is moving left.
            return intersection_x + 1, intersection_y

def getQueueCost(queue, high_cost):
    # if isDestination(x, y, board):
    #     raise Exception('Attempting to get the queue cost for a destination position.')
    #
    # if not isInBounds(x, y, board):
    #     raise Exception('Attempting to get the queue cost for an out-of-bounds position: (%d, %d)' % (x, y))
    return sum([high_cost * car.priority + 1 * (1 - car.priority) for car in queue])

def getCarCost(car, high_cost):
    return high_cost * car.priority + 1 * (1 - car.priority)
