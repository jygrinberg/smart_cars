import random
import numpy as np

class Configurer:
    """
    Class responsible for storing the simulation configuration. The parameters passed into the constructor are always
    read from command-line args. Other parameters can either be specified from the command-line args, or from a config
    file.
    """

    def __init__(self, ProtocolClass, CarClass, MyCarClass, num_rounds, high_cost, force_unlimited_reward, animate):
        """
        :param ProtocolClass: Class name of a subclass of the Protocol class.
        :param CarClass: Class name of a subclass of the Car class. All cars (except possibly one -- see
         the description for MyCarClass) will be this type of car.
        :param MyCarClass: Class name of a subclass of the Car class. If not None, one car of of this type will be
         created.
        :param num_rounds: Number of simulation rounds to run. The same cars exist across rounds, and the protocol keeps
         track of each car's reward across rounds. Each round represents one trip per car.
        :param high_cost: Cost per car high priority car per iteration. Low priority cars accrue a cost of 1.0 per
        iteration.
        :param force_unlimited_reward: Usually, cars can only bid high if they have enough reward (as defined by the
         protocol). If True, always allow cars to bid high.
        :param animate: If True, visualize the simulation using the Tkinter animator.
        """
        self.ProtocolClass = ProtocolClass
        self.CarClass = CarClass
        self.MyCarClass = MyCarClass

        # The protocol is initialized in self._finalizeConfig() once all the configurer's parameters are set.
        self.protocol = None

        # Initialize simulation parameters that are always specified by command line args.
        self.num_rounds = num_rounds
        self.high_cost = high_cost
        self.force_unlimited_reward = force_unlimited_reward
        self.animate = animate

        # Initialize parameters that can be specified either by command line args or by a config file.
        self.config_from_file = True
        self.num_cars = None
        self.num_roads = None
        self.width = None
        self.height = None
        self._car_trips = []
        self.random_seed = None
        self.high_priority_probability = 0.3

    def configWithArgs(self, num_cars, num_roads, random_seed, high_priority_probability):
        """
        Set parameters that can either be specified by command-line args or from a file using values from the
        command-line.
        :param num_cars: Number of cars in the simulation.
        :param num_roads: Number of roads in each direction (up, down, left, right).
        :param random_seed: Random seed value.
        :param high_priority_probability: Probability that a car is high priority.
        """
        self.config_from_file = False
        self.num_cars = num_cars
        self.num_roads = num_roads
        self.high_priority_probability = high_priority_probability

        if random_seed >= 0:
            self.random_seed = random_seed

        # Important! Might need to multiply by 4 instead of 2 if using getRandomTurnRoute() instead of getRandomRoute().
        self.width = self.num_roads * 2 + 1
        self.height = self.num_roads * 2 + 1

        self._finalizeConfiguration()

    def configFromFile(self, filename):
        """
        Set parameters that can either be specified by command-line args or from a file using values from the specified
        filename
        :param filename: Pathname for a config file.
        """
        with open(filename, 'r') as f:
            try:
                self.num_cars = int(f.readline().strip())
            except:
                raise Exception('First line in config file must have the format: num_cars (int)')
            try:
                self.num_roads = int(f.readline().strip())
            except:
                raise Exception('Second line in config file must have the format: num_roads (int)')

            # Important! Might need to multiply by 4 instead of 2 if using getRandomTurnRoute() instead of
            # getRandomRoute().
            self.width = self.num_roads * 2 + 1
            self.height = self.num_roads * 2 + 1

            for line in f.readlines():
                values = line.strip().split(' ')
                if len(values) != 3:
                    raise Exception('Line in config file must have the format: '
                                    'side (string)<space>position (int)<space>priority (int), but was:\n\t%s' % line)
                side, position, priority = values
                position = int(position)
                priority = float(priority)
                route = []
                if side == 'top':
                    origin = (position, 0)
                    route.append(['down', self.height - 1])
                    destination = (position, self.height - 1)
                elif side == 'left':
                    origin = (0, position)
                    route.append(['right', self.width - 1])
                    destination = (self.width - 1, position)
                elif side == 'bottom':
                    origin = (position, self.height - 1)
                    route.append(['up', self.height - 1])
                    destination = (position, 0)
                elif side =='right':
                    origin = (self.width - 1, position)
                    route.append(['left', self.width - 1])
                    destination = (0, position)
                else:
                    raise Exception('Side value in config file must be top, left, bottom, or right, but is: %s' % side)
                self._car_trips.append((origin, destination, route, priority))
        self._finalizeConfiguration()

    def getNextCarTrip(self, round_id, car_id):
        """
        Get the starting position, destination, route from origin to destination, and priority for the trip. The
        route is a list of 'directions', where each direction is a tuple of the form ({'up', 'down', 'left', or
        'right'}, num_steps).
        :param round_id: ID number of the round (used for pseudo-random number generation).
        :param car_id: ID number of the car (used for pseudo-random number generation).
        :return: origin, destination, route, priority
        """
        if self.config_from_file:
            return self._car_trips[car_id]

        # Set the random seed for pseudo-random number generation.
        if self.random_seed is not None:
            random.seed(self.random_seed + 43 * (car_id + 37 * round_id))

        # Generate a random route and pick a random priority (priority is 1 with probability
        # self.high_priority_probability).
        origin, destination, route = self._getRandomRoute()
        priority = np.random.choice([0,1],
            p=[1-self.high_priority_probability, self.high_priority_probability])
        return origin, destination, route, priority

    def _getRandomRoute(self):
        """
        Generates a random route for a car. Cars start at a random coordinate on one of the edges of the board and
        continue straight until they reach the end of the board.
        :return: origin coordinates, destination coordinates, route (which is a list of [direction, num_segments]
        lists). direction can be either 'up', 'down', 'left', or 'right'.
        """
        route = []
        # Pick a starting side. If the board is 3x3 (i.e. one road going right and one road going down), cars can only
        # start on the top or left. Otherwise, cars can start on any side.
        possible_sides = ['top', 'left']
        if self.width >= 4:
            possible_sides.append('bottom')
        if self.height >= 4:
            possible_sides.append('right')
        side = random.choice(possible_sides)

        # Based on the starting side, pick a random number of road segments to go straight, at which point the car will
        # turn. Determine which direction the turn will be, then compute the coordinates of the destination.
        if side == 'top':
            x = random.randint(0, (self.width - 2) / 4) * 4 + 1
            origin = (x, 0)
            route.append(['down', self.height - 1])
            destination = (x, self.height - 1)
        elif side == 'left':
            y = random.randint(0, (self.height - 2) / 4) * 4 + 1
            origin = (0, y)
            route.append(['right', self.width - 1])
            destination = (self.width - 1, y)
        elif side == 'bottom':
            x = random.randint(0, (self.width - 4) / 4) * 4 + 3
            origin = (x, self.height - 1)
            route.append(['up', self.height - 1])
            destination = (x, 0)
        else:
            y = random.randint(0, (self.height - 4) / 4) * 4 + 3
            origin = (self.width - 1, y)
            route.append(['left', self.width - 1])
            destination = (0, y)

        return origin, destination, route

    def _getRandomTurnRoute(self):
        """
        Generates a random route for a car. Cars start at a random coordinate on one of the edges of the board. They
        travel straight for a random number of road segments, then turn (in the direction of the street on which they
        land), then continue straight until they reach the end of the board.
        :return: origin coordinates, destination coordinates, route (which is a list of [direction, num_segments]
        lists). direction can be either 'up', 'down', 'left', or 'right'.
        """
        route = []
        # Pick a starting side.
        side = random.choice(['top', 'left', 'bottom', 'right'])
        # Based on the starting side, pick a random number of road segments to go straight, at which point the car will
        # turn. Determine which direction the turn will be, then compute the coordinates of the destination.
        if side == 'top':
            x = random.randint(0, (self.width - 2) / 4) * 4 + 1
            origin = (x, 0)
            route.append(['down', random.randrange(1, self.height - 1, 2)])
            if (route[0][1] - 1) % 4 == 0:
                route.append(['right', self.width - 1 - x])
                destination = (self.width - 1, route[0][1])
            else:
                route.append(['left', x])
                destination = (0, route[0][1])
        elif side == 'left':
            y = random.randint(0, (self.height - 2) / 4) * 4 + 1
            origin = (0, y)
            route.append(['right', random.randrange(1, self.width - 1, 2)])
            if (route[0][1] - 1) % 4 == 0:
                route.append(['down', self.height - 1 - y])
                destination = (route[0][1], self.height - 1)
            else:
                route.append(['up', y])
                destination = (route[0][1], 0)
        elif side == 'bottom':
            x = random.randint(0, (self.width - 4) / 4) * 4 + 3
            origin = (x, self.height - 1)
            route.append(['up', random.randrange(1, self.height - 1, 2)])
            if (self.height - route[0][1] - 2) % 4 == 0:
                route.append(['right', self.width - 1 - x])
                destination = (self.width - 1, self.height - 1 - route[0][1])
            else:
                route.append(['left', x])
                destination = (0, self.height - 1 - route[0][1])
        else:
            y = random.randint(0, (self.height - 4) / 4) * 4 + 3
            origin = (self.width - 1, y)
            route.append(['left', random.randrange(1, self.width - 1, 2)])
            if (self.width - route[0][1] - 2) % 4 == 0:
                route.append(['down', self.height - 1 - y])
                destination = (self.width - 1 - route[0][1], self.height - 1)
            else:
                route.append(['up', y])
                destination = (self.width - 1 - route[0][1], 0)

        return origin, destination, route

    def _finalizeConfiguration(self):
        """
        Performs any tasks require to complete configuration.
        :return:
        """
        self.protocol = self.ProtocolClass(self)