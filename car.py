import random
from abc import ABCMeta, abstractmethod


class Car:
    __metaclass__ = ABCMeta
    @abstractmethod
    def getAction(self, position_0, num_cars_0, position_1, num_cars_1):
        """
        Determines the car's action at each time step.
        TODO
        :return: Action value.
        """
        pass

    def __init__(self, car_id, protocol):
        self.car_id = car_id
        self.priority = None
        self.position = None
        self.rank = None
        self.route = None
        self.destination = None
        self.protocol = protocol

    def initTrip(self, origin, rank, route, destination):
        self.position = origin
        self.rank = rank
        self.route = route
        self.destination = destination

        # Pick a random priority.
        self.priority = random.choice([0, 1])

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
        if position is not self.position:
            # Decrement the current direction by 1.
            self.route[0][1] -= 1
            if self.route[0][1] == 0:
                # The current direction is completed, so remove it.
                self.route = self.route[1:]

        # Update the position.
        self.position = position

    def hasArrived(self):
        return self.position == self.destination


class RandomCar(Car):
    def getAction(self, position_0, num_cars_0, position_1, num_cars_1):
        if self.protocol.getCarReward(self.car_id) > 0:
            return random.choice([0, 1])
        return 0

class TruthfulCar(Car):
    def getAction(self, position_0, num_cars_0, position_1, num_cars_1):
        if self.protocol.getCarReward(self.car_id) > 0:
            return self.priority
        return 0