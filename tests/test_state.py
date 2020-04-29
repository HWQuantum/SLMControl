"""Tests for the SLMState class
"""

import unittest
from SLMControl.state import SLMState
import SLMControl.state_validation as sv
from uuid import uuid4


def test_spec_after(func):
    def wrapper_test_spec(*args, **kwargs):
        v = func(*args, **kwargs)
        args[0].assertTrue(sv.slm_controller.is_valid(args[0].state._data),
                           "state doesn't conform to schema")
        return v

    return wrapper_test_spec


class SLMStateTest(unittest.TestCase):
    def setUp(self):
        """Fill the state with some data
        """
        self.state = SLMState()
        self.screen_id = uuid4()
        self.view_id = uuid4()
        self.pattern_id = uuid4()
        self.pattern_name = "test_name"
        self.screen_name = "test_name"
        self.view_name = "test_name"

        self.state._data["patterns"][self.pattern_id] = {
            "id": self.pattern_id,
            "type": "test_type",
            "name": self.pattern_name,
            "test_prop": 20125,
        }
        self.state._data["views"][self.view_id] = {
            "id": self.view_id,
            "name": self.view_name,
            "transform": {
                "position": (0, 1),
                "size": (10, 10),
                "rotation": 0
            },
            "patterns": {}
        }
        self.state._data["screens"][self.screen_id] = {
            "id": self.screen_id,
            "name": self.screen_name,
            "size": (0, 1),
            "offset": (10, 10),
            "views": {}
        }
        self.state._data["additional_data"] = 2

    @test_spec_after
    def test_get_screen_by_uuid(self):
        self.assertEqual(self.state.get_screen_by_uuid(self.screen_id),
                         self.state._data["screens"][self.screen_id])

    @test_spec_after
    def test_get_view_by_uuid(self):
        self.assertEqual(self.state.get_view_by_uuid(self.view_id),
                         self.state._data["views"][self.view_id])

    @test_spec_after
    def test_get_pattern_by_uuid(self):
        self.assertEqual(self.state.get_pattern_by_uuid(self.pattern_id),
                         self.state._data["patterns"][self.pattern_id])

    @test_spec_after
    def test_get_pattern_by_name(self):
        self.assertEqual(self.state.get_pattern_by_name(self.pattern_name),
                         self.state.get_pattern_by_uuid(self.pattern_id))

    @test_spec_after
    def test_get_view_by_name(self):
        self.assertEqual(self.state.get_view_by_name(self.view_name),
                         self.state.get_view_by_uuid(self.view_id))

    @test_spec_after
    def test_get_screen_by_name(self):
        self.assertEqual(self.state.get_screen_by_name(self.screen_name),
                         self.state.get_screen_by_uuid(self.screen_id))


if __name__ == "__main__":
    unittest.main()
