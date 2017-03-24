from abc import ABCMeta, abstractmethod
import random
import util
import copy

class Protocol(object):
    '''
    If self.fixed_actions_per_round is True, then the functions initRound() and setCarRoundAction() are called at the
    beginning of each round, and getCarRoundAction() is called instead of calling the car's getAction() when determining
    cars' actions at each conflict.
    '''
    __metaclass__ = ABCMeta

    def __init__(self, config):
        self.config = config
        self.rewards = {}
        self.initial_reward = 0.0
        self.unlimited_reward = config.force_unlimited_reward
        self.fixed_actions_per_round = False

        # Initialize a map from car_id to the car's reward.
        for car_id in xrange(self.config.num_cars):
            self.rewards[car_id] = self.initial_reward

    @abstractmethod
    def getWinPosition(self, position_0, actions_0, position_1, actions_1, game_state):
        """
        Identifies the 'winning' position in the conflict (the first car in the winning position is the one that gets to
        proceed into the intersection). Cars in the 'losing' position in the conflict do not move.
        :param position_0: (x,y) tuple coordinates of one of the positions involved in the conflict.
        :param actions_0: List of actions for each car in position_0.
        :param position_1: (x,y) tuple coordinates of one of the positions involved in the conflict.
        :param actions_1: List of actions for each car in position_1.
        :param game_state: GameState object storing the state of the simulation for the current round.
        :return: Winning position (x,y), losing position  (x,y)
        """
        pass

    @abstractmethod
    def updateCarReward(self, car_id, position, win_position, car_action, position_0, actions_0, position_1, actions_1):
        """
        Computes and stores the reward (if any) for the car at the given position based on the results of the conflict.
        :param car_id: Car that will be rewarded.
        :param position: (x,y) tuple coordinates of the current position of the car for whom to compute a reward.
        :param win_position: (x,y) tuple coordinates of the position that won the conflict.
        :param car_action: Action the car took.
        :param position_0: (x,y) tuple coordinates of one of the positions involved in the conflict.
        :param actions_0: List of actions for each car in position_0.
        :param position_1: (x,y) tuple coordinates of one of the positions involved in the conflict.
        :param actions_1: List of actions for each car in position_1.
        :return: Float reward value.
        """
        pass

    @abstractmethod
    def __str__(self):
        pass

    def initRound(self, round_id):
        """
        This is called at the beginning of the round for each car.
        :return:
        """
        pass

    def setCarRoundAction(self, car_id, action):
        """
        This is called at the beginning of the round for each car.
        :return:
        """
        pass

    def getCarRoundAction(self, car_id):
        """
        This is called for each car involved with each conflict.
        :return:
        """
        pass

    def canCarBidHigh(self, car_id):
        """
        Returns true if car_id has enough reward to bid high.
        :param car_id: Car for which to return true or false.
        :return: True or False.
        """
        return self.unlimited_reward or self.rewards[car_id] > 0

    def getCarReward(self, car_id):
        """
        Returns the total reward accrued for the specified car (initialized to self.initial_reward).
        :param car_id: Car for which to return the total reward.
        :return: Float reward value.
        """
        if car_id not in self.rewards:
            raise Exception('car_id %d not in the protocol\'s reward dict' % car_id)
        return self.rewards[car_id]

    def getTotalReward(self, num_cars):
        """
        Returns the total reward summed across all cars.
        :return: Float of total reward.
        """
        sum = 0
        for car_id in xrange(num_cars):
            if car_id in self.rewards:
                sum += self.rewards[car_id]
            else:
                sum += self.initial_reward
        return sum

    def _getOptimalWinPosition(self, position_0, actions_0, position_1, actions_1, game_state, num_iterations=1):
        """
        :param num_iterations: Number of iterations to simulate when computing optimal win position.
        """
        if position_1 is None:
            # There is no conflict.
            return position_0

        win_position = position_0

        if num_iterations == 1:
            # Total bid is total cost of the queue assuming truthful actions.
            position_0_bids = sum(actions_0) * self.config.high_cost + len(actions_0) - sum(actions_0)
            position_1_bids = sum(actions_1) * self.config.high_cost + len(actions_1) - sum(actions_1)

            # Winner is the position with a higher bid. Ties are broken randomly.
            if position_0_bids > position_1_bids or \
                    (position_0_bids == position_1_bids and random.choice([True, False])):
                win_position = position_0
            else:
                win_position = position_1
        else:
            def getExternality(game_state, iteration, position):
                # Keep a pointer to the main simulation's protocol.
                old_protocol = game_state.config.protocol
                game_state.config.protocol = RandomProtocol(game_state.config)

                # Compute externality.
                cost = getExternalityRec(game_state, iteration, position)

                # Set game_state's protocol back to the original protocol.
                game_state.config.protocol = old_protocol
                return cost

            def getExternalityRec(curr_game_state, num_iterations, position):
                # Create a copy of the game that will be simulated using RandomProtocol.
                game = curr_game_state.getCopy(position, num_iterations)

                my_car = game.board[position[0]][position[1]][0]
                if my_car.hasArrived():
                    return 0

                competing_position = util.getCompetingPosition(position)
                cost = util.getQueueCost(game.board[competing_position[0]][competing_position[1]],
                                         self.config.high_cost)
                self_cost = util.getCarCost(game.board[position[0]][position[1]][0], self.config.high_cost)
                self_queue_cost = util.getQueueCost(game.board[position[0]][position[1]], self.config.high_cost)

                # Force my_car to win in the first iteration.
                force_win = True
                force_lose = False

                for curr_iteration in xrange(num_iterations):
                    # Simulate one iteration of the game. If this is the first simulated round, let position_a win.
                    if force_win:
                        game.updateState(automatic_win_position=position)
                    elif force_lose:
                        game.updateState(automatic_lose_position=position)
                    else:
                        game.updateState()
                    force_win = False
                    force_lose = False

                    if my_car.hasArrived():
                        break

                    # If the car is not first in a queue, the cost is infinite.
                    if game.board[my_car.position[0]][my_car.position[1]][0] is not my_car:
                        # return float('inf')
                        cost += self_queue_cost
                        continue

                    # If the car is is in conflict with a non-empty queue, determine whether it proceeds or waits for an
                    # iteration.
                    if not util.isIntersection(my_car.position):
                        competing_position = util.getCompetingPosition(my_car.position)
                        if util.isInBounds(competing_position, game.board) and \
                                        len(game.board[competing_position[0]][competing_position[1]]) > 0:
                            # Car is in a conflict with a non-empty queue.
                            cost += util.getQueueCost(game.board[competing_position[0]][competing_position[1]],
                                                      game.config.high_cost)
                            # continue
                            externality = getExternality(game, num_iterations - curr_iteration - 1, my_car.position)
                            competing_externality = getExternality(game, num_iterations - curr_iteration - 1,
                                                                   competing_position)

                            if externality > competing_externality or \
                                    (externality == competing_externality and random.choice([True, False])):
                                # Car remains where it is.
                                force_lose = True
                                continue
                            else:
                                # Car proceeds. Add the cost of the competing queue.
                                force_win = True
                                cost += util.getQueueCost(game.board[competing_position[0]][competing_position[1]],
                                                          game.config.high_cost)

                return cost

            position_0_cost = getExternality(game_state, num_iterations, position_0)
            position_1_cost = getExternality(game_state, num_iterations, position_1)

            # Winner is the position with a lower bid. Ties are broken randomly.
            if position_0_cost < position_1_cost or \
                    (position_0_cost == position_1_cost and random.choice([True, False])):
                win_position = position_0
            else:
                win_position = position_1

        return win_position


class RandomProtocol(Protocol):
    """
    This is a baseline protocol that makes random decisions.
    """

    def __init__(self, config):
        super(RandomProtocol, self).__init__(config)
        # Set reward to unlimited in order to make everything completely random.
        self.unlimited_reward = True

    def getWinPosition(self, position_0, actions_0, position_1, actions_1, game_state):
        if position_1 is None:
            return position_0

        # If only one position has cars, pick that position.
        if len(actions_0) > 0 and len(actions_1) == 0:
            return position_0
        elif len(actions_1) > 0 and len(actions_0) == 0:
            return position_1

        # Otherwise, arbitrarily pick win and lose positions.
        if random.choice([True, False]):
            return position_0
        return position_1

    def updateCarReward(self, car_id, position, win_position, car_action, position_0, actions_0, position_1, actions_1):
        return 0

    def __str__(self):
        return 'random'

class VCGProtocol(Protocol):
    """
    This is a protocol making use of a VCG auction.
    """

    def __init__(self, config, voting_externality=True):
        '''
        :param voting_externality: Set to True to compute externality as the social welfare to everyone else if a given
        agent were present but voted differently. Set to False to compute externality as the social welfare to everyone
        had a given agent not been present.
        '''
        super(VCGProtocol, self).__init__(config)
        self.voting_externality = voting_externality

    def getWinPosition(self, position_0, actions_0, position_1, actions_1, game_state):
        return self._getOptimalWinPosition(position_0, actions_0, position_1, actions_1, game_state)

    def updateCarReward(self, car_id, position, win_position, car_action, position_0, actions_0, position_1, actions_1):
        if position_1 is None:
            # No conflict occurred.
            return 0

        # Total bid is total cost of the queue assuming truthful actions.
        position_0_bids = sum(actions_0) * self.config.high_cost + len(actions_0) - sum(actions_0)
        position_1_bids = sum(actions_1) * self.config.high_cost + len(actions_1) - sum(actions_1)

        if position == position_0:
            car_position_bids = position_0_bids
            other_position_bids = position_1_bids
        else:
            car_position_bids = position_1_bids
            other_position_bids = position_0_bids

        bid_difference = abs(position_0_bids - position_1_bids)

        # Compute everyone else's total utility had car not been present.
        utility_without_car = abs(other_position_bids - (car_position_bids -
                                                         (car_action * self.config.high_cost + 1.0 - car_action)))

        # Compute everyone else's total utility given that car was present.
        utility_with_car = abs(other_position_bids - car_position_bids)
        if position == win_position:
            # Car won, so we remove the car's utility by subtracting its utility.
            utility_with_car -= car_action * self.config.high_cost + 1.0 - car_action
        else:
            # Car lost, so we remove the car's utility by adding its utility.
            utility_with_car += car_action * self.config.high_cost + 1.0 - car_action

        externality = utility_without_car - utility_with_car

        reward = -externality
        # reward = 0.0
        # if self.voting_externality and self.fixed_cost == 1.0:
        #     # Compute externality as the social welfare to everyone else if a given agent were present but voted
        #     # differently.
        #     if bid_difference == 0:
        #         # Conflict was a tie.
        #         if car_action == 1:
        #             # Car would have lost had it bid 0.
        #             reward = -1.0
        #         elif car_action == 0:
        #             # Car would have won had it bid non-zero.
        #             reward = 1.0
        #     elif bid_difference == 1:
        #         # One side won by one vote.
        #         if position == win_position and car_action == 1:
        #             # Car won, but it would have tied had it bid 0.
        #             reward = -1.0
        #         elif position != win_position and car_action == 0:
        #             # Car lost, but it would have tied had it bid 1.
        #             reward = 1.0
        # elif self.voting_externality:
        #     # Compute externality as the social welfare to everyone else if a given agent were present but voted
        #     # differently.
        #     if bid_difference == 0:
        #         # Conflict was a tie.
        #         if car_action == 1:
        #             # Car would have lost had it bid 0.
        #             reward = -0.5
        #         elif car_action == 0:
        #             # Car would have won had it bid 1.
        #             reward = 0.5
        #     elif position == win_position:
        #         # Car was in the winning position.
        #         if bid_difference < car_action:
        #             # Car would have lost had it bid 0.
        #             reward = -1.0
        #         elif bid_difference == car_action:
        #             # Car would have tied had it bid 0.
        #             reward = -0.5
        #     else:
        #         # Car was in the losing position.
        #         if bid_difference < car_action:
        #             # Car would have won had it bid 1.
        #             reward = 1.0
        #         elif bid_difference == car_action:
        #             # Car would have tied had it bid 1.
        #             reward = 0.5
        # else:
        #     # Set to False to compute externality as the social welfare to everyone had a given agent not been present.
        #     if position == win_position and car_action == 1:
        #         # Car in winning position and car's action is 1.
        #         if bid_difference == 0:
        #             # Car would have lost had it not been present.
        #             reward = -1.0
        #         elif bid_difference == 1 + self.fixed_cost:
        #             # Car would have tied had it acted differently.
        #             reward = -0.5
        #     elif position != win_position and car_action == 0:
        #         # Car in losing position and car's action is 0.
        #         if bid_difference == 0:
        #             # Car would have won had it acted differently.
        #             reward = 1.0
        #         elif bid_difference == 1:
        #             # Car would have tied had it acted differently.
        #             reward = 0.5

        self.rewards[car_id] += reward
        return reward

    def __str__(self):
        return 'vcg'

class ButtonProtocol(Protocol):
    """
    This protocol allows each car to signal high priority as long as at least self.num_rounds_latency rounds rounds
    have elapsed since the last time the car signalled high priority.
    """

    def __init__(self, config):
        super(ButtonProtocol, self).__init__(config)

        self.fixed_actions_per_round = True

        # Initialize a dictionary. Key is car_id. Value is the car's action for the round.
        self.car_round_actions = {}

        # Number of rounds car has to wait after it bids 1 until it can bid 1 again.
        self.num_rounds_latency = int(1 / self.config.high_priority_probability)

        # Initialize a map from car_id to the car's reward with *random* values.
        for car_id in xrange(self.config.num_cars):
            self.rewards[car_id] = random.randrange(-self.num_rounds_latency + 1, 2)

    def initRound(self, round_id):
        self.car_round_actions.clear()

        for car_id in self.rewards:
            self.rewards[car_id] += 1

    def setCarRoundAction(self, car_id, action):
        self.car_round_actions[car_id] = action
        if action == 1:
            # Reset the reward to -self.num_rounds_latency + 1 so that the car will be able to bid high again in another
            # self.num_rounds_latency rounds.
            self.rewards[car_id] = -self.num_rounds_latency + 1

    def getCarRoundAction(self, car_id):
        if car_id not in self.car_round_actions:
            raise Exception('No action found for car_id=%d' % car_id)
        return self.car_round_actions[car_id]

    def getWinPosition(self, position_0, actions_0, position_1, actions_1, game_state):
        return self._getOptimalWinPosition(position_0, actions_0, position_1, actions_1, game_state)

    def updateCarReward(self, car_id, position, win_position, car_action, position_0, actions_0, position_1, actions_1):
        # Reward is only updated at the beginning of each round.
        return self.rewards[car_id]

    def __str__(self):
        return 'button'


class OptimalProtocol(Protocol):
    """
    This is an optimal greedy protocol assuming truthful cars.
    """

    def __init__(self, config, num_iterations=1):
        super(OptimalProtocol, self).__init__(config)
        # Set reward to unlimited in order to make locally optimal choices.
        self.unlimited_reward = True
        self.num_iterations = num_iterations

    def getWinPosition(self, position_0, actions_0, position_1, actions_1, game_state):
        return self._getOptimalWinPosition(position_0, actions_0, position_1, actions_1, game_state,
                                           self.num_iterations)

    def updateCarReward(self, car_id, position, win_position, car_action, position_0, actions_0, position_1, actions_1):
        return 0

    def __str__(self):
        return 'greedy'


class GeneralizedGreedyProtocol0(OptimalProtocol):
    num_iterations = 0
    def __init__(self, config):
        self.num_iterations = 0
        super(GeneralizedGreedyProtocol0, self).__init__(config, num_iterations=self.num_iterations)

    def __str__(self):
        return 'greedy_externality_%d' % self.num_iterations


class GeneralizedGreedyProtocol2(OptimalProtocol):
    num_iterations = 0
    def __init__(self, config):
        self.num_iterations = 2
        super(GeneralizedGreedyProtocol2, self).__init__(config, num_iterations=self.num_iterations)

    def __str__(self):
        return 'greedy_externality_%d' % self.num_iterations


class GeneralizedGreedyProtocol4(OptimalProtocol):
    num_iterations = 0
    def __init__(self, config):
        self.num_iterations = 4
        super(GeneralizedGreedyProtocol4, self).__init__(config, num_iterations=self.num_iterations)

    def __str__(self):
        return 'greedy_externality_%d' % self.num_iterations


class GeneralizedGreedyProtocol6(OptimalProtocol):
    num_iterations = 0
    def __init__(self, config):
        self.num_iterations = 6
        super(GeneralizedGreedyProtocol6, self).__init__(config, num_iterations=self.num_iterations)

    def __str__(self):
        return 'greedy_externality_%d' % self.num_iterations


class GeneralizedGreedyProtocol8(OptimalProtocol):
    num_iterations = 0
    def __init__(self, config):
        self.num_iterations = 8
        super(GeneralizedGreedyProtocol8, self).__init__(config, num_iterations=self.num_iterations)

    def __str__(self):
        return 'greedy_externality_%d' % self.num_iterations


class OptimalRandomProtocol(OptimalProtocol):
    """
    This protocol implements OptimalProtocol 50% of the time and RandomProtocol 50% of the time.
    """

    def getWinPosition(self, position_0, actions_0, position_1, actions_1, game_state):
        if position_1 is None:
            return position_0

        # If only one position has cars, pick that position.
        if len(actions_0) > 0 and len(actions_1) == 0:
            return position_0
        elif len(actions_1) > 0 and len(actions_0) == 0:
            return position_1

        optimal_probability = 0.5

        if random.random() < optimal_probability:
            # Pick an optimal choice.
            return super(OptimalRandomProtocol, self).getWinPosition(position_0, actions_0, position_1, actions_1,
                                                                     game_state)

        # Otherwise, arbitrarily pick win and lose positions.
        if random.choice([True, False]):
            return position_0
        return position_1
