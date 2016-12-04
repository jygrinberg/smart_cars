from abc import ABCMeta, abstractmethod
import random


class Protocol(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        # Initialize a map from car_id to total reward.
        self.rewards = {}
        self.fixed_cost = None
        self.initial_reward = 0.0

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

    def setSimulationParams(self, fixed_cost):
        """
        Set parameters specific to the simulation.
        :param fixed_cost: Cost per car per iteration (aside from the car's priority).
        :return:
        """
        self.fixed_cost = fixed_cost

    def getCarReward(self, car_id):
        """
        Returns the total reward accrued for the specified car (initialized to self.initial_reward).
        :param car_id: Car for which to return the total reward.
        :return: Float reward value.
        """
        if car_id in self.rewards:
            return self.rewards[car_id]
        return self.initial_reward

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
        # Arbitrarily pick a reward.
        reward = random.randint(0, 1)
        if car_id not in self.rewards:
            self.rewards[car_id] = self.initial_reward
        self.rewards[car_id] += reward
        return reward

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
        position_0_bids = sum(actions_0) + len(actions_0) * self.fixed_cost
        position_1_bids = sum(actions_1) + len(actions_1) * self.fixed_cost
        bid_difference = abs(position_0_bids - position_1_bids)

        reward = 0.0
        if self.voting_externality and self.fixed_cost == 1.0:
            # Compute externality as the social welfare to everyone else if a given agent were present but voted
            # differently.
            if bid_difference == 0:
                # Conflict was a tie.
                if car_action == 1:
                    # Car would have lost had it bid 0.
                    reward = -1.0
                elif car_action == 0:
                    # Car would have won had it bid non-zero.
                    reward = 1.0
            elif bid_difference == 1:
                # One side won by one vote.
                if position == win_position and car_action == 1:
                    # Car won, but it would have tied had it bid 0.
                    reward = -1.0
                elif position != win_position and car_action == 0:
                    # Car lost, but it would have tied had it bid 1.
                    reward = 1.0
        elif self.voting_externality:
            # Compute externality as the social welfare to everyone else if a given agent were present but voted
            # differently.
            if bid_difference == 0:
                # Conflict was a tie.
                if car_action == 1:
                    # Car would have lost had it bid 0.
                    reward = -0.5
                elif car_action == 0:
                    # Car would have won had it bid 1.
                    reward = 0.5
            elif position == win_position:
                # Car was in the winning position.
                if bid_difference < car_action:
                    # Car would have lost had it bid 0.
                    reward = -1.0
                elif bid_difference == car_action:
                    # Car would have tied had it bid 0.
                    reward = -0.5
            else:
                # Car was in the losing position.
                if bid_difference < car_action:
                    # Car would have won had it bid 1.
                    reward = 1.0
                elif bid_difference == car_action:
                    # Car would have tied had it bid 1.
                    reward = 0.5
        else:
            # Set to False to compute externality as the social welfare to everyone had a given agent not been present.
            if position == win_position and car_action == 1:
                # Car in winning position and car's action is 1.
                if bid_difference == 0:
                    # Car would have lost had it acted differently.
                    reward = -1.0
                elif bid_difference == 1:
                    # Car would have tied had it acted differently.
                    reward = -0.5
            elif position != win_position and car_action == 0:
                # Car in losing position and car's action is 0.
                if bid_difference == 0:
                    # Car would have won had it acted differently.
                    reward = 1.0
                elif bid_difference == 1:
                    # Car would have tied had it acted differently.
                    reward = 0.5

        if car_id not in self.rewards:
            self.rewards[car_id] = self.initial_reward
        self.rewards[car_id] += reward
        return reward

    def __str__(self):
        return 'vcg'