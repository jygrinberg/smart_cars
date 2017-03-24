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
    if protocol_class_name == 'greedy':
        return GreedyProtocol
    if protocol_class_name == 'generalized_greedy_0':
        return GeneralizedGreedyProtocol0
    if protocol_class_name == 'generalized_greedy_2':
        return GeneralizedGreedyProtocol2
    if protocol_class_name == 'generalized_greedy_4':
        return GeneralizedGreedyProtocol4
    if protocol_class_name == 'generalized_greedy_6':
        return GeneralizedGreedyProtocol6
    if protocol_class_name == 'generalized_greedy_8':
        return GeneralizedGreedyProtocol8
    if protocol_class_name == 'greedy_random':
        return GreedyRandomProtocol
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

def getPositionDirection(position):
    x, y = position
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

def getUpcomingQueue(position, num_intersections=1):
    x, y = position
    dx, dy = getPositionDirection(position)
    return x + 2 * dx * num_intersections, y + 2 * dy * num_intersections

def getNextPosition(position, num_intersections=1, reverse=False):
    dx, dy = getPositionDirection(position)
    
    if reverse:
        num_intersections *= -1
        
    x, y = position
    return x + dx * num_intersections, y + dy * num_intersections

def isInBounds(position, board):
    return 0 <= position[0] < len(board) and 0 <= position[1] < len(board[0])

def isDestination(position, board):
    x, y = position
    if x == 0 or y == 0 or x == len(board) - 1 or y == len(board[0]):
        return True
    return False

def isIntersection(position):
    x, y = position
    if x % 2 == 1 and y % 2 == 1:
        return True
    return False

def getCompetingPosition(position):
    x, y = position
    dx, dy = getPositionDirection(position)

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


def getPositionsWithinDistance(position, distance):
    positions = set()
    for curr_distance in xrange(distance + 1):
        curr_position = util.getNextPosition(position, curr_distance)
        positions.add(curr_position)
        if not util.isIntersection(curr_position):
            competing_position = util.getCompetingPosition(curr_position)
            addPositionsWithinDistanceRec(competing_position, curr_distance, positions)
    return positions

def addPositionsWithinDistanceRec(position, distance, positions):
    if position in positions or position[0] is None or position[1] is None:
        return

    positions.add(position)
    competing_position = util.getCompetingPosition(position)
    positions.add(competing_position)

    if distance == 0:
        return

    prev_intersection = util.getNextPosition(position, 1, reverse=True)
    positions.add(prev_intersection)
    prev_position = util.getNextPosition(position, 2, reverse=True)

    addPositionsWithinDistanceRec(prev_position, distance - 2, positions)
    addPositionsWithinDistanceRec(competing_position, distance - 2, positions)

def getQueueCost(queue, high_cost):
    # if isDestination(x, y, board):
    #     raise Exception('Attempting to get the queue cost for a destination position.')
    #
    # if not isInBounds(x, y, board):
    #     raise Exception('Attempting to get the queue cost for an out-of-bounds position: (%d, %d)' % (x, y))
    return sum([high_cost * car.priority + 1 * (1 - car.priority) for car in queue])

def numTravellingCars(queue):
    return sum([1 for car in queue if not car.hasArrived()])

def getCarCost(car, high_cost):
    """
    Returns the cost of the car per iteration.
    """
    return high_cost * car.priority + 1 * (1 - car.priority)

def getCarOptimalCost(car, high_cost):
    """
    Returns a lower bound on the cost the provided car can incur (assumes cars can drive through each other).
    """
    return getCarCost(car, high_cost) * \
           (abs(car.position[0] - car.destination[0]) + abs(car.position[1] - car.destination[1]))