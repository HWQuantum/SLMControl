from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QGroupBox, QComboBox, QScrollArea, QPushButton, QTabWidget
from PyQt5.QtCore import pyqtSlot, pyqtSignal
import pyqtgraph as pg
import numpy as np

from oam_pattern_controls import OAMControlSet, XYController
from zernike_controls import ZernikeSet


class SLMDisplay():
    '''Class to display an SLM pattern fullscreen onto a monitor
    '''
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
        '''Set the screen the plot is to be displayed on
        destroys the current window, and creates a new one with the same values
        '''
        slm_display_size = self.window.slm_display_size
        slm_position = self.window.slm_position
        image = self.window.image
        window_title = self.window.windowTitle()

        self.create_screen(screen, slm_display_size, slm_position,
                           window_title)
        self.window.set_and_update_image(image)

    def create_screen(self, screen, slm_display_size, slm_position,
                      window_title):
        '''Create a screen'''
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
    '''Class to display a numpy array as a fullscreen plot
    '''
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

    def update_SLM_size(self, size):
        '''Update the display size of the slm
        '''
        self.slm_display_size = size
        self.set_limits()


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
    def __init__(self, window_title, screens, slm_size):
        '''Pass a list of screens to allow this to select what screen a
        pattern is displayed on
        Pass slm_size to set the size of the slm to display on
        (how many pixels it has)
        '''
        super().__init__()
        self.screens = screens

        layout = QGridLayout()
        self.x, self.y = np.mgrid[-1:1:(slm_size[0] * 1j), -1:1:(slm_size[1] *
                                                                 1j)]

        screen_selector = QComboBox()
        oam_scroll_area = QScrollArea()
        zernike_scroll_area = QScrollArea()
        add_controller_button = QPushButton("Add OAM control")

        self.oam_controller = OAMControlSet()
        self.plot = FullScreenPlot(slm_size, slm_size)
        self.lut_controller = LUTController()
        self.zernike_controller = ZernikeSet(self.x, self.y, [(2, 2), (0, 2),
                                                              (-2, 2)])
        self.diffraction_grating = XYController("Diffraction grating")

        oam_scroll_area.setWidget(self.oam_controller)
        oam_scroll_area.setWidgetResizable(True)
        zernike_scroll_area.setWidget(self.zernike_controller)
        zernike_scroll_area.setWidgetResizable(True)

        for i, screen in enumerate(screens):
            screen_selector.addItem("Screen {}".format(i))

        self.slm_window = SLMDisplay(window_title,
                                     screens[screen_selector.currentIndex()],
                                     slm_size)

        screen_selector.currentIndexChanged.connect(
            lambda _: self.slm_window.set_screen(self.screens[screen_selector.
                                                              currentIndex()]))

        self.lut_controller.value_changed.connect(self.update_LUT)
        self.oam_controller.value_changed.connect(self.update_image)
        self.zernike_controller.value_changed.connect(self.update_image)
        self.diffraction_grating.value_changed.connect(self.update_image)
        add_controller_button.clicked.connect(
            self.oam_controller.add_new_oam_pattern)

        layout.addWidget(QLabel("Display on:"), 0, 0)
        layout.addWidget(screen_selector, 0, 1)
        layout.addWidget(add_controller_button, 0, 2)
        layout.addWidget(self.diffraction_grating, 0, 3)
        layout.addWidget(oam_scroll_area, 1, 0, 1, 4)
        layout.addWidget(self.plot, 2, 0, 1, 4)
        layout.addWidget(self.lut_controller, 3, 0, 1, 1)
        layout.addWidget(zernike_scroll_area, 3, 1, 1, 3)

        self.setLayout(layout)

        for i in range(1):
            self.oam_controller.add_new_oam_pattern()

    def update_LUT(self):
        self.plot.update_LUT(self.lut_controller.get_LUT())
        self.slm_window.window.update_LUT(self.lut_controller.get_LUT())

    def update_image(self):
        '''Update the image displayed on the oam plot and the
        gui plot
        '''
        diff_x, diff_y = self.diffraction_grating.get_values()
        zernike_image = self.zernike_controller.get_pattern()
        oam_image = np.sum([
            p["amplitude"] *
            np.exp(1j * ((p["ang_mom"] * np.arctan2(
                self.y - p["position"][1], self.x - p["position"][0])) +
                         (diff_x * self.x + diff_y * self.y) + p["phase"]))
            for p in self.oam_controller.get_values()
        ],
                           axis=0)
        new_image = np.angle(zernike_image * oam_image)
        self.plot.set_and_update_image(new_image)
        self.slm_window.set_image(new_image)

    def set_slm_size(self, size):
        '''Set the size of the slm to display on in pixels
        size is a tuple, eg: (500, 500)
        '''
        self.x, self.y = np.mgrid[-1:1:(size[0] * 1j), -1:1:(size[1] * 1j)]
        self.slm_window.window.update_SLM_size(size)
        self.plot.screen_size = size
        self.plot.update_SLM_size(size)
        self.zernike_controller.generate_polynomials(self.x, self.y)


class MultiSLMController(QTabWidget):
    '''Class to control multiple SLMs
    '''
    def __init__(self, screens, slm_size_list):
        super().__init__()
        for i, slm_screen in enumerate(slm_size_list):
            title = "SLM {}".format(i)
            self.addTab(SLMController(title, screens, slm_screen), title)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    w = MultiSLMController(app.screens(), [(500, 500), (500, 500)])
    w.show()
    app.exec()
