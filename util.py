import os

VERBOSE = False

def getOutfilePathname(filename):
    '''
    Returns the absolute pathname to the provided filename in the outfiles director.
    :param filename: Name of the file (EX: 'plot.png')
    :return: Absolute pathname (EX: '/home/cs269i/cars/outfiles/plot.png')
    '''
    return '%s/outfiles/%s' % (os.getcwd(), filename)