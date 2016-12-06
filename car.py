import random
from abc import ABCMeta, abstractmethod


class Car:
    __metaclass__ = ABCMeta
    @abstractmethod
    def getAction(self, position_0, num_cars_0, position_1, num_cars_1):
        """
        Determines the car's action at each time step.
        :param position_0: (x,y) tuple coordinates of one of the positions involved in the conflict.
        :param actions_0: List of actions for each car in position_0.
        :param position_1: (x,y) tuple coordinates of one of the positions involved in the conflict.
        :param actions_1: List of actions for each car in position_1.
        :return: Action value.
        """
        pass

    @abstractmethod
    def __str__(self):
        pass

    def __init__(self, car_id, protocol, unlimited_reward):
        self.car_id = car_id
        self.priority = None
        self.position = None
        self.route = None
        self.destination = None
        self.direction = None
        self.protocol = protocol
        self.unlimited_reward = unlimited_reward

    def initTrip(self, origin, destination, route, priority):
        self.position = origin
        self.destination = destination
        self.route = route
        self.priority = priority
        self.direction = route[0][0]

    def getNextPosition(self):
        if len(self.route) == 0:
            raise Exception('Getting next position for car_id %d with empty route.' % self.car_id)
        if self.route[0][0] == 'up':
            return (self.position[0], self.position[1] - 1)
        if self.route[0][0] == 'down':
            return (self.position[0], self.position[1] + 1)
        if self.route[0][0] == 'left':
            return (self.position[0] - 1, self.position[1])
        else:
            return (self.position[0] + 1, self.position[1])

    def updatePosition(self, position):
        if position != self.position:
            # Decrement the current direction by 1.
            self.route[0][1] -= 1
            if self.route[0][1] == 0:
                # The current direction is completed, so remove it.
                self.route = self.route[1:]

                # Update the direction, if there is a new one.
                if len(self.route) > 0:
                    self.direction = self.route[0][0]

        # Update the position.
        self.position = position

    def hasArrived(self):
        return self.position == self.destination


class RandomCar(Car):
    def getAction(self, position_0, num_cars_0, position_1, num_cars_1):
        if self.unlimited_reward or self.protocol.getCarReward(self.car_id) > 0:
            return random.choice([0, 1])
        return 0

    def __str__(self):
        return 'random'


class TruthfulCar(Car):
    def getAction(self, position_0, num_cars_0, position_1, num_cars_1):
        if self.unlimited_reward or self.protocol.getCarReward(self.car_id) > 0:
            return self.priority
        return 0

    def __str__(self):
        return 'truthful'


class AggressiveCar(Car):
    def getAction(self, position_0, num_cars_0, position_1, num_cars_1):
        if self.unlimited_reward or self.protocol.getCarReward(self.car_id) > 0:
            return 1
        return 0

    def __str__(self):
        return 'greedy'