"""Utilities to split up some rectangles, and vary them, etc...
"""


class Rect:
    """Rect represents a rectangle
    This is defined by a width and height, and an anchor point.
    The anchor point is a pair of (rx, ry) and (x, y) 
    Where (x, y) refers to a point in space where the square is located.
    (rx, ry) refers to the point on the square that is located at that point. These are in square-coords, ranging from (0, 1).
    To transform from square coords to spatial coordinates, just multiply by width and height.
    """
    def __init__(self, size, anchor_space, anchor_rect):
        self.size = size
        self.anchor_space = anchor_space
        self.anchor_rect = anchor_rect

    def split_in_half(self, axis, distance=0, split_point=0.5):
        """Split in half along an axis. axis={0, 1} - horizontal or vertical
        Distance defines the distance between the squares (in spatial coordinates)
        Returns the two squares which do this.
        """
        if axis == 0:
            # Split along the x-axis
            # Need to get the left-most and right-most x points
            left_x, right_x = self.x_bounds
            width_1 = self.size[0] * split_point - distance / 2
            width_2 = self.size[0] * (1 - split_point) - distance / 2
            h = self.size[1]
            as_y = self.anchor_space[1]
            ar_y = self.anchor_rect[1]
            return (Rect((width_1, h), (left_x, as_y), (0, ar_y)),
                    Rect((width_2, h), (right_x, as_y), (1, ar_y)))
        else:
            # Split along the y-axis
            # Need to get the top-most and bottom-most x points
            bottom_y, top_y = self.y_bounds
            height_1 = self.size[1] * split_point - distance / 2
            height_2 = self.size[1] * (1 - split_point) - distance / 2
            w = self.size[0]
            as_x = self.anchor_space[0]
            ar_x = self.anchor_rect[0]
            return (Rect((w, height_1), (as_x, bottom_y), (ar_x, 0)),
                    Rect((w, height_2), (as_x, top_y), (ar_x, 1)))

    @property
    def x_bounds(self):
        left_x = self.anchor_space[0] - self.anchor_rect[0] * self.size[0]
        right_x = self.anchor_space[0] + (
            1 - self.anchor_rect[0]) * self.size[0]
        return (left_x, right_x)

    @property
    def y_bounds(self):
        bottom_y = self.anchor_space[1] - self.anchor_rect[1] * self.size[1]
        top_y = self.anchor_space[1] + (1 -
                                        self.anchor_rect[1]) * self.size[1]
        return (bottom_y, top_y)

    @property
    def centre(self):
        centre_x = self.anchor_space[0]+self.size[0]*(0.5-self.anchor_rect[0])
        centre_y = self.anchor_space[1]+self.size[1]*(0.5-self.anchor_rect[1])
        return (centre_x, centre_y)

    @centre.setter
    def centre(self, c):
        """Set the centre of this rectangle
        c is a tuple (x, y)
        """
        self.anchor_space = c
        self.anchor_rect = (0.5, 0.5)

    def split_in_half_along_longest_axis(self, distance=0, split_point=0.5):
        """Return two squares which split this square along the shortest axis
        """
        return self.split_in_half(self.size[0] < self.size[1], distance,
                                  split_point)

    def __str__(self):
        return "size: {}, anchor space: {}, anchor rect: {}".format(
            self.size, self.anchor_space, self.anchor_rect)

    def __repr__(self):
        return self.__str__()
