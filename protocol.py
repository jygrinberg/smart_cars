from abc import ABCMeta, abstractmethod
import random


class Protocol(object):
    '''
    If self.fixed_actions_per_round is True, then the functions initRound() and setCarRoundAction() are called at the
    beginning of each round, and getCarRoundAction() is called instead of calling the car's getAction() when determining
    cars' actions at each conflict.
    '''
    __metaclass__ = ABCMeta

    def __init__(self):
        self.rewards = {}
        self.fixed_cost = None
        self.initial_reward = 0.0
        self.unlimited_reward = False
        self.fixed_actions_per_round = False

    @abstractmethod
    def getWinLosePositions(self, position_0, actions_0, position_1, actions_1):
        """
        Identifies the 'winning' position in the conflict (the first car in the winning position is the one that gets to
        proceed into the intersection), and the 'losing' position in the conflict (the cars in the losing position do
        not move).
        :param position_0: (x,y) tuple coordinates of one of the positions involved in the conflict.
        :param actions_0: List of actions for each car in position_0.
        :param position_1: (x,y) tuple coordinates of one of the positions involved in the conflict.
        :param actions_1: List of actions for each car in position_1.
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

    def setSimulationParams(self, fixed_cost, num_cars, unlimited_reward):
        """
        Set parameters specific to the simulation.
        :param fixed_cost: Cost per car per iteration (aside from the car's priority).
        :param number of cars in the simulation.
        :param unlimited_reward: If true, cars are allowed to bid 1 whenever they wayn.
        """
        self.fixed_cost = fixed_cost
        self.unlimited_reward = unlimited_reward

        # Initialize a map from car_id to the car's reward.
        for car_id in xrange(num_cars):
            self.rewards[car_id] = self.initial_reward

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

class RandomProtocol(Protocol):
    """
    This is a baseline protocol that makes random decisions.
    """
    def __init__(self):
        super(RandomProtocol, self).__init__()
        # Unlimited reward is always set to true in order to make everything completely random.
        self.unlimited_reward = True

    def getWinLosePositions(self, position_0, actions_0, position_1, actions_1):
        if position_1 is None:
            return position_0, position_1

        # If only one position has cars, pick that position.
        if len(actions_0) > 0 and len(actions_1) == 0:
            return position_0, position_1
        elif len(actions_1) > 0 and len(actions_0) == 0:
            return position_1, position_0

        # Otherwise, arbitrarily pick win and lose positions.
        if random.choice([True, False]):
            return position_0, position_1
        return position_1, position_0

    def updateCarReward(self, car_id, position, win_position, car_action, position_0, actions_0, position_1, actions_1):
        return 0

    def __str__(self):
        return 'random'

class VCGProtocol(Protocol):
    """
    This is a protocol making use of a VCG auction.
    """
    def __init__(self, voting_externality=True):
        '''
        :param voting_externality: Set to True to compute externality as the social welfare to everyone else if a given
        agent were present but voted differently. Set to False to compute externality as the social welfare to everyone
        had a given agent not been present.
        '''
        super(VCGProtocol, self).__init__()
        self.voting_externality = voting_externality

    def getWinLosePositions(self, position_0, actions_0, position_1, actions_1):
        if position_1 is None:
            # There is no conflict.
            return position_0, position_1

        # Total bid is the sum of each car's bid plus fixed cost.
        position_0_bids = sum(actions_0) + len(actions_0) * self.fixed_cost
        position_1_bids = sum(actions_1) + len(actions_1) * self.fixed_cost

        # Winner is the position with a higher bid. Ties are broken randomly.
        win_position = position_0
        lose_position = position_1
        if position_1_bids > position_0_bids or (position_0_bids == position_1_bids and random.choice([True, False])):
            win_position = position_1
            lose_position = position_0

        return win_position, lose_position

    def updateCarReward(self, car_id, position, win_position, car_action, position_0, actions_0, position_1, actions_1):
        if position_1 is None:
            # No conflict occurred.
            return 0

        position_0_bids = sum(actions_0) + len(actions_0) * self.fixed_cost
        position_1_bids = sum(actions_1) + len(actions_1) * self.fixed_cost

        if position == position_0:
            car_position_bids = position_0_bids
            other_position_bids = position_1_bids
        else:
            car_position_bids = position_1_bids
            other_position_bids = position_0_bids

        bid_difference = abs(position_0_bids - position_1_bids)

        # Compute everyone else's total utility had car not been present.
        utility_without_car = abs(other_position_bids - (car_position_bids - car_action - self.fixed_cost))

        # Compute everyone else's total utility given that car was present.
        utility_with_car = abs(other_position_bids - car_position_bids)
        if position == win_position:
            # Car won, so we remove the car's utility by subtracting its utility.
            utility_with_car -= car_action + self.fixed_cost
        else:
            # Car lost, so we remove the car's utility by adding its utility.
            utility_with_car += car_action + self.fixed_cost

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
    This is a protocol making use of a VCG auction.
    """
    def __init__(self):
        super(ButtonProtocol, self).__init__()

        self.fixed_actions_per_round = True

        # Number of rounds car has to wait after it bids 1 until it can bid 1 again.
        self.num_rounds_latency = 3

        # Initialize a dictionary. Key is car_id. Value is the car's action for the round.
        self.car_round_actions = {}

    def initRound(self, round_id):
        self.car_round_actions.clear()

        for car_id in self.rewards:
            self.rewards[car_id] += 1

    def setCarRoundAction(self, car_id, action):
        self.car_round_actions[car_id] = action
        if action == 1:
            self.rewards[car_id] = -self.num_rounds_latency

    def getCarRoundAction(self, car_id):
        if car_id not in self.car_round_actions:
            raise Exception('No action found for car_id=%d' % car_id)
        return self.car_round_actions[car_id]

    def getWinLosePositions(self, position_0, actions_0, position_1, actions_1):
        if position_1 is None:
            # There is no conflict.
            return position_0, position_1

        # Total bid is the sum of each car's bid plus fixed cost.
        position_0_bids = sum(actions_0) + len(actions_0) * self.fixed_cost
        position_1_bids = sum(actions_1) + len(actions_1) * self.fixed_cost

        # Winner is the position with a higher bid. Ties are broken randomly.
        win_position = position_0
        lose_position = position_1
        if position_1_bids > position_0_bids or (position_0_bids == position_1_bids and random.choice([True, False])):
            win_position = position_1
            lose_position = position_0

        return win_position, lose_position

    def updateCarReward(self, car_id, position, win_position, car_action, position_0, actions_0, position_1, actions_1):
        # Reward is only updated at the beginning of each round.
        return self.rewards[car_id]

    def __str__(self):
        return 'button'