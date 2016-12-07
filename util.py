import os

VERBOSE = False

def getOutfilePathname(filename):
    '''
    Returns the absolute pathname to the provided filename in the outfiles director.
    :param filename: Name of the file (EX: 'plot.png')
    :return: Absolute pathname (EX: '/home/cs269i/cars/outfiles/plot.png')
    '''
    return '%s/outfiles/%s' % (os.getcwd(), filename)

def fixedCostToHighCost(fixed_cost):
    return 1.0 / fixed_cost + 1.0

def highCostToFixedCost(high_cost):
    return 1.0 / (high_cost + 1)