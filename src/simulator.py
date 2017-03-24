from __future__ import print_function
from collections import deque
from configurer import *
from animator import *
import util


class Simulator:
    def __init__(self, config):
        """
        :param config: An instance of the Config class used to specify simulation parameters.
        """
        self.config = config

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
        num_car_class = self.config.num_cars
        if self.config.MyCarClass is not None:
            num_car_class -= 1
            self.my_car = self.config.MyCarClass(self.config.num_cars - 1, self.config.protocol)
            self.cars.append(self.my_car)
        for car_id in xrange(num_car_class):
            car = self.config.CarClass(car_id, self.config.protocol)
            self.cars.append(car)

        self.animator = None
        if self.config.animate:
            self.animator = Animator(500, self.config.height, self.config.num_cars, self.config.high_cost, self.my_car)

    def run(self):
        """
        Runs the simulation for self.num_rounds number of rounds. Computes the total cost and reward for all cars per
        round, and also the cost and reward for my_car per round (if the MyCarClass passed into the constructor was not
        None).
        """
        if self.config.num_rounds == 0 or self.config.num_cars == 0 or self.config.num_roads == 0:
            return

        if self.animator:
            self.animator.initAnimation(str(self.config.protocol), str(self.cars[0]))

        # Run the simulation for num_rounds times.
        for round_id in xrange(self.config.num_rounds):
            # Initialize the game.
            game = GameState(self.config, round_id, self.cars, self.my_car)
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
            self.simulation_costs.append(game.getCompetitiveRatio())
            self.simulation_rewards.append(self.config.protocol.getTotalReward(self.config.num_cars))
            if self.my_car is not None:
                self.my_car_costs.append(game.my_car_cost)
                self.my_car_rewards.append(self.config.protocol.getCarReward(self.my_car.car_id))

            game.printState(round_id, iteration_id)

            if util.VERBOSE >= 1:
                print('Round %d\tTotal reward = %.3f\tTotal cost = %.3f' % (round_id, self.simulation_rewards[-1],
                                                                            self.simulation_costs[-1]))
                if self.my_car is not None:
                    print('\tMy car reward = %.3f\tMy car cost = %.3f' % (self.my_car_rewards[-1],
                                                                          self.my_car_costs[-1]))
        if self.config.num_cars == 0:
            return
        print('CONFIGURATION: %s' % str(self.config))
        print('MEAN COST: %.3f\tMY CAR COST: %.3f' %
              (self.getMeanCost(), self.getMyCarMeanCost()))

    def getMeanCost(self):
        """
        Returns the mean cost per car per round.
        """
        return sum(self.simulation_costs) / float(self.config.num_rounds) #/ float(self.config.num_cars)

    def getMeanReward(self):
        """
        Returns the mean reward per car per round.
        """
        return sum(self.simulation_rewards) / float(self.config.num_rounds) / float(self.config.num_cars)

    def getMyCarMeanCost(self):
        """
        Returns the mean cost of my_car per round.
        """
        return sum(self.my_car_costs) / float(self.config.num_rounds)

    def getMyCarMeanReward(self):
        """
        Returns the mean reward of my_car per round.
        """
        return sum(self.my_car_rewards) / float(self.config.num_rounds)


class GameState:
    """
    This class manages the state of the road network when running the simulator. A new instance of this class should be
    created for reach round in the simulation.

    The road network is modeled as a grid of one-way streets.
    Street ids 1, 5, 9, etc. go down/right.
    Street ids 3, 7, 11, etc. go up/left.

    The road network (saved in self.board) is a matrix of queues, where the queue at each position represents the queue
    of cars waiting to progress through that position. The queues at intersections are allowed to have at most one car.
    The queues at road segments can have any number of cars.
    """

    def __init__(self, config, round_id, cars, my_car=None, init_new_trips=True):
        self.config = config
        self.my_car = my_car

        # Initialize the board, which stores queues of cars at each (x,y) position
        self.board = [[deque() for _ in xrange(self.config.height)] for _ in xrange(self.config.width)]

        # Initialize the board storing the total cost at each (x,y) position in the board.
        self.cost_board = [[0] * self.config.height for _ in xrange(self.config.width)]

        # List of tuples of the form (win_position, next_position), where win_position is a position that won in the
        # latest iteration, and next_position is the position to which the car there moved.
        self.win_next_positions = []

        # Initialize a trip for each car. Add each car to the board. Also, randomly shuffle the order of the cars.
        self.cars = cars
        if init_new_trips:
            random.shuffle(self.cars)
        for car in self.cars:
            position = car.position

            if init_new_trips:
                # Get the starting position, destination, route from origin to destination, and priority for the trip. The
                # route is a list of 'directions', where each direction is a tuple of the form ({'up', 'down', 'left', or
                # 'right'}, num_steps).
                origin, destination, route, priority = self.config.getNextCarTrip(round_id, car.car_id)
                position = origin

                # Initialize the car's trip.
                car.initTrip(origin, destination, route, priority)

            # Add the car to the board.
            self.board[position[0]][position[1]].append(car)
            self.cost_board[position[0]][position[1]] += self.getCarCost(car)

        # Call the protocol functions that need to be called if the protocol involves fixed actions per round.
        if init_new_trips and self.config.protocol.fixed_actions_per_round:
            self.config.protocol.initRound(round_id)
            for car in self.cars:
                self.config.protocol.setCarRoundAction(car.car_id, car.getAction(car.position, 1, None, 0))

        # Initialize the total cost, my_car cost, optimal cost, and number of cars not yet arrived.
        self.total_cost = 0.0
        self.my_car_cost = 0.0
        self.optimal_cost = sum([util.getCarOptimalCost(car, self.config.high_cost) for car in self.cars])
        self.num_cars_travelling = len(cars)

    def getCompetitiveRatio(self):
        return self.total_cost / self.optimal_cost

    def updateState(self, automatic_win_position=None, automatic_lose_position=None):
        """
        Runs one iteration of the simulation. Updates self.board and self.cost_board to reflect the new state of the
        simulation. Also updates self.win_next_positions with a list of (win_position, next_position) tuples.

        If automatic_win_position is not None, that position automatically wins. This is useful when simulating the
        effects of letting one car win.
        """
        # Increment the total weighted travel time and remove all the arrived cars from self.cars.
        travelling_cars = []
        for car in self.cars:
            if not car.hasArrived():
                self.total_cost += self.getCarCost(car)
                travelling_cars.append(car)
        self.cars = travelling_cars
        if self.my_car is not None and not self.my_car.hasArrived():
            self.my_car_cost += self.getCarCost(self.my_car)

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
                if self.config.protocol.fixed_actions_per_round:
                    action = self.config.protocol.getCarRoundAction(car.car_id)
                else:
                    action = car.getAction(position_0, num_cars[0], position_1, num_cars[1])
                actions[car.car_id] = action
                if car.position == position_0:
                    actions_list[0].append(action)
                else:
                    actions_list[1].append(action)

            # Determine which position wins.
            win_position = None
            if automatic_win_position and \
                    (automatic_win_position == position_0 or automatic_win_position == position_1):
                # An automatic_win_position was provided, and one of the positions in this conflict is
                # automatic_win_position.
                if automatic_win_position == position_0:
                    win_position = position_0
                else:
                    win_position = position_1
            if automatic_lose_position and \
                    (automatic_lose_position == position_0 or automatic_lose_position == position_1):
                # An automatic_lose_position was provided, and one of the positions in this conflict is
                # automatic_lose_position.
                if automatic_lose_position == position_0:
                    win_position = position_0
                else:
                    win_position = position_1
            else:
                win_position = self.config.protocol.getWinPosition(position_0, actions_list[0], position_1,
                                                                   actions_list[1], self)

            # Store the win position.
            win_positions.add(win_position)

            # Reward cars.
            for car in cars:
                self.config.protocol.updateCarReward(car.car_id, car.position, win_position, actions[car.car_id],
                                                     position_0, actions_list[0], position_1, actions_list[1])

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
                self.cost_board[car.position[0]][car.position[1]] += self.getCarCost(car)

    def isEnd(self):
        """
        Determines if the round is over (i.e. if all cars have reached their destinations).
        :return: True if the round is over.
        """
        return self.num_cars_travelling == 0

    def getCarCost(self, car):
        """
        Computes the cost of the specified car per iteration, which is high_cost if the car is high priority and 1.0
        otherwise.
        :param car: Car instance.
        :return: Car cost per iteration.
        """
        return self.config.high_cost * car.priority + 1 * (1 - car.priority)

    def getCopy(self, position, num_iterations=2):
        if util.isIntersection(position):
            raise Exception('Position passed into GameState.getCopy() cannot be an intersection.')

        positions = util.getPositionsWithinDistance(position, num_iterations)
        cars = []
        for position in positions:
            if util.isInBounds(position, self.board):
                cars += self._getCarCopies(position)

        # Get copies of all the cars relevant for a two iteration simulation.
        # cars = []
        #
        # cars += self._getCarCopies(position, 1)
        #
        # next_1_position = util.getNextPosition(position[0], position[1], 1)
        # cars += self._getCarCopies(next_1_position)
        #
        # next_2_position = util.getNextPosition(position[0], position[1], 2)
        # cars += self._getCarCopies(next_2_position, 3)
        #
        # competing_position = util.getCompetingPosition(next_2_position[0], next_2_position[1])
        # cars += self._getCarCopies(competing_position)
        #
        # competing_1_position = util.getNextPosition(competing_position[0], competing_position[1], -1)
        # cars += self._getCarCopies(competing_1_position)
        #
        # competing_2_position = util.getNextPosition(competing_position[0], competing_position[1], -2)
        # cars += self._getCarCopies(competing_2_position, 1)
        #
        # competing_2_competing_position = util.getCompetingPosition(competing_2_position[0],
        #                                                                 competing_2_position[1])
        # cars += self._getCarCopies(competing_2_competing_position, 1)

        return GameState(self.config, 0, cars, init_new_trips=False)

    def printState(self, round_id, iteration_id):
        """
        Prints the number of cars at each position in the board.
        :param round_id: Round ID number.
        :param iteration_id: Iteration ID number.
        """
        if util.VERBOSE >= 2:
            print('State: round=%d\iteration=%d' % (round_id, iteration_id))
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


    def _getCarCopies(self, position, max_num_cars=None):
        if not util.isInBounds(position, self.board):
            return []

        cars = []
        if max_num_cars is None:
            max_num_cars = len(self.board[position[0]][position[1]])
        for i in xrange(min(len(self.board[position[0]][position[1]]), max_num_cars)):
            car = copy.deepcopy(self.board[position[0]][position[1]][i])
            cars.append(car)
        return cars
