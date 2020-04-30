"""Classes to do with controlling the state from a GUI
"""

import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw
from SLMControl.state import SLMState
from uuid import UUID, uuid4
from SLMControl.screen import Screen
from SLMControl.view import View

class SLMStateGui(qw.QWidget):
    def __init__(self, state = None):
        super().__init__()
        if state is None:
            self._state = SLMState()
        else:
            self._state = state

        self.screens = {}
        self.views = {}
        self.patterns = {}

    def get_pattern_control(self, pattern_id: UUID) -> qw.QWidget:
        """Open a pattern control from a UUID, returning the widget if it's already open
        TODO add in a way to open arbitrary pattern controllers
        """
        if pattern_id in self.patterns:
            return self.patterns[pattern_id]
        else:
            self.patterns[pattern_id] = self._state.get_pattern_by_uuid(pattern_id)
            pass

    def get_screen_control(self, screen_id: UUID) -> qw.QWidget:
        """Open a screen control from a UUID, returning the widget from self.screens[screen_id]
        if already created
        """
        if screen_id in self.screens:
            return self.screens[screen_id]
        else:
            s_gui = Screen(self._state.get_screen_by_uuid(screen_id), self._state)
            self.screens[screen_id] = s_gui
            return s_gui

    def get_view_control(self, view_id: UUID) -> qw.QWidget:
        """Open a view control from a UUID, returning the widget from self.views[view_id]
        if already created
        """
        if view_id in self.views:
            return self.views[view_id]
        else:
            v_gui = View(self._state.get_view_by_uuid(view_id), self._state)
            self.views[view_id] = v_gui
            return v_gui

import sys

app = qw.QApplication(sys.argv)
s = SLMStateGui()
s.show()
sys.exit(app.exec())
