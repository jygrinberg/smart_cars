from __future__ import print_function
from car import *
from protocol import *
import random
import time

class Simulator:
    def __init__(self, protocol, CarClass, num_cars, num_rounds, num_roads, random_seed=None):
        self.protocol = protocol
        self.num_cars = num_cars
        self.num_rounds = num_rounds
        self.num_roads = num_roads
        self.total_cost = 0

        # Set a global random seed, if specified.
        if random_seed is not None:
            random.seed(random_seed)

        # Initialize the cars.
        self.cars = []
        for car_id in xrange(self.num_cars):
            car = CarClass(car_id, self.protocol)
            self.cars.append(car)

    def run(self):
        # Run the simulation for num_rounds times.
        for round_id in xrange(self.num_rounds):
            # Initialize the state.
            game = State(self.cars, self.protocol, self.num_roads)
            game.printState(round_id, 0)

            # Simulate the round until all cars reach their destination.
            iteration_id = 0
            while not game.isEnd():
                game.updateState()
                iteration_id += 1
                game.printState(round_id, iteration_id)

            # Update the total cost.
            self.total_cost += game.getTotalCost()
            game.printState(round_id, iteration_id)
            print('TOTAL COST: %d' % self.total_cost)

    def getTotalCost(self):
        return self.total_cost


class State:
    """
    Street ids 1, 5, 9, etc. go down/right.
    Street ids 3, 7, 11, etc. go up/left.
    """

    def __init__(self, cars, protocol, num_roads):
        self.protocol = protocol

        # Initialize the board, which stores the number of cars at each (x,y) position.
        self.width = num_roads * 4 + 1
        self.height = num_roads * 4 + 1
        self.board = [[0] * self.height for _ in xrange(self.width)]

        # Initialize a trip for each car. Add each car to the board.
        self.cars = cars
        for car in self.cars:
            # Get the starting position, destination, and a route from origin to destination. The route is a list of
            # 'directions', where each direction is a tuple of the form ({'up', 'down', 'left', or 'right'}, num_steps).
            origin, destination, route = self._getRandomRoute()

            # Determine the queue number of the car. This number is greater than 0 if there are already cars at this
            # location.
            rank = self.board[origin[0]][origin[1]]
            self.board[origin[0]][origin[1]] += 1

            # Initialize the trip.
            car.initTrip(origin, rank, route, destination)

        # Initialize the total cost, and number of cars not yet arrived.
        self.total_cost = 0
        self.num_cars_travelling = len(cars)

    def updateState(self):
        # Increment the total weighted travel time and remove all the arrived cars from self.cars.
        travelling_cars = []
        for car in self.cars:
            if not car.hasArrived():
                self.total_cost += car.priority + 1
                travelling_cars.append(car)
        self.cars = travelling_cars

        # Determine the next position to which each car would *like* to move. next_positions maps next positions to
        # car_ids that to move to that position.
        next_positions = {}
        car_next_positions = {}
        for car in self.cars:
            next_position = car.getNextPosition()
            if next_position not in next_positions:
                next_positions[next_position] = set()
            next_positions[next_position].add(car)
            car_next_positions[car.car_id] = next_position

        # Resolve next_positions in order to determine which cars move. next_positions maps from car_id to the position
        # to which the car will move.
        win_positions = set()
        lose_positions = set()
        for next_position, cars in next_positions.iteritems():
            position_0 = None
            position_1 = None
            for car in cars:
                if position_0 is None:
                    position_0 = car.position
                    continue
                elif car.position != position_0:
                    position_1 = car.position
                    break

            # Compute the information given to each car when asking it for a decision. num_cars is number of cars at
            # the given position.
            num_cars = [0, 0]
            for car in cars:
                if car.position is position_0:
                    num_cars[0] += 1
                else:
                    num_cars[1] += 1

            # Get each car's action (i.e. move forward, if possible, or agree not to move). Actions maps car_id to that
            # car's action. actions_list is a list of votes at each position.
            actions = {}
            actions_list = [[], []]
            for car in cars:
                action = car.getAction(position_0, num_cars[0], position_1, num_cars[1])
                actions[car.car_id] = action
                if car.position is position_0:
                    actions_list[0].append(action)
                else:
                    actions_list[1].append(action)

            # Determine which position wins.
            win_position, lose_position = self.protocol.getWinLosePositions(position_0, actions_list[0], position_1,
                                                                            actions_list[1])

            # Store the win and lose positions.
            win_positions.add(win_position)
            if lose_position is not None:
                lose_positions.add(lose_position)
            
            # Reward cars.
            for car in cars:
                self.protocol.updateCarReward(car.car_id, car.position, win_position, actions[car.car_id], position_0,
                                              actions_list[0], position_1, actions_list[1])

        # Update the car ranks. moving_cars maps next_positions to cars that will move.
        moving_cars = {}
        for car in self.cars:
            if car.position in win_positions:
                # Car is in a winning position.
                if car.rank == 0:
                    # Car is first in the queue, so it moves forward. Append this car to next_position's queue.
                    next_position = car_next_positions[car.car_id]
                    moving_cars[next_position] = car
                    if next_position in lose_positions or next_position not in win_positions:
                        # The next position is a losing position, so the queue will get longer by 1.
                        car.rank = self.board[next_position[0]][next_position[1]]
                    else:
                        # The next position is a winning position, so the queue will remain the same length.
                        car.rank = self.board[next_position[0]][next_position[1]] - 1
                else:
                    # Car is not first in the queue, so it gets bumped up by 1.
                    car.rank -= 1

        # Inform cars that will move of their new positions, and update the board accordingly.
        for next_position, car in moving_cars.iteritems():
            self.board[car.position[0]][car.position[1]] -= 1
            car.updatePosition(next_position)
            self.board[next_position[0]][next_position[1]] += 1

        # Update number of cars travelling.
        self.num_cars_travelling = 0
        for car in self.cars:
            if not car.hasArrived():
                self.num_cars_travelling += 1

    def isEnd(self):
        return self.num_cars_travelling == 0

    def getTotalCost(self):
        return self.total_cost

    def _getRandomRoute(self):
        route = []
        side = random.choice(['top', 'left', 'bottom', 'right'])
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

    def printState(self, round_id, iteration_id):
        print('State: round=%d\titeration=%d' % (round_id, iteration_id))
        print('  ', end='')
        for x in xrange(self.width):
            if x % 4 == 3:
                print('n ', end='')
            else:
                print('  ', end='')
        print('')
        for y in xrange(self.height):
            if y % 4 == 3:
                print('<-', end='')
            else:
                print('  ', end='')

            for x in xrange(self.width):
                count = self.board[x][y]
                if x % 2 == 0 and y % 2 == 0:
                    count_string = ' '
                elif count == 0:
                    count_string = '.'
                else:
                    count_string = str(count)
                print('%s ' % count_string, end='')

            if y % 4 == 1:
                print('->', end='')
            else:
                print('  ', end='')
            print('')

        print('  ', end='')
        for x in xrange(self.width):
            if x % 4 == 1:
                print('v ', end='')
            else:
                print('  ', end='')
        print('')