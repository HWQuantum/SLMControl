import numpy as np
from PyQt5.QtWidgets import QWidget, QComboBox, QGridLayout, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import pyqtSlot, pyqtSignal
import pyqtgraph as pg
import json

from pattern import PatternContainer
from lut_control import LUTWidget


class SLMDisplay():
    """Class to display an SLM pattern fullscreen onto a monitor
    """
    def __init__(self,
                 window_title,
                 screen,
                 slm_display_size=None,
                 slm_position=(0, 0)):
        self.screen = screen

        self.window = None
        self.create_screen(screen, slm_display_size, slm_position,
                           window_title)

    def set_screen(self, screen):
        """Set the screen the plot is to be displayed on
        destroys the current window, and creates a new one with the same values
        """
        slm_display_size = self.window.slm_display_size
        slm_position = self.window.slm_position
        image = self.window.image
        window_title = self.window.windowTitle()
        LUT = self.window.LUT

        self.create_screen(screen, slm_display_size, slm_position,
                           window_title)
        if LUT is not None:
            self.window.update_LUT(LUT)
        self.window.set_and_update_image(image)

    def create_screen(self, screen, slm_display_size, slm_position,
                      window_title):
        """Set up the slm display on the given screen
        """
        self.screen = screen

        if self.window is not None:
            self.window.close()

        self.window = FullScreenPlot(
            (screen.geometry().width(), screen.geometry().height()),
            slm_display_size, slm_position)

        self.window.show()
        self.window.windowHandle().setScreen(screen)
        self.window.showFullScreen()
        self.window.setWindowTitle(window_title)

    @pyqtSlot(np.ndarray)
    def set_image(self, image):
        '''Set the image which is being displayed on the fullscreen plot
        '''
        self.window.set_and_update_image(image)


class FullScreenPlot(pg.PlotWidget):
    """Class to display a numpy array as a fullscreen plot
    """
    def __init__(self, screen_size, slm_display_size=None,
                 slm_position=(0, 0)):
        '''Take in the screen size which to plot to, the slm display size if
        it differs from the screen size and the slm position if it needs to
        be placed at a specific point on the plot

        The slm position is taken from the top-left corner of the image
        '''
        super().__init__()

        self.screen_size = None
        self.slm_display_size = None
        self.slm_position = None
        self.image = None

        # update the size parameters
        if slm_display_size is None:
            slm_display_size = screen_size
        self.screen_size = screen_size
        self.slm_display_size = slm_display_size
        self.slm_position = slm_position
        self.image = np.zeros(self.slm_display_size)
        self.LUT = None

        self.set_limits()
        self.hideAxis('left')
        self.hideAxis('bottom')

        # set a placeholder image
        self.image_display = pg.ImageItem(self.image)
        self.addItem(self.image_display)

    def set_limits(self):
        '''Set the limits of the display
        '''
        self.setLimits(xMin=0 - self.slm_position[0],
                       xMax=self.screen_size[0] - self.slm_position[0],
                       yMin=self.slm_display_size[1] - self.screen_size[1] +
                       self.slm_position[1],
                       yMax=self.slm_display_size[1] + self.slm_position[1],
                       minXRange=self.screen_size[0],
                       maxXRange=self.screen_size[0],
                       minYRange=self.screen_size[1],
                       maxYRange=self.screen_size[1])

    @pyqtSlot(np.ndarray)
    def set_and_update_image(self, new_image):
        '''Take a numpy array and set it as the new image,
        then update the display
        '''
        self.image = new_image
        self.image_display.setImage(self.image)

    @pyqtSlot(np.ndarray)
    def update_LUT(self, LUT):
        '''Update the lookup table for the plot
        '''
        self.image_display.setLookupTable(LUT)
        self.LUT = LUT

    def update_SLM_size(self, size):
        '''Update the display size of the slm
        '''
        self.slm_display_size = size
        self.set_limits()


def points_to_lut(points):
    '''Converts a set of points into a LUT for pyqtgraph
    '''
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    lut = np.interp(np.linspace(-np.pi, np.pi, 255), xs, ys)
    return lut


class SLMController(QWidget):
    """A controller for a single SLM
    """
    def __init__(self, window_title, screens, slm_size, overlay=None):
        """
        window_title is the title that's displayed on the slm pattern window
        Pass a list of screens, to decide what screen the pattern is displayed on. 
        slm_size gives the size of the slm
        overlay is a complex-number array of the shape slm_size which
        is overlaid onto the image. This allows you to add corrections to the slm.
        """
        super().__init__()
        self.screens = screens

        self.layout = QGridLayout()

        self.x, self.y = np.mgrid[-1:1:(slm_size[0] * 1j), -1:1:(slm_size[1] *
                                                                 1j)]
        self.slm_size = slm_size

        self.overlay = overlay
        self.screen_selector = QComboBox()
        self.pattern = PatternContainer(self.x, self.y)
        self.lut_control = None
        self.lut_control_button = QPushButton("Open LUT controls")
        self.lut_list = [(-np.pi, 0), (np.pi, 255)]
        self.plot = FullScreenPlot(slm_size, slm_size)

        for i, screen in enumerate(screens):
            self.screen_selector.addItem("Screen {}".format(i))

        self.slm_window = SLMDisplay(
            window_title, self.screens[self.screen_selector.currentIndex()],
            slm_size)

        self.screen_selector.currentIndexChanged.connect(
            lambda _: self.slm_window.set_screen(self.screens[
                self.screen_selector.currentIndex()]))

        self.pattern.value_changed.connect(self.update_image)
        self.lut_control_button.clicked.connect(self.open_lut_control)

        self.layout.addWidget(QLabel("Display on:"), 0, 0)
        self.layout.addWidget(self.screen_selector, 0, 1)
        self.layout.addWidget(self.lut_control_button, 0, 2, 1, 2)
        self.layout.addWidget(self.pattern, 1, 0, 1, 2)
        self.layout.addWidget(self.plot, 1, 2, 1, 2)

        self.setLayout(self.layout)

    @pyqtSlot()
    def update_image(self):
        """Update the image that's displayed on the SLM display and
        the widget's plot
        """
        new_image = self.pattern.get_pattern()
        if self.overlay is None:
            new_image = np.abs(new_image) * np.angle(new_image)
        else:
            new_image = np.abs(new_image) * np.angle(new_image * self.overlay)

        self.plot.set_and_update_image(new_image)
        self.slm_window.set_image(new_image)

    @pyqtSlot()
    def open_lut_control(self):
        """Open the lookup table controls in a separate window
        """
        if self.lut_control is None:
            self.lut_control = LUTWidget(self.lut_list)
            self.lut_control.value_changed.connect(self.update_LUT)
            self.lut_control.closed.connect(self.remove_lut_control)
            self.lut_control.show()

    def remove_lut_control(self):
        """Remove the lookup table control from the variable
        """
        self.lut_control = None

    @pyqtSlot(list)
    def update_LUT(self, new_lut):
        """Update the lookup table
        """
        if len(new_lut) >= 2:
            self.lut_list = new_lut
            new_lut = points_to_lut(self.lut_list)
            self.plot.update_LUT(new_lut)
            self.slm_window.window.update_LUT(new_lut)

    def closeEvent(self, event):
        """Make sure the SLM window will close
        """
        self.slm_window.window.close()
        if self.lut_control is not None:
            self.lut_control.close()

    def get_values(self):
        """Get the values
        """
        return {
            "pattern": self.pattern.get_values(),
            "lut_list": self.lut_list,
        }

    def set_values(self, value):
        try:
            self.pattern.set_values(values["pattern"])
        except KeyError:
            pass

        try:
            self.lut_list.set_values(values["lut_list"])
        except KeyError:
            pass


class MultiSLMController(QWidget):
    '''Controls for entanglement on multiple SLMs
    '''
    def __init__(self, screens, slm_sizes):
        super().__init__()
        self.layout = QGridLayout()
        save_button = QPushButton("Save values")
        load_button = QPushButton("Load values")

        self.slms = [
            SLMController("SLM {}".format(i), screens, size)
            for i, size in enumerate(slm_sizes)
        ]

        self.layout.addWidget(save_button, 0, 0)
        self.layout.addWidget(load_button, 0, 1)
        for i, slm in enumerate(self.slms):
            self.layout.addWidget(slm, i + 1, 0, 1, 2)

        self.setLayout(self.layout)

        save_button.clicked.connect(self.save_file)
        load_button.clicked.connect(self.open_file)

    def closeEvent(self, event):
        for slm in self.slms:
            slm.closeEvent(event)

    def get_values(self):
        '''Returns a list of slm settings
        ready and prepared to be tucked in a json
        '''
        return [slm_screen.get_values() for slm_screen in self.slms]

    def set_values(self, slm_list):
        '''Accepts a list of slm settings
        '''
        for i, slm in enumerate(slm_list):
            if i < len(self.slms):
                self.slms[i].set_values(slm)

    def save_values_to_json_file(self, filename):
        '''Save the values to a given filename
        doesn't catch any errors
        '''
        values = self.get_values()
        with open(filename, 'w') as f:
            json.dump(values, f)

    def read_values_from_json_file(self, filename):
        '''Read the values from a given filename
        doesn't catch any errors
        '''
        with open(filename, 'r') as f:
            self.set_values(json.load(f))

    def try_read_values_from_json_file(self, filename):
        '''wraps reading values in a try except thing,
        so it doesn't fail when reading a naughty file
        '''
        try:
            self.read_values_from_json_file(filename)
        except:
            pass

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "")
        if filename:
            self.try_read_values_from_json_file(filename)

    def save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save file", "")
        if filename:
            self.save_values_to_json_file(filename)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])

    w = MultiSLMController(app.screens(), [(512, 512), (512, 512)])

    w.show()
    app.exec()
