from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QGroupBox, QComboBox, QScrollArea, QPushButton, QTabWidget, QFileDialog
from PyQt5.QtCore import pyqtSlot, pyqtSignal
import pyqtgraph as pg
import numpy as np
import json

from oam_pattern_controls import OAMControlSet, XYController
from zernike_controls import ZernikeSet
from lut_control import LUTWidget


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
        self.value_changed.emit()


def points_to_lut(points):
    '''Converts a set of points into a LUT for pyqtgraph
    '''
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    lut = np.interp(np.linspace(-np.pi, np.pi, 255), xs, ys)
    return lut


class SLMController(QWidget):
    '''A controller for a single SLM
    '''
    def __init__(self, window_title, screens, slm_size):
        '''Pass a list of screens to allow this to select what screen a
        pattern is displayed on
        Pass slm_size to set the size of the slm to display on
        (how many pixels it has)
        There are two zernike controls: one for position and one for the slm
        '''
        super().__init__()
        self.screens = screens

        layout = QGridLayout()
        self.x, self.y = np.mgrid[-1:1:(slm_size[0] * 1j), -1:1:(slm_size[1] *
                                                                 1j)]
        self.slm_size = slm_size

        screen_selector = QComboBox()
        oam_scroll_area = QScrollArea()
        position_zernike_scroll_area = QScrollArea()
        slm_zernike_scroll_area = QScrollArea()
        add_controller_button = QPushButton("Add OAM control")

        self.oam_controller = OAMControlSet()
        self.plot = FullScreenPlot(slm_size, slm_size)
        self.position_zernike_controller = ZernikeSet(
            self.x, self.y, [(2, 2), (0, 2), (-2, 2)],
            title="Position Zernike Controller")
        self.slm_zernike_controller = ZernikeSet(self.x, self.y, [(2, 2),
                                                                  (0, 2),
                                                                  (-2, 2)],
                                                 title="SLM Zernike Controller")
        self.position_controller = XYController("Position")

        self.lut_control = None
        self.lut_control_button = QPushButton("Open LUT controls")
        self.diffraction_grating = XYController("Diffraction grating")
        self.lut_list = [(-np.pi, 0), (np.pi, 255)]

        oam_scroll_area.setWidget(self.oam_controller)
        oam_scroll_area.setWidgetResizable(True)
        position_zernike_scroll_area.setWidget(
            self.position_zernike_controller)
        position_zernike_scroll_area.setWidgetResizable(True)
        slm_zernike_scroll_area.setWidget(self.slm_zernike_controller)
        slm_zernike_scroll_area.setWidgetResizable(True)

        for i, screen in enumerate(screens):
            screen_selector.addItem("Screen {}".format(i))

        self.slm_window = SLMDisplay(window_title,
                                     screens[screen_selector.currentIndex()],
                                     slm_size)

        screen_selector.currentIndexChanged.connect(
            lambda _: self.slm_window.set_screen(self.screens[screen_selector.
                                                              currentIndex()]))

        self.oam_controller.value_changed.connect(self.update_image)
        self.position_zernike_controller.value_changed.connect(self.update_image)
        self.slm_zernike_controller.value_changed.connect(self.update_image)
        self.diffraction_grating.value_changed.connect(self.update_image)
        self.position_controller.value_changed.connect(self.update_image)
        self.position_controller.value_changed.connect(
            self.change_zernike_position)
        add_controller_button.clicked.connect(
            self.oam_controller.add_new_oam_pattern)
        self.lut_control_button.clicked.connect(self.open_lut_control)

        layout.addWidget(QLabel("Display on:"), 0, 1)
        layout.addWidget(screen_selector, 0, 2)
        layout.addWidget(add_controller_button, 0, 0)
        layout.addWidget(self.diffraction_grating, 0, 3)
        layout.addWidget(oam_scroll_area, 1, 0, 1, 3)
        layout.addWidget(self.plot, 1, 3, 1, 1)
        layout.addWidget(self.lut_control_button, 3, 0, 1, 1)
        layout.addWidget(self.position_controller, 3, 1, 1, 3)
        layout.addWidget(position_zernike_scroll_area, 4, 0, 1, 2)
        layout.addWidget(slm_zernike_scroll_area, 4, 2, 1, 2)

        self.setLayout(layout)

        self.oam_controller.add_new_oam_pattern()

    def change_zernike_position(self):
        x, y = self.position_controller.get_values()
        self.position_zernike_controller.change_position(self.x-x, self.y-y)

    def open_lut_control(self):
        '''Open the LUT control if it's not open already
        '''
        if self.lut_control is None:
            self.lut_control = LUTWidget(self.lut_list)
            self.lut_control.value_changed.connect(self.update_LUT)
            self.lut_control.closed.connect(self.remove_lut_control)
            self.lut_control.show()

    def remove_lut_control(self):
        self.lut_control = None

    @pyqtSlot(list)
    def update_LUT(self, new_lut):
        if len(new_lut) >= 2:
            self.lut_list = new_lut
            new_lut = points_to_lut(self.lut_list)
            self.plot.update_LUT(new_lut)
            self.slm_window.window.update_LUT(new_lut)

    def update_image(self):
        '''Update the image displayed on the oam plot and the
        gui plot
        '''
        diff_x, diff_y = self.diffraction_grating.get_values()
        position_zernike_image = self.position_zernike_controller.get_pattern()
        slm_zernike_image = self.slm_zernike_controller.get_pattern()
        x, y = self.position_controller.get_values()
        oam_image = np.sum([
            p["amplitude"] *
            np.exp(1j * ((p["ang_mom"] * np.arctan2(self.y - y, self.x - x)) +
                         (diff_x * self.x + diff_y * self.y) + p["phase"]))
            for p in self.oam_controller.get_values()
        ],
                           axis=0)
        new_image = np.angle(slm_zernike_image * position_zernike_image *
                             oam_image)
        self.plot.set_and_update_image(new_image)
        self.slm_window.set_image(new_image)

    def set_slm_size(self, size):
        '''Set the size of the slm to display on in pixels
        size is a tuple, eg: (500, 500)
        '''
        self.x, self.y = np.mgrid[-1:1:(size[0] * 1j), -1:1:(size[1] * 1j)]
        delta_x, delta_y = self.position_controller.get_values()
        self.slm_window.window.update_SLM_size(size)
        self.plot.screen_size = size
        self.plot.update_SLM_size(size)
        self.position_zernike_controller.generate_polynomials(
            self.x - delta_x, self.y - delta_y)
        self.slm_zernike_controller.generate_polynomials(self.x, self.y)

    def close_slm_window(self):
        self.slm_window.window.close()
        if self.lut_control is not None:
            self.lut_control.close()

    def get_values(self):
        '''Get a dictionary of values for the contained widgets
        '''
        return {
            "oam_controller":
            self.oam_controller.get_values(),
            "position_zernike_controller":
            self.position_zernike_controller.get_values(),
            "slm_zernike_controller":
            self.slm_zernike_controller.get_values(),
            "diffraction_grating":
            self.diffraction_grating.get_values(),
            "position_controller":
            self.position_controller.get_values(),
            "lut_list":
            self.lut_list,
        }

    def set_values(self, *args, **kwargs):
        '''Set the values of the SLM display from a set of args and kwargs
        Expects values for:
        oam_controller,
        position_zernike_controller,
        slm_zernike_controller,
        position_controller,
        diffraction_grating,
        lut_list,
        '''
        for dictionary in args:
            for key, value in dictionary.items():
                if key == 'lut_list':
                    self.update_LUT(value)
                else:
                    try:
                        getattr(self, key).set_values(value)
                    except AttributeError:
                        pass

        for key, value in kwargs.items():
            if key == 'lut_list':
                self.update_LUT(value)
            else:
                try:
                    getattr(self, key).set_values(value)
                except AttributeError:
                    pass


class MultiSLMController(QWidget):
    '''Class to control multiple SLMs
    '''
    def __init__(self, screens, slm_size_list):
        super().__init__()
        self.slm_tabs = []
        self.tab_widget = QTabWidget()
        for i, slm_screen in enumerate(slm_size_list):
            title = "SLM {}".format(i)
            slm_tab = SLMController(title, screens, slm_screen)
            self.tab_widget.addTab(slm_tab, title)
            self.slm_tabs.append(slm_tab)
        self.layout = QGridLayout()
        save_button = QPushButton("Save values")
        load_button = QPushButton("Load values")

        self.layout.addWidget(save_button, 0, 0)
        self.layout.addWidget(load_button, 0, 1)
        self.layout.addWidget(self.tab_widget, 1, 0, 1, 2)
        self.setLayout(self.layout)

        save_button.clicked.connect(self.save_file)
        load_button.clicked.connect(self.open_file)

    def closeEvent(self, event):
        for tab in self.slm_tabs:
            tab.close_slm_window()

    def get_values(self):
        '''Returns a list of slm settings
        ready and prepared to be tucked in a json
        '''
        return [slm_screen.get_values() for slm_screen in self.slm_tabs]

    def set_values(self, slm_list):
        '''Accepts a list of slm settings
        '''
        for i, slm in enumerate(slm_list):
            if i < len(self.slm_tabs):
                self.slm_tabs[i].set_values(slm)

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


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    w = MultiSLMController(app.screens(), [(512, 512), (512, 512)])
    w.show()
    app.exec()
