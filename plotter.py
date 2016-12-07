import util
from car import *
from configurer import *
from protocol import *
from run import *
from simulator import *
from optparse import OptionParser


class Plotter:
    def __init__(self, variable_name, variable_min, variable_max, variable_step, metric_name):
        self.variable_name = variable_name
        self.variable_min = variable_min
        self.variable_max = variable_max
        self.variable_step = variable_step
        self.metric_name = metric_name

    def runAndPlot(self, options):
        context_metrics = {}
        variable_values = [self.variable_min + (i * self.variable_step)
                           for i in xrange(int((self.variable_max - self.variable_min) / self.variable_step))]

        num_cars = options.num_cars
        num_roads = options.num_roads
        num_rounds = options.num_rounds
        random_seed = options.random_seed
        high_priority_probability = options.high_priority_probability
        fixed_cost = options.fixed_cost
        unlimited_reward = options.unlimited_reward

        for context in [{'protocol': 'button', 'car': 'truthful', 'my_car': 'truthful', 'label': 'b_t_t'},
                        {'protocol': 'button', 'car': 'truthful', 'my_car': 'aggressive', 'label': 'b_t_a'}]:
            protocol = getProtocol(context['protocol'])
            CarClass = getCarClass(context['car'])
            MyCarClass = getCarClass(context['my_car'])
            metric_values = []
            for variable_value in variable_values:
                # Update the variable value.
                if self.variable_name == 'num_cars':
                    num_cars = variable_value
                elif self.variable_name == 'num_roads':
                    num_roads = variable_value
                elif self.variable_name == 'high_priority_probability':
                    high_priority_probability = variable_value                
                elif self.variable_name == 'fixed_cost':
                    fixed_cost = variable_value
                else:
                    raise Exception('Unrecognized variable_name %s' % self.variable_name)
                
                # Run the simulation.
                config = Configurer()
                config.configWithArgs(num_cars, num_roads, random_seed, high_priority_probability)
                simulator = Simulator(protocol, CarClass, MyCarClass, num_rounds, fixed_cost, unlimited_reward,
                                      False, # Do not animate
                                      config)
                simulator.run()

                # Extract the metric value.
                if self.metric_name == 'cost':
                    metric_value = simulator.getMeanCost()
                elif self.metric_name == 'reward':
                    metric_value = simulator.getMeanReward()
                elif self.metric_name == 'my_cost':
                    metric_value = simulator.getMyCarMeanCost()
                elif self.metric_name == 'my_reward':
                    metric_value = simulator.getMyCarMeanReward()
                else:
                    raise Exception('Unrecognized metric_name %s' % self.metric_name)
                
                metric_values.append(metric_value)
                
            context_metrics[context['label']] = metric_values

        # Compute the filename given all the parameters.
        filename = '%s_vs_%s_%.1f_to_%.1f' % \
                   (self.variable_name, self.metric_name, self.variable_min, self.variable_max)
        if self.variable_name is not 'num_cars':
            filename += str(num_cars)
        elif self.variable_name is not 'num_roads':
            filename += str(num_roads)
        elif self.variable_name is not 'high_priority_probability':
            filename += str(high_priority_probability)
        elif self.variable_name is not 'fixed_cost':
            filename += str(fixed_cost)
        filename += '.png'

        self._plotVariableVsMetric(variable_values, context_metrics, filename)
    
    def _plotVariableVsMetric(self, variable_values, metric_values, filename):
        import matplotlib.pyplot as plt

        # Plot values for each context.
        plt.clf()
        for label, metric_value in metric_values.iteritems():
            plt.plot(variable_values, metric_value, label=label)

        # Get a human readable string for the variable name.
        if self.variable_name == 'num_cars':
            variable_name_pretty = 'Number of cars'
        elif self.variable_name == 'num_roads':
            variable_name_pretty = 'Number of roads'
        elif self.variable_name == 'high_priority_probability':
            variable_name_pretty = 'Probability of high priority'                
        elif self.variable_name == 'fixed_cost':
            variable_name_pretty = 'Fixed cost'
        else:
            raise Exception('Unrecognized variable_name %s' % self.variable_name)        

        # Get a human readable string for the metric name.
        if self.metric_name == 'cost':
            metric_name_pretty = 'Total Cost'
        elif self.metric_name == 'reward':
            metric_name_pretty = 'Total Reward'
        elif self.metric_name == 'my_cost':
            metric_name_pretty = 'My Car Cost'
        elif self.metric_name == 'my_reward':
            metric_name_pretty = 'My Car Reward'
        else:
            raise Exception('Unrecognized metric_name %s' % self.metric_name)

        # Decorate the plot.
        plt.title('%s vs. %s' % (variable_name_pretty, metric_name_pretty))
        plt.xlabel(self.variable_name)
        plt.ylabel(metric_name_pretty)
        plt.grid()
        plt.legend()
        plt.xlim(xmin=variable_values[0], xmax=variable_values[-1])
        plt.savefig(util.getOutfilePathname(filename))

        print('Saved file: %s' % filename)