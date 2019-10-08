'''This file contains the functions that load the pixel entanglement stuff
The circle packings come from http://hydra.nat.uni-magdeburg.de/packing/csq/csq.html
The coordinates give the centres of the circles, and they all have the same radius, given in the radii array.

The circles fit into a square with coordinates (-0.5, -0.5) -> (0.5, 0.5) 
or a circle with radius 1
'''

import numpy as np
from numba import njit, jit
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

radii_sq = np.loadtxt(
    'circle_packing/radius_square.txt'
)[:, 1]  # the radius array for packing circles into a square

radii_ci = np.loadtxt(
    'circle_packing/radius_circle.txt'
)[:, 1]  # the radius array for packing circles into a circle


def get_coords_square(i):
    '''Get the coordinates of i circles packed into a square
    '''
    if i == 1:
        return np.loadtxt('circle_packing/csq{}.txt'.format(i))
    else:
        return np.loadtxt('circle_packing/csq{}.txt'.format(i))[:, 1:]


def get_coords_circle(i):
    '''Get the coordinates of i circles packed into a circle
    '''
    if i == 1:
        return np.loadtxt('circle_packing/cci{}.txt'.format(i))[1:]
    else:
        return np.loadtxt('circle_packing/cci{}.txt'.format(i))[:, 1:]


@njit()
def point_in_circle(x, y, c):
    '''Check if the given point is inside the given circle
    p is a tuple (x, y) - the point you want to check
    c is a tuple (r, (x, y)) containing the radius of the circle and the x and y
    '''
    return ((x - c[1][0])**2 + (y - c[1][1])**2) < c[0]**2


@jit()
def complex_field(components,
                  X,
                  Y,
                  pixel_radius=1,
                  circle_radius=1,
                  circle_position=(0, 0)):
    '''Take the components of a vector, the X and Y matrices (from meshgrid)
    the radius of the pixel bases, the radius of the circle containing the pixels
    and the positions of the containing circle
    return the complex field over X and Y which represents this vector
    '''
    n_pixels = len(components)
    coords = get_coords_circle(n_pixels)
    field = np.zeros(X.shape, dtype=np.complex128)
    if n_pixels > 1:
        for i, p in enumerate(coords):
            field += components[i] * point_in_circle(
                X / circle_radius - circle_position[0],
                Y / circle_radius - circle_position[1],
                (pixel_radius * radii_ci[n_pixels], p))
    else:
        field += components[0] * point_in_circle(
            X / circle_radius - circle_position[0],
            Y / circle_radius - circle_position[1],
            (pixel_radius * radii_ci[n_pixels], coords))

    return field


def plot_circles(i, ax):
    '''Pack i circles into the unit circle and plot them
    '''
    coords = get_coords_circle(i)
    for row in coords:
        ax.add_patch(mpatches.Circle(row, radii_ci[i]))


def nice_circles_plot():
    fig, axs = plt.subplots(5, 5)
    for i, ax in enumerate(axs.flatten()):
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        plot_circles(i + 2, ax)
    plt.show()
