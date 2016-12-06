import os

VERBOSE = False

def getOutfilePathname(filename):
    '''
    Returns the absolute pathname to the provided filename in the outfiles director.
    :param filename: Name of the file (EX: 'plot.png')
    :return: Absolute pathname (EX: '/home/cs269i/cars/outfiles/plot.png')
    '''
    return '%s/outfiles/%s' % (os.getcwd(), filename)

def plotVariableVsCost(variables, costs, variable_name, filename):
    '''
    Plots total cost as the value of some simulation variable is changed.
    :param variables: List of variable values.
    :param costs: Dictionary. Keys are protocol/car name. Value is a list of total cost per variable value.
    :param variable_name: String representation of the variable (ex: 'Cars').
    :param filename: Filename (ex: 'plot.png').
    '''
    import matplotlib.pyplot as plt
    plt.clf()
    for name, curr_costs in costs.iteritems():
        plt.plot(variables, curr_costs, label=name)

    plt.title('Number of %s vs. Total Cost' % variable_name)
    plt.xlabel('Number of %s' % variable_name.lower())
    plt.ylabel('Total cost')
    plt.grid()
    plt.legend()
    plt.xlim(xmin=variables[0])
    plt.savefig(getOutfilePathname(filename))
    print('Saved file: %s' % filename)


def plotVariableVsReward(variables, rewards, variable_name, filename):
    '''
    Plots total cost as the value of some simulation variable is changed.
    :param variables: List of variable values.
    :param rewards: Dictionary. Keys are protocol/car name. Value is a list of total reward per variable value.
    :param variable_name: String representation of the variable (ex: 'Cars').
    :param filename: Filename (ex: 'plot.png').
    '''
    import matplotlib.pyplot as plt
    plt.clf()
    for name, curr_rewards in rewards.iteritems():
        plt.plot(variables, curr_rewards, label=name)

    plt.title('Number of %s vs. Total Rewards' % variable_name)
    plt.xlabel('Number of %s' % variable_name.lower())
    plt.ylabel('Total rewards')
    plt.grid()
    plt.legend()
    plt.xlim(xmin=variables[0])
    plt.savefig(getOutfilePathname(filename))
    print('Saved file: %s' % filename)