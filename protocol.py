from abc import ABCMeta, abstractmethod
import random


class Protocol(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        # Initialize a map from car_id to total reward.
        self.rewards = {}

    @abstractmethod
    def getWinLosePositions(self, position_0, actions_0, position_1, actions_1):
        """
        Identifies the 'winning' position in the conflict (the first car in the winning position is the one that gets to
        proceed into the intersection), and the 'losing' position in the conflict (the cars in the losing position do
        not move).
        TODO
        :return: Winning position (x,y), losing position  (x,y)
        """
        pass

    @abstractmethod
    def updateCarReward(self, car_id, position, win_position, car_action, position_0, actions_0, position_1, actions_1):
        """
        Computes and stores the reward (if any) for the car at the given position based on the results of the conflict.
        :param car_id: Car that will be rewarded.
        :param position: Current position of the car for whom to compute a reward.
        :param win_position: Position that won the conflict.
        TODO
        :return: Float reward value.
        """
        pass

    def getCarReward(self, car_id):
        """
        Returns the total reward accrued for the specified car (initialized to 0).
        :param car_id: Car for which to return the total reward.
        :return: Float reward value.
        """
        if car_id in self.rewards:
            return self.rewards[car_id]
        return 0.0


class RandomProtocol(Protocol):
    """
    This is a placeholder protocol that makes random decisions.
    """
    def getWinLosePositions(self, position_0, actions_0, position_1, actions_1):
        # Arbitrarily pick win and lose positions.
        if random.choice([True, False]):
            return position_0, position_1
        return position_1, position_0

    def updateCarReward(self, car_id, position, win_position, car_action, position_0, actions_0, position_1, actions_1):
        # Arbitrarily pick a reward.
        reward = random.randint(0, 1)
        if car_id not in self.rewards:
            self.rewards[car_id] = 0
        self.rewards[car_id] += reward
        return reward


class VCGProtocol(Protocol):
    """
    This is a protocol making use of a VCG auction.
    """
    def getWinLosePositions(self, position_0, actions_0, position_1, actions_1):
        # Total bid is the sum of actions (each action is 0 or 1) plus the number of bidders (because cost per car is
        # 1 or 2).
        position_0_bids = sum(actions_0) + len(actions_0)
        position_1_bids = sum(actions_1) + len(actions_1)

        # Winner is the position with a higher bid. Ties are broken randomly.
        win_position = position_0
        lose_position = position_1
        if position_1_bids > position_0_bids or (position_0_bids == position_1_bids and random.choice([True, False])):
            win_position = position_1
            lose_position = position_0

        return win_position, lose_position

    def updateCarReward(self, car_id, position, win_position, car_action, position_0, actions_0, position_1, actions_1):
        position_0_bids = sum(actions_0) + len(actions_0)
        position_1_bids = sum(actions_1) + len(actions_1)
        bid_difference = abs(position_0_bids - position_1_bids)

        reward = 0.0
        if position is win_position and car_action == 1:
            # Car in winning position and car's action is 1.
            if bid_difference == 0:
                # Car would have lost had it acted differently.
                reward = -1.0
            elif bid_difference == 1:
                # Car would have tied had it acted differently.
                reward = -0.5
        elif position is not win_position and car_action == 0:
            # Car in losing position and car's action is 0.
            if bid_difference == 0:
                # Car would have won had it acted differently.
                reward = 1.0
            elif bid_difference == 1:
                # Car would have tied had it acted differently.
                reward = 0.5

        if car_id not in self.rewards:
            self.rewards[car_id] = 0
        self.rewards[car_id] += reward
        return reward