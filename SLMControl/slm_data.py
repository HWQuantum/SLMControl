"""This file contains information about the data structures
of the different classes

-------
Classes
-------

* Bronwie pattern
A brownie pattern is an ordered list of Rectangles
[Rect]

* Pizza pattern
A pizza pattern has:
inner radius
outer radius
slice spacing
circle span (how much of a circle does the pizza actually go around)
"""

from square_splitting import Rect
import numpy as np

example_brownie = [Rect((1, 1), (0, 0), (0, 0))]

example_pizza = {
    "inner_radius": 0,
    "outer_radius": 2,
    "slice_spacing": 0,
    "circle_span": 2 * np.pi
}
