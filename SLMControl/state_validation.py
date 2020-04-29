"""This module contains a description of the the state of the slmcontrol application

The data is stored in a single dictionary, which is validated with the schema library
"""

from schema import Schema, And, Use, Optional, Or
from typing import Union
from uuid import uuid4, UUID
import numpy as np


def screen_size_value(n):
    """Return true if n >= 0 and is an integer
    """
    return (n >= 0) and isinstance(n, int)


def view_size_value(n):
    """Return true if n is a valid view size (integer)
    """
    return isinstance(n, int)


def is_number(n):
    """Return true if n is a number (int or float)
    """
    return isinstance(n, (int, float))


def is_screen_size(v):
    """Validates a correct screen size
    """
    return screen_size_value(v[0]) and screen_size_value(v[1])


def is_view_size(v):
    """Validates a correct size for a view on a screen
    """
    return view_size_value(v[0]) and view_size_value(v[1])


def is_2d_vec(v):
    """Validates a correct pattern size
    """
    return is_number(v[0]) and is_number(v[1])


def is_view_reference_data(v):
    """Validates view reference data
    View reference data should be an iterable containing:
    [screen_position, screen_size]
    """
    return is_2d_vec(v[0]) and is_2d_vec(v[1])


def is_pattern_coefficient(v):
    """Check if v is a valid coefficient to a pattern
    """
    return isinstance(v, (float, int, complex))


def is_pattern_reference_data(v):
    """Validates pattern reference data
    the data should be a coefficient and a transform
    where coefficient can be a complex number
    """
    return (is_pattern_coefficient(v[0]) and transform.validate(v[1]))


# A transform is a dictionary containing a position, size and rotation
transform = Schema({
    "position": is_2d_vec,
    "size": is_2d_vec,
    "rotation": is_number
})

# The slm_screen is a representation of a specific SLM screen.
# It can display multiple patterns by using multiple slm_views
slm_screen = Schema({
    "id": UUID,
    Optional("name"): str,
    "size": is_screen_size,
    "offset": is_view_size,
    "views": Or({UUID: is_view_reference_data}, {})
})

# The slm_view represents a specific view onto a pattern
slm_view = Schema({
    "id": UUID,
    Optional("name"): str,
    "transform": transform,
    "patterns": Or({UUID: is_pattern_reference_data}, {})
})

# Pattern is a thing that can be projected onto an slm screen
pattern = Schema({
    "id": UUID,
    "type": str,
    Optional("name"): str,
    Optional(str): object
})

# The data for controlling a set of SLMs
slm_controller = Schema({
    "screens": Or({UUID: slm_screen}, {}),
    "views": Or({UUID: slm_view}, {}),
    "patterns": Or({UUID: pattern}, {}),
    Optional(str): object
})
