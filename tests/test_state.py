"""Tests for the SLMState class
"""

import unittest
from SLMControl.state import SLMState
import SLMControl.state_validation as sv
from uuid import uuid4


class SLMStateTest(unittest.TestCase):
    def setUp(self):
        """Fill the state with some data
        """
        self.state = SLMState()
        self.screen_id = uuid4()
        self.view_id = uuid4()
        self.pattern_id = uuid4()
        self.state._data["patterns"][self.pattern_id] = {
            "id": self.pattern_id,
            "type": "test_type",
            "name": "test_name"
        }
        self.state._data["views"][self.view_id] = {
            "id": self.view_id,
            "name": "test_view",
            "transform": {
                "position": (0, 1),
                "size": (10, 10),
                "rotation": 0
            },
            "patterns": {}
        }
        self.state._data["screens"][self.screen_id] = {
            "id": self.screen_id,
            "name": "test_screen",
            "size": (0, 1),
            "offset": (10, 10),
            "views": {}
        }

    def test_get_screen_by_uuid(self):
        self.assertEqual(self.state.get_screen_by_uuid(self.screen_id),
                         self.state._data["screens"][self.screen_id])
        self.assertTrue(sv.slm_screen.validate(self.state._data["screens"][self.screen_id]))

    def test_get_view_by_uuid(self):
        self.assertEqual(self.state.get_view_by_uuid(self.view_id),
                         self.state._data["views"][self.view_id])

    def test_get_pattern_by_uuid(self):
        self.assertEqual(self.state.get_pattern_by_uuid(self.pattern_id),
                         self.state._data["patterns"][self.pattern_id])


if __name__ == "__main__":
    unittest.main()
