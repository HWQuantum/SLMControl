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
    return screen_size_value(t[0]) and screen_size_value(t[1])


def is_view_size(v):
    """Validates a correct size for a view on a screen
    """
    return view_size_value(v[0]) and view_size_value(v[1])


def is_2d_vec(v):
    """Validates a correct pattern size
    """
    return is_number(v[0]) and is_number(v[1])


def is_view_reference(v):
    """Validates a view reference.
    A view reference should be an iterable containing:
    [uuid, screen_position, screen_size]
    """
    return isinstance(v[0], UUID) and is_2d_vec(v[1]) and is_2d_vec(v[2])


def is_pattern_coefficient(v):
    """Check if v is a valid coefficient to a pattern
    """
    return isinstance(v, (float, int, complex))


def is_pattern_reference(v):
    """Validates a pattern reference
    A pattern reference should be an iterable containing:
    [uuid, coefficient, transform]
    where coefficient can be a complex number
    """
    return (isinstance(v[0], UUID) and is_pattern_coefficient(v[1])
            and transform.validate(v[2]))


# A transform is a dictionary containing a position, size and rotation
transform = Schema({
    "position": is_2d_vec,
    "shape": is_2d_vec,
    "rotation": is_number
})

# The slm_screen is a representation of a specific SLM screen.
# It can display multiple patterns by using multiple slm_views
slm_screen = Schema({
    "id": UUID,
    Optional("name"): str,
    "size": is_screen_size,
    "offset": is_view_size,
    "views": [is_view_reference]
})

# The slm_view represents a specific view onto a pattern
slm_view = Schema({
    "id": UUID,
    Optional("name"): str,
    "transform": transform,
    "patterns": [is_pattern_reference]
})

# Pattern is a thing that can be projected onto an slm screen
pattern = Schema({"id": UUID, "type": str, Optional("name"): str, str: object})

# The data for controlling a set of SLMs
slm_controller = Schema({
    "screens": Or({UUID: slm_screen}, {}),
    "views": Or({UUID: slm_view}, {}),
    "patterns": Or({UUID: pattern}, {}),
    str: object
})
