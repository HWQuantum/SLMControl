from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QGroupBox
from PyQt5.QtCore import pyqtSlot, pyqtSignal
import pyqtgraph as pg
import numpy as np


class SLMDisplay():
    '''Class to display an SLM pattern fullscreen onto a monitor
    '''
    screen = None

    def __init__(self, screen, slm_display_size=None, slm_position=(0, 0)):
        self.screen = screen

        self.window = FullScreenPlot(
            (screen.geometry().width(), screen.geometry().height()),
            slm_display_size, slm_position)

        self.window.showFullScreen()

    def set_screen(self, screen):
        '''Set the screen the plot is to be displayed on
        '''
        self.screen = screen
        self.window.windowHandle().setScreen(self.screen)
        self.window.showFullScreen()

    @pyqtSlot(np.ndarray)
    def set_image(self, image):
        '''Set the image which is being displayed on the fullscreen plot
        '''
        self.window.set_and_update_image(image)


class FullScreenPlot(pg.PlotWidget):
    '''Class to display a numpy array as a fullscreen plot
    '''
    screen_size = None
    slm_display_size = None
    slm_position = None
    image = None

    def __init__(self, screen_size, slm_display_size=None,
                 slm_position=(0, 0)):
        '''Take in the screen size which to plot to, the slm display size if
        it differs from the screen size and the slm position if it needs to
        be placed at a specific point on the plot

        The slm position is taken from the top-left corner of the image
        '''
        super().__init__()

        # update the size parameters
        if slm_display_size is None:
            slm_display_size = screen_size
        self.screen_size = screen_size
        self.slm_display_size = slm_display_size
        self.slm_position = slm_position
        self.image = np.zeros(self.slm_display_size)

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


class LUTController(QGroupBox):
    '''Control the lookup table of the pyqtgraph imageitem

    the imageitem needs a (256, 3) shaped ndarray which contains the
    colours to display

    this is controlled by 3 spinboxes:
    maximum value
    minimum clamp
    maximum clamp
    '''

    value_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setTitle("LUT Controls")

        layout = QGridLayout()

        self.max_value = pg.SpinBox(value=255,
                                    int=True,
                                    step=1,
                                    bounds=(0, 255))
        self.min_clamp = pg.SpinBox(value=-np.pi, bounds=(-np.pi, np.pi))
        self.max_clamp = pg.SpinBox(value=np.pi, bounds=(-np.pi, np.pi))

        self.max_value.sigValueChanged.connect(self.value_changed.emit)
        self.min_clamp.sigValueChanged.connect(self.value_changed.emit)
        self.max_clamp.sigValueChanged.connect(self.value_changed.emit)

        layout.addWidget(QLabel("max value:"), 0, 0, 1, 1)
        layout.addWidget(self.max_value, 0, 1, 1, 1)
        layout.addWidget(QLabel("max clamp:"), 1, 0, 1, 1)
        layout.addWidget(self.max_clamp, 1, 1, 1, 1)
        layout.addWidget(QLabel("min clamp:"), 2, 0, 1, 1)
        layout.addWidget(self.min_clamp, 2, 1, 1, 1)

        self.setLayout(layout)

    def get_LUT(self):
        '''Get the lookup table defined by this controller
        '''
        min_index = np.int(
            np.round((self.min_clamp.value() + np.pi) / (2 * np.pi) * 255))
        max_index = np.int(
            np.round((self.max_clamp.value() + np.pi) / (2 * np.pi) * 255))
        lut = np.empty((255, 3), dtype=np.uint8)
        lut[:min_index] = 0
        lut[max_index:] = self.max_value.value()
        if min_index < max_index:
            lut[min_index:max_index, :] = np.tile(
                np.linspace(0,
                            self.max_value.value(),
                            abs(max_index - min_index),
                            dtype=np.uint8), (3, 1)).T
        return lut

    def get_values(self):
        '''Get the values defined by this LUT controller
        and return them in a dictionary
        '''
        return {
            "max_value": self.max_value.value(),
            "max_clamp": self.max_clamp.value(),
            "min_clamp": self.min_clamp.value(),
            }

    def set_values(self, *args, **kwargs):
        '''Set the values of this LUT controller
        '''
        for dictionary in args:
            for key, value in dictionary.items():
                try:
                    getattr(self, key).setValue(value)
                except AttributeError:
                    pass
        for key, value in kwargs.items():
            try:
                getattr(self, key).setValue(value)
            except AttributeError:
                pass

class SLMController(QWidget):
    '''A controller for a single SLM
    '''
    def __init__(self, screens):
        '''Pass a list of screens to allow this to select what screen a
        pattern is displayed on
        '''
        super().__init__()
        layout = QGridLayout()
        l=LUTController()
        l.set_values({'max_value': 10})
        layout.addWidget(l)
        self.setLayout(layout)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    w = SLMController(app.screens())
    w.show()
    app.exec()
