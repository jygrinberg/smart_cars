from Tkinter import *
import time
import copy

class Animator:
    def __init__(self, size, num_roads, num_cars, fixed_cost):
        self.num_roads = num_roads
        self.fixed_cost = fixed_cost

        # Determine the max expected cost of a queue at any given position. This is a very rough approximation.
        self.cost_cutoff = max(num_cars / num_roads, 1)

        self.offset = 20
        self.step_size = (size - 2 * self.offset) / (self.num_roads - 1)

        self.board_width = size
        self.board_height = size

        self.stats_width = 200
        self.canvas_width = self.board_width + self.stats_width
        self.canvas_height = self.board_height

        self.master = Tk()
        self.canvas = Canvas(self.master, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()

        self.iteration_time = 0.1

        self.car_board = [[None] * self.num_roads for _ in xrange(self.num_roads)]
        self.car_labels = [[None] * self.num_roads for _ in xrange(self.num_roads)]
        self.prev_board = None

        self.stats_round_id = None
        self.stats_iteration_id = None
        self.stats_total_cost = None

    def _updateStats(self, round_id, iteration_id, total_cost):
        # Remove old stats.
        self.canvas.delete(self.stats_round_id)
        self.canvas.delete(self.stats_iteration_id)
        self.canvas.delete(self.stats_total_cost)

        # Add new stats.
        dynamic_stats_offset = self.offset + 80
        self.stats_round_id = self.canvas.create_text(self.board_width + (self.stats_width - 2 * self.offset) / 2.0,
                                                      dynamic_stats_offset, text='Round ID: %d' % round_id,
                                                      justify=CENTER)
        self.stats_iteration_id = self.canvas.create_text(self.board_width + (self.stats_width - 2 * self.offset) / 2.0,
                                                          dynamic_stats_offset + 30,
                                                          text='Iteration ID: %d' % iteration_id, justify=CENTER)
        self.stats_total_cost = self.canvas.create_text(self.board_width + (self.stats_width - 2 * self.offset) / 2.0,
                                                        dynamic_stats_offset + 60, text='Total Cost: %.2f' % total_cost,
                                                        justify=CENTER)

    def _coord(self, road_id, object_offset=0):
        return self.offset + (self.step_size * road_id) + (object_offset / 2)

    def _getCarColor(self, cost):
        cost_color_value = 255 - int(min(1, float(cost) / self.cost_cutoff) * 200)
        cost_color = '#%02x%02x%02x' % (0, 0, cost_color_value)
        return cost_color

    def _createCar(self, row_id, col_id, cost, car_queue):
        cost_color = self._getCarColor(cost)
        circle_car = False
        if circle_car:
            car_size = 10
            return self.canvas.create_oval(self._coord(row_id, -car_size), self._coord(col_id, -car_size),
                                                self._coord(row_id, car_size), self._coord(col_id, car_size),
                                                fill=cost_color, outline=cost_color, width=car_size)

        direction = car_queue[0].direction
        car_size = 40 # min(1, float(cost) / self.cost_cutoff) * 30 + 30
        if direction == 'up':
            return self.canvas.create_polygon(self._coord(row_id, -car_size), self._coord(col_id, car_size),
                                              self._coord(row_id, car_size), self._coord(col_id, car_size),
                                              self._coord(row_id, 0), self._coord(col_id, -car_size), fill=cost_color)
        elif direction == 'down':
            return self.canvas.create_polygon(self._coord(row_id, -car_size), self._coord(col_id, -car_size),
                                              self._coord(row_id, car_size), self._coord(col_id, -car_size),
                                              self._coord(row_id, 0), self._coord(col_id, car_size), fill=cost_color)
        elif direction == 'right':
            return self.canvas.create_polygon(self._coord(row_id, -car_size), self._coord(col_id, -car_size),
                                              self._coord(row_id, -car_size), self._coord(col_id, car_size),
                                              self._coord(row_id, car_size), self._coord(col_id, 0), fill=cost_color)
        else:
            return self.canvas.create_polygon(self._coord(row_id, car_size), self._coord(col_id, -car_size),
                                              self._coord(row_id, car_size), self._coord(col_id, car_size),
                                              self._coord(row_id, -car_size), self._coord(col_id, 0), fill=cost_color)
        
    def initAnimation(self, protocol_name, car_class_name):
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

        # Add animation-wide parameter info.
        self.canvas.create_text(self.board_width + (self.stats_width - 2 * self.offset) / 2.0, self.offset,
                                text='Protocol: %s' % protocol_name, justify=CENTER)
        self.canvas.create_text(self.board_width + (self.stats_width - 2 * self.offset) / 2.0,  self.offset + 30,
                                text='Car: %s' % car_class_name, justify=CENTER)

        # Initialize the stats.
        self._updateStats(0, 0, 0)

        # Update the canvas.
        self.master.update()

    def initRound(self, board, cost_board, round_id, total_cost):
        # Remove existing cars.
        [[self.canvas.delete(car) for car in car_row] for car_row in self.car_board]
        [[self.canvas.delete(car_label) for car_label in car_label_row] for car_label_row in self.car_labels]
        self.car_board = [[None] * self.num_roads for _ in xrange(self.num_roads)]
        self.car_labels = [[None] * self.num_roads for _ in xrange(self.num_roads)]

        for row_id in xrange(self.num_roads):
            for col_id in xrange(self.num_roads):
                if len(board[row_id][col_id]) == 0:
                    continue
                car = self._createCar(row_id, col_id, cost_board[row_id][col_id], board[row_id][col_id])
                car_label = self.canvas.create_text(self._coord(row_id), self._coord(col_id),
                                                    text='%d' % len(board[row_id][col_id]), fill='white',
                                                    justify=CENTER)
                self.car_board[row_id][col_id] = car
                self.car_labels[row_id][col_id] = car_label

        # Update the stats.
        self._updateStats(round_id, 0, total_cost)

        # Update the canvas.
        self.master.update()
        self.prev_board = copy.deepcopy(board)

    def updateAnimation(self, board, cost_board, win_next_positions, round_id, iteration_id, total_cost):
        '''
        Updates the canvas and displays the new state of the board for self.iteration_time seconds.
        :param board: List of lists of queues. The queue at (x,y) represents the queue of cars at that position.
        :param cost_board: List of lists, whose value at (x,y) represents the total cost of all cars at that position.
        :param win_next_positions: List of tuples of the form (win_position, next_position), where win_position is a
        position that won in the latest iteration, and next_position is the position to which the car there moved.
        '''
        # Populate slide_cars with the cars that move. slide_cars is a list of tuples of the form
        # (car widget, label widget, dx, dy).
        slide_cars = []
        for win_position, next_position in win_next_positions:
            if len(self.prev_board[win_position[0]][win_position[1]]) > 1:
                # The win position has cars after the moving car leaves, so create a new car widget and label for the
                # moving car.
                car = self._createCar(win_position[0], win_position[1],
                                      self.prev_board[win_position[0]][win_position[1]][0].priority + self.fixed_cost,
                                      self.prev_board[win_position[0]][win_position[1]])
                label = self.canvas.create_text(self._coord(win_position[0]), self._coord(win_position[1]), text='1',
                                                fill='white', justify=CENTER)

                # Update the car and label at the winning position.
                self.canvas.itemconfig(self.car_board[win_position[0]][win_position[1]],
                                       fill=self._getCarColor(cost_board[win_position[0]][win_position[1]]))
                self.canvas.itemconfig(self.car_labels[win_position[0]][win_position[1]],
                                       text='%d' % (len(self.prev_board[win_position[0]][win_position[1]]) - 1))
            else:
                # There is only one car in the win position, so move the widgets at this position.
                car = self.car_board[win_position[0]][win_position[1]]
                self.car_board[win_position[0]][win_position[1]] = None
                label = self.car_labels[win_position[0]][win_position[1]]
                self.car_labels[win_position[0]][win_position[1]] = None

            dx = 0
            dy = 0
            direction = self.prev_board[win_position[0]][win_position[1]][0].direction
            if direction == 'up':
                dy = -1
            elif direction == 'down':
                dy = 1
            elif direction == 'left':
                dx = -1
            else:
                dx = 1
            slide_cars.append((car, label, dx, dy))

        # Slide the cars that won.
        num_slide_iterations = 100
        slide_interval = float(self.step_size) / num_slide_iterations
        for _ in xrange(num_slide_iterations):
            [self.canvas.move(car, dx * slide_interval, dy * slide_interval) for car, _, dx, dy in slide_cars]
            [self.canvas.move(label, dx * slide_interval, dy * slide_interval) for _, label, dx, dy in slide_cars]
            self.master.update()
            time.sleep(float(self.iteration_time) / num_slide_iterations)

        # Update the next positions to reflect the cars having finished sliding.
        for win_position, next_position in win_next_positions:
            if self.car_labels[next_position[0]][next_position[1]] is not None:
                # There is already a label at next_position, so delete it.
                self.canvas.delete(self.car_labels[next_position[0]][next_position[1]])
                self.car_labels[next_position[0]][next_position[1]] = None
            else:
                # There is no car widget at next_position, so create one.
                car = self._createCar(next_position[0], next_position[1],
                                      cost_board[next_position[0]][next_position[1]],
                                      board[next_position[0]][next_position[1]])
                self.car_board[next_position[0]][next_position[1]] = car

            # Create a new label with the total number of cars at next_position.
            label = self.canvas.create_text(self._coord(next_position[0]), self._coord(next_position[1]),
                                            text='%d' % len(board[next_position[0]][next_position[1]]),
                                            fill='white', justify=CENTER)
            self.car_labels[next_position[0]][next_position[1]] = label

        # Remove the sliding cars and labels.
        [self.canvas.delete(car) for car, _, _, _ in slide_cars]
        [self.canvas.delete(label) for _, label, _, _ in slide_cars]

        # Update the stats.
        self._updateStats(round_id, iteration_id, total_cost)

        # Update the canvas.
        self.master.update()
        time.sleep(self.iteration_time)

        self.prev_board = copy.deepcopy(board)