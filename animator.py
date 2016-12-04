from Tkinter import *
import time


class Animator:
    def __init__(self, size, num_roads, num_cars):
        self.num_roads = num_roads

        # Determine the max expected cost of a queue at any given position. This is a very rough approximation.
        self.cost_cutoff = max(num_cars / num_roads, 1)

        self.master = Tk()
        self.canvas = Canvas(self.master, width=size, height=size)
        self.canvas.pack()

        self.offset = 10
        self.step_size = (size - 2 * self.offset) / (self.num_roads - 1)

        self.iteration_time = 1.0

        self.cars = set()
        self.car_labels = set()
        
    def _coord(self, road_id, object_offset=0):
        return self.offset + (self.step_size * road_id) + (object_offset / 2)

    def _createCar(self, row_id, col_id, cost_color):
        car_width = 10
        circle_car = True
        if circle_car:
            return self.canvas.create_oval(self._coord(row_id, -car_width), self._coord(col_id, -car_width),
                                                self._coord(row_id, car_width), self._coord(col_id, car_width),
                                                fill=cost_color, outline=cost_color, width=car_width)
        return self.canvas.create_polygon(self._coord(row_id, -car_width), self._coord(col_id, -car_width),
                                          self._coord(row_id, car_width), self._coord(col_id, car_width))

    def initAnimation(self):
        # Draw road network.
        for row_id in xrange(1, self.num_roads, 2):
            self.canvas.create_line(self._coord(0), self._coord(row_id), self._coord(self.num_roads - 1),
                                    self._coord(row_id), fill='black', width=2.0)
        for col_id in xrange(1, self.num_roads, 2):
            self.canvas.create_line(self._coord(col_id), self._coord(0), self._coord(col_id),
                                    self._coord(self.num_roads - 1), fill='black', width=2.0)

        # Draw intersections.
        dot_width = 4.0
        for row_id in xrange(0, self.num_roads):
            y = self._coord(row_id)
            for col_id in xrange(0, self.num_roads):
                if row_id % 2 == 0 and col_id % 2 == 0:
                    continue
        
                x = self._coord(col_id)
                self.canvas.create_oval(x - dot_width / 2, y - dot_width / 2, x + dot_width / 2, y + dot_width / 2,
                                        fill='black', width=dot_width)
        self.master.update()

    def updateAnimation(self, board, cost_board, cars):
        '''
        Updates the canvas and displays the new state of the board for self.iteration_time seconds.
        :param board: List of lists, whose value at (x,y) represents the number of cars at that position.
        :param cost_board: List of lists, whose value at (x,y) represents the total cost of all cars at that position.
        :param cars: List of car objects on the board.
        '''
        # Remove existing cars.
        [self.canvas.delete(car) for car in self.cars]
        [self.canvas.delete(car_label) for car_label in self.car_labels]

        # Add new cars.
        for row_id in xrange(self.num_roads):
            for col_id in xrange(self.num_roads):
                if board[row_id][col_id] == 0:
                    continue
                cost_color_value = int(min(1, float(cost_board[row_id][col_id]) / self.cost_cutoff) * 255)
                cost_color = '#%02x%02x%02x' % (0, 0, cost_color_value)
                car = self._createCar(row_id, col_id, cost_color)
                car_label = self.canvas.create_text(self._coord(row_id), self._coord(col_id),
                                                    text='%d' % board[row_id][col_id], fill='white', justify=CENTER)
                self.cars.add(car)
                self.car_labels.add(car_label)

        self.master.update()
        time.sleep(self.iteration_time)

        #
        # mainloop()
