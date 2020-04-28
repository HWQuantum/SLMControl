"""This module contains a description of the the state of the slmcontrol application

The data is stored in a single dictionary, which is validated with the schema library
"""

from schema import Schema, And, Use, Optional
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


# The slm_screen is a representation of a specific SLM screen.
# It can display multiple patterns by using multiple slm_views
slm_screen = Schema({
    "id": UUID,
    Optional("name"): str,
    "size": (screen_size_value, screen_size_value)
})

# The slm_view represents a specific view onto a pattern
slm_view = Schema({
    "id": UUID,
    Optional("name"): str,
    "pattern_top_left": (is_number, is_number),
    "pattern_size": (is_number, is_number),
    "pattern_rotation": is_number,
    Optional("pattern_id"): UUID,
})
