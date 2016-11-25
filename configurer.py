import random

class Configurer:
    def __init__(self):
        self.config_from_file = True
        self.num_cars = None
        self.num_roads = None
        self.width = None
        self.height = None
        self._car_trips = []

    def configWithArgs(self, num_cars, num_roads):
        self.config_from_file = False
        self.num_cars = num_cars
        self.num_roads = num_roads

        # Important! Might need to multiply by 4 instead of 2 if using getRandomTurnRoute() instead of getRandomRoute().
        self.width = self.num_roads * 2 + 1
        self.height = self.num_roads * 2 + 1

    def configFromFile(self, filename):
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

    def getNextCarTrip(self, car_id):
        if self.config_from_file:
            return self._car_trips[car_id]

        # Generate a random route and pick a random priority in the range [0, 1].
        origin, destination, route = self._getRandomRoute()
        priority = random.choice([0, 1])
        return origin, destination, route, priority

    def _getRandomRoute(self):
        '''
        Generates a random route for a car. Cars start at a random coordinate on one of the edges of the board and
        continue straight until they reach the end of the board.
        :return: origin coordinates, destination coordinates, route (which is a list of [direction, num_segments]
        lists). direction can be either 'up', 'down', 'left', or 'right'.
        '''
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
        '''
        Generates a random route for a car. Cars start at a random coordinate on one of the edges of the board. They
        travel straight for a random number of road segments, then turn (in the direction of the street on which they
        land), then continue straight until they reach the end of the board.
        :return: origin coordinates, destination coordinates, route (which is a list of [direction, num_segments]
        lists). direction can be either 'up', 'down', 'left', or 'right'.
        '''
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
