"""Tests for the SLMState class
"""

import unittest
from SLMControl.state import SLMState
import SLMControl.state_validation as sv
from uuid import uuid4


def _test_spec_after(func):
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

    @_test_spec_after
    def test_get_screen_by_uuid(self):
        self.assertEqual(self.state.get_screen_by_uuid(self.screen_id),
                         self.state._data["screens"][self.screen_id])

    @_test_spec_after
    def test_get_view_by_uuid(self):
        self.assertEqual(self.state.get_view_by_uuid(self.view_id),
                         self.state._data["views"][self.view_id])

    @_test_spec_after
    def test_get_pattern_by_uuid(self):
        self.assertEqual(self.state.get_pattern_by_uuid(self.pattern_id),
                         self.state._data["patterns"][self.pattern_id])

    @_test_spec_after
    def test_get_pattern_by_name(self):
        self.assertEqual(self.state.get_pattern_by_name(self.pattern_name),
                         self.state.get_pattern_by_uuid(self.pattern_id))
        # gives key error when name not in state
        with self.assertRaises(KeyError):
            self.state.get_pattern_by_name("wrong_name")

    @_test_spec_after
    def test_get_view_by_name(self):
        self.assertEqual(self.state.get_view_by_name(self.view_name),
                         self.state.get_view_by_uuid(self.view_id))
        # gives key error when name not in state
        with self.assertRaises(KeyError):
            self.state.get_view_by_name("wrong_name")

    @_test_spec_after
    def test_get_screen_by_name(self):
        self.assertEqual(self.state.get_screen_by_name(self.screen_name),
                         self.state.get_screen_by_uuid(self.screen_id))
        # gives key error when name not in state
        with self.assertRaises(KeyError):
            self.state.get_screen_by_name("wrong_name")

    @_test_spec_after
    def test_connect_pattern_to_view(self):
        self.assertTrue(
            self.state.connect_pattern_to_view(self.pattern_id, self.view_id))
        self.assertEqual(
            self.state._data["views"][self.view_id]["patterns"], {
                self.pattern_id:
                [self.pattern_id, 1, {
                    "position": [0, 0],
                    "size": [0, 0],
                    "rotation": 0
                }]
            })

    @_test_spec_after
    def test_connect_pattern_to_view_twice(self):
        transform = {
            "position": [10, -1],
            "size": [-10, -10],
            "rotation": -1.0
        }
        self.assertTrue(
            self.state.connect_pattern_to_view(self.pattern_id, self.view_id))
        self.assertTrue(
            self.state.connect_pattern_to_view(self.pattern_id, self.view_id,
                                               0, transform))
        self.assertEqual(self.state._data["views"][self.view_id]["patterns"],
                         {self.pattern_id: [self.pattern_id, 0, transform]})

    @_test_spec_after
    def test_adding_pattern(self):
        my_id = uuid4()
        pattern = {"id": my_id, "type": "test_type", "name": "added_name"}
        self.state.add_pattern(pattern)
        self.assertEqual(self.state.get_pattern_by_uuid(my_id), pattern)

    @_test_spec_after
    def test_adding_pattern_when_already_added(self):
        my_id = uuid4()
        pattern = {"id": my_id, "type": "test_type", "name": "added_name"}
        self.state.add_pattern(pattern)
        pattern2 = {"id": my_id, "type": "test_type", "name": "name2"}
        self.state.add_pattern(pattern2)
        self.assertEqual(self.state.get_pattern_by_uuid(my_id), pattern2)

    @_test_spec_after
    def test_remove_pattern(self):
        self.state.connect_pattern_to_view(self.pattern_id, self.view_id)
        self.state.remove_pattern(self.pattern_id)
        self.assertEqual(self.state._data["patterns"], {})
        self.assertEqual(self.state._data["views"][self.view_id]["patterns"],
                         {})

    @_test_spec_after
    def test_add_view(self):
        my_id = uuid4()
        view = {
            "id": my_id,
            "name": "test_view",
            "transform": {
                "position": [0, 0],
                "size": [0, 0],
                "rotation": 0
            },
            "patterns": {}
        }
        self.state.add_view(view)
        self.assertEqual(self.state.get_view_by_uuid(my_id), view)

    @_test_spec_after
    def test_add_view_when_already_added(self):
        view = {
            "id": self.view_id,
            "name": "test_view",
            "transform": {
                "position": [0, 10],
                "size": [100, 0],
                "rotation": 20
            },
            "patterns": {}
        }
        self.state.add_view(view)
        self.assertEqual(self.state.get_view_by_uuid(self.view_id), view)

    def test_remove_view(self):
        self.state.connect_view_to_screen(self.view_id, self.screen_id)
        self.state.remove_view(self.view_id)
        self.assertEqual(self.state._data["views"], {})
        self.assertEqual(self.state._data["screens"][self.screen_id]["views"],
                         {})

    @_test_spec_after
    def test_connect_view_to_screen(self):
        self.assertTrue(
            self.state.connect_view_to_screen(self.view_id, self.screen_id))
        self.assertEqual(self.state._data["screens"][self.screen_id]["views"],
                         {self.view_id: [self.view_id, [0, 0], [0, 0]]})

    @_test_spec_after
    def test_connect_view_to_screen_twice(self):
        pos = [10, -10]
        size = [30, 40]
        self.assertTrue(
            self.state.connect_view_to_screen(self.view_id, self.screen_id))
        self.assertTrue(
            self.state.connect_view_to_screen(self.view_id, self.screen_id,
                                              pos, size))
        self.assertEqual(self.state._data["screens"][self.screen_id]["views"],
                         {self.view_id: [self.view_id, pos, size]})

    @_test_spec_after
    def test_add_screen(self):
        screen_id = uuid4()
        screen = {
            "id": screen_id,
            "name": "new_screen",
            "size": [50, 50],
            "offset": [0, 0],
            "views": {}
        }
        self.state.add_screen(screen)
        self.assertEqual(self.state.get_screen_by_uuid(screen_id), screen)

    @_test_spec_after
    def test_remove_screen(self):
        self.assertTrue(self.state.remove_screen(self.screen_id))
        self.assertEqual(self.state._data["screens"], {})


if __name__ == "__main__":
    unittest.main()
