from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QTimer
import pyqtgraph as pg
import numpy as np
import sys


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
