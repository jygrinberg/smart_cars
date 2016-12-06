from __future__ import print_function
from car import *
from protocol import *
from configurer import *
from animator import *
import time
import util
from collections import deque

class Simulator:
    def __init__(self, protocol, CarClass, MyCarClass, num_rounds, fixed_cost, unlimited_reward, animate, config):
        """
        :param fixed_cost: Cost per car per iteration (aside from the car's priority).
        :param unlimited_reward: Initialize cars with infinite reward so that they can bid 1.0 whenever desired.
        """
        self.protocol = protocol
        self.num_rounds = num_rounds
        self.fixed_cost = fixed_cost

        self.config = config
        self.num_cars = self.config.num_cars
        self.num_roads = self.config.num_roads

        self.protocol.setSimulationParams(self.fixed_cost, self.num_cars, unlimited_reward,
                                          self.config.high_priority_probability)

        # Store cost and reward stats from the simulation.
        # * simulation_costs is a list of the total cost per round.
        # * simulation_rewards is a list of the total reward per round.
        # * my_car_costs is a list of my_car's cost per round.
        # * my_car_rewards is a list of my_car's reward per round.
        self.simulation_costs = []
        self.simulation_rewards = []
        self.my_car_costs = []
        self.my_car_rewards = []

        # Initialize the cars. If MyCarClass is not None, make one of the cars MyCarClass.
        self.cars = []
        self.my_car = None
        num_car_class = self.num_cars
        if MyCarClass is not None:
            num_car_class -= 1
            self.my_car = MyCarClass(self.num_cars - 1, self.protocol)
            self.cars.append(self.my_car)
        for car_id in xrange(num_car_class):
            car = CarClass(car_id, self.protocol)
            self.cars.append(car)
        random.shuffle(self.cars)

        self.animator = None
        if animate:
            self.animator = Animator(500, self.config.height, self.num_cars, self.fixed_cost, self.my_car)

    def run(self):
        if self.animator:
            self.animator.initAnimation(str(self.protocol), str(self.cars[0]))

        # Run the simulation for num_rounds times.
        for round_id in xrange(self.num_rounds):
            # Initialize the game.
            game = GameState(self.cars, self.protocol, self.fixed_cost, self.config, round_id, self.my_car)
            game.printState(round_id, 0)
            if self.animator:
                self.animator.initRound(game.board, game.cost_board, round_id, 0)

            # Simulate the round until all cars reach their destinations.
            iteration_id = 0
            while not game.isEnd():
                game.updateState()
                iteration_id += 1
                game.printState(round_id, iteration_id)
                if self.animator:
                    self.animator.updateAnimation(game.board, game.cost_board, game.win_next_positions, round_id,
                                                  iteration_id, game.total_cost)

            # Keep track of stats from the round.
            self.simulation_costs.append(game.total_cost)
            self.simulation_rewards.append(self.protocol.getTotalReward(self.num_cars))
            if self.my_car is not None:
                self.my_car_costs.append(game.my_car_cost)
                self.my_car_rewards.append(self.protocol.getCarReward(self.my_car.car_id))

            game.printState(round_id, iteration_id)
            print('Round %d\tTotal reward = %.3f\tTotal cost = %.3f' % (round_id, self.simulation_rewards[-1],
                                                                        self.simulation_costs[-1]))
            if self.my_car is not None:
                print('\tMy car reward = %.3f\tMy car cost = %.3f' % (self.my_car_rewards[-1], self.my_car_costs[-1]))
        print('TOTAL MEAN COST: %.3f\tTOTAL MEAN COST PER CAR: %.3f\tMY CAR COST: %.3f' %
              (self.getMeanCost(), self.getMeanCost() / self.num_cars, self.getMyCarMeanCost()))

    def getMeanCost(self):
        '''
        Returns the total mean cost of all cars over all the rounds.
        '''
        return sum(self.simulation_costs) / float(self.num_rounds)

    def getMeanReward(self):
        '''
        Returns the total mean reward of all cars over all the rounds.
        '''
        return sum(self.simulation_rewards) / float(self.num_rounds)

    def getMyCarMeanCost(self):
        '''
        Returns the mean cost of my_car over all the rounds.
        '''
        return sum(self.my_car_costs) / float(self.num_rounds)

    def getMyCarMeanReward(self):
        '''
        Returns the mean reward of my_car over all the rounds.
        '''
        return sum(self.my_car_rewards) / float(self.num_rounds)


class GameState:
    """
    Street ids 1, 5, 9, etc. go down/right.
    Street ids 3, 7, 11, etc. go up/left.
    """

    def __init__(self, cars, protocol, fixed_cost, config, round_id, my_car):
        self.protocol = protocol
        self.fixed_cost = fixed_cost
        self.config = config
        self.my_car = my_car

        # Initialize the board, which stores queues of cars at each (x,y) position
        self.board = [[deque() for _ in xrange(self.config.height)] for _ in xrange(self.config.width)]

        # Initialize the board storing the total cost at each (x,y) position in the board.
        self.cost_board = [[0] * self.config.height for _ in xrange(self.config.width)]

        # List of tuples of the form (win_position, next_position), where win_position is a position that won in the
        # latest iteration, and next_position is the position to which the car there moved.
        self.win_next_positions = []

        # Initialize a trip for each car. Add each car to the board.
        self.cars = cars
        for car in self.cars:
            # Get the starting position, destination, route from origin to destination, and priority for the trip. The
            # route is a list of 'directions', where each direction is a tuple of the form ({'up', 'down', 'left', or
            # 'right'}, num_steps).
            origin, destination, route, priority = self.config.getNextCarTrip(round_id, car.car_id)

            # Initialize the car's trip.
            car.initTrip(origin, destination, route, priority)

            # Add the car to the board.
            self.board[origin[0]][origin[1]].append(car)
            self.cost_board[origin[0]][origin[1]] += self.fixed_cost + car.priority

        # Initialize the total cost, and number of cars not yet arrived.
        self.total_cost = 0.0
        self.my_car_cost = 0.0
        self.num_cars_travelling = len(cars)

        # Call the protocol functions that need to be called if the protocol involves fixed actions per round.
        if self.protocol.fixed_actions_per_round:
            self.protocol.initRound(round_id)
            for car in self.cars:
                self.protocol.setCarRoundAction(car.car_id, car.getAction(car.position, 1, None, 0))

    def updateState(self):
        '''
        Runs one iteration of the simulation. Updates self.board and self.cost_board to reflect the new state of the
        simulation. Also updates self.win_next_positions with a list of (win_position, next_position) tuples.
        '''
        # Increment the total weighted travel time and remove all the arrived cars from self.cars.
        travelling_cars = []
        for car in self.cars:
            if not car.hasArrived():
                car_cost = car.priority + self.fixed_cost
                self.total_cost += car_cost
                travelling_cars.append(car)
        self.cars = travelling_cars
        if self.my_car is not None and not self.my_car.hasArrived():
            self.my_car_cost += self.my_car.priority + self.fixed_cost

        # Determine the next position to which each car would *like* to move.
        # * next_positions is a dictionary. Key is next_position. Value is a set of car_ids wanting to move there.
        # * car_next_positions is a dictionary. Key is car_id. Value is its desired next position.
        next_positions = {}
        car_next_positions = {}
        for car in self.cars:
            next_position = car.getNextPosition()
            if next_position not in next_positions:
                next_positions[next_position] = set()
            next_positions[next_position].add(car)
            car_next_positions[car.car_id] = next_position

        # Resolve the conflicts in order to determine which cars move.
        # * win_positions are sets containing positions with at least one car that won.
        win_positions = set()
        for next_position, cars in next_positions.iteritems():
            # Arbitrarily set one position in the conflict as position_0, and the other (if it exists) as position_1.
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
            # the given position corresponding to the index.
            num_cars = [0, 0]
            for car in cars:
                if car.position == position_0:
                    num_cars[0] += 1
                else:
                    num_cars[1] += 1

            # Get each car's action (i.e. move forward, if possible, or agree not to move).
            # * actions is a dictionary. Key is car_id. Value is the car's action.
            # * actions_list is a list of actions for each position.
            # * actions_car_id_list is a list of car_ids for each position.
            actions = {}
            actions_list = [[], []]
            for car in cars:
                if self.protocol.fixed_actions_per_round:
                    action = self.protocol.getCarRoundAction(car.car_id)
                else:
                    action = car.getAction(position_0, num_cars[0], position_1, num_cars[1])
                actions[car.car_id] = action
                if car.position == position_0:
                    actions_list[0].append(action)
                else:
                    actions_list[1].append(action)

            # Determine which position wins.
            win_position, lose_position = self.protocol.getWinLosePositions(position_0, actions_list[0], position_1,
                                                                            actions_list[1])

            # Store the win and lose positions.
            win_positions.add(win_position)

            # Reward cars.
            for car in cars:
                self.protocol.updateCarReward(car.car_id, car.position, win_position, actions[car.car_id], position_0,
                                              actions_list[0], position_1, actions_list[1])

        # Move the cars that are first in the queues in the winning positions. Inform these cars of their new positions.
        # Also, populate win_next_positions.
        self.win_next_positions = []
        for position in win_positions:
            moving_car = self.board[position[0]][position[1]].popleft()
            next_position = car_next_positions[moving_car.car_id]
            moving_car.updatePosition(next_position)
            self.board[next_position[0]][next_position[1]].append(moving_car)
            self.win_next_positions.append((position, next_position))

        # Update number of cars travelling and update self.cost_board to reflect the total cost of cars at each
        # location in the board.
        self.num_cars_travelling = 0
        for car in self.cars:
            if not car.hasArrived():
                self.num_cars_travelling += 1
                self.cost_board[car.position[0]][car.position[1]] += car.priority + self.fixed_cost

    def isEnd(self):
        return self.num_cars_travelling == 0

    def printState(self, round_id, iteration_id):
        if util.VERBOSE:
            print('State: round=%d\titeration=%d' % (round_id, iteration_id))
            print('  ', end='')
            for x in xrange(self.config.width):
                if x % 4 == 3:
                    print('n ', end='')
                else:
                    print('  ', end='')
            print('')
            for y in xrange(self.config.height):
                if y % 4 == 3:
                    print('<-', end='')
                else:
                    print('  ', end='')

                for x in xrange(self.config.width):
                    count = len(self.board[x][y])
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
            for x in xrange(self.config.width):
                if x % 4 == 1:
                    print('v ', end='')
                else:
                    print('  ', end='')
            print('')