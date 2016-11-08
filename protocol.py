from abc import ABCMeta, abstractmethod


class Protocol(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def getWinLosePositions(self, votes):
        """
        Identifies the 'winning' position in a conflict (the first car in the winning position is the one that gets to
        proceed into the intersection).
        :param votes: Dictionary storing the actions of all the cars in the conflict. Key is one of the current
        positions at which cars in the conflict are currently queued. Value is a list. The value at index i in the list
        corresponds to the number of cars that voted action i.
        :return: Winning position (x,y), losing position  (x,y)
        """
        pass

    @abstractmethod
    def computeCarReward(self, position, win_position, votes):
        """
        Computes the reward (if any) for the car at the given position based on the results of the conflict.
        :param position: Current position of the car for whom to compute a reward.
        :param win_position: Position that won the conflict.
        :param votes: Dictionary storing the actions of all the cars in the conflict. Key is one of the current
        positions at which cars in the conflict are currently queued. Value is a list. The value at index i in the list
        corresponds to the number of cars that voted action i.
        :return: Reward value (>= 0).
        """
        pass


class RandomProtocol(Protocol):
    """
    This is a placeholder protocol that makes random decisions.
    """

    def getWinLosePositions(self, votes):
        # Arbitrarily pick win and lose positions.
        win_position = None
        lose_position = None
        for position in votes:
            if win_position is None:
                win_position = position
                continue
            lose_position = position
            break
        return win_position, lose_position

    def computeCarReward(self, position, win_position, votes):
        return 0