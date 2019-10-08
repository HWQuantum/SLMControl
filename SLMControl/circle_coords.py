'''This file contains the functions that load the pixel entanglement stuff
The circle packings come from http://hydra.nat.uni-magdeburg.de/packing/csq/csq.html
The coordinates give the centres of the circles, and they all have the same radius, given in the radii array.

The circles fit into a square with coordinates (-0.5, -0.5) -> (0.5, 0.5)
'''

import numpy as np
from numba import njit

radii = np.loadtxt('circle_packing/radius.txt')[:, 1]


def get_coords(i):
    '''Get the coordinates of i circles packed into a square
    '''
    return np.loadtxt('circle_packing/csq{}.txt'.format(i))[:, 1:]


@njit()
def point_in_circle(x, y, c):
    '''Check if the given point is inside the given circle
    p is a tuple (x, y) - the point you want to check
    c is a tuple (r, (x, y)) containing the radius of the circle and the x and y
    '''
    return ((x - c[1][0])**2 + (y - c[1][1])**2) < c[0]**2
