from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QAction, QFileDialog
from PyQt5.QtCore import QSettings

from slm_controller import MultiSLMController
from coincidence_counting import CoincidenceWidget


class ExperimentController(QMainWindow):
    def __init__(self, screens, display_sizes, experiment_functions,
                 application):
        """Pass:
        screens, the list of screens given by QApplication.screens()
        display_sizes: a list containing tuples which give the resolutions of the slms; [(x, y)]

        experiment_functions is a list of functions, names and tooltips 
        which are the experiments to run
        the type is: [(name, tooltip, function)]

        The function signature is
        f(multi_slm_controller, coincidence_counter, application) -> measurements
        """
        super().__init__()

        layout = QHBoxLayout()

        self.app = application

        self.slm_controller = MultiSLMController(screens, display_sizes)
        self.experiment_functions = experiment_functions
        self.coincidence_counter = CoincidenceWidget()

        self.last_measurement_data = []

        layout.addWidget(self.slm_controller)
        layout.addWidget(self.coincidence_counter)

        self.internal_widget = QWidget()
        self.internal_widget.setLayout(layout)
        self.setCentralWidget(self.internal_widget)

        self.create_menus()
        self.load_values_from_default()

    def create_menus(self):
        save_defaults_action = QAction("Save new defaults", self)
        save_defaults_action.triggered.connect(self.save_values_to_default)
        load_defaults_action = QAction("Load defaults", self)
        load_defaults_action.triggered.connect(self.load_values_from_default)
        save_action = QAction("Save values", self)
        save_action.triggered.connect(self.save_values)
        load_action = QAction("Load values", self)
        load_action.triggered.connect(self.load_values)
        save_last_measurement = QAction("Save last measurement", self)
        save_last_measurement.triggered.connect(self.save_last_measurement)
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu("File")
        file_menu.addAction(save_defaults_action)
        file_menu.addAction(load_defaults_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        file_menu.addSeparator()
        file_menu.addAction(save_last_measurement)

        experiment_menu = main_menu.addMenu("Experiments")
        for (name, tooltip, function) in self.experiment_functions:
            action = QAction(name, self)
            action.setToolTip(tooltip)
            action.triggered.connect(lambda: self.run_experiment(function))
            experiment_menu.addAction(action)

    def closeEvent(self, event):
        self.slm_controller.close()

        event.accept()

    def set_values(self, slm_values, coincidence_values):
        self.slm_controller.set_values(slm_values)
        self.coincidence_counter.set_values(coincidence_values)

    def load_values_from_default(self):
        settings = QSettings("HWQuantum", "SLMControl")
        self.set_values(settings.value("slm_settings", {}),
                        settings.value("coincidence_settings", {}))

    def save_values_to_default(self):
        settings = QSettings("HWQuantum", "SLMControl")
        settings.setValue("slm_settings", self.slm_controller.get_values())
        settings.setValue("coincidence_settings",
                          self.coincidence_counter.get_values())

    def load_values(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "")
        if filename:
            settings = QSettings(filename, QSettings.IniFormat)
            self.set_values(settings.value("slm_settings", {}),
                            settings.value("coincidence_settings", {}))

    def save_last_measurement(self):
        if len(self.last_measurement_data) > 0:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save last measurement data", "")
            if filename:
                with open(filename, 'wb') as f:
                    self.last_measurement_data[-1].save_data(f)

    def save_values(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save file", "")
        if filename:
            settings = QSettings(filename, QSettings.IniFormat)
            settings.setValue("slm_settings", self.slm_controller.get_values())
            settings.setValue("coincidence_settings",
                              self.coincidence_counter.get_values())

    def run_experiment(self, function):
        """Run an experiment using the given function
        """
        self.last_measurement_data.append(
            function(self.slm_controller, self.coincidence_counter, self.app))


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import experiments
    import inspect
    import sys

    app = QApplication(sys.argv)
    functions = [(f[1].__menu_name__, f[1].__tooltip__, f[1])
                 for f in inspect.getmembers(experiments, inspect.isfunction)]

    w = ExperimentController(app.screens(), [(512, 512), (512, 512)],
                             functions, app)

    w.show()

    app.exec()
