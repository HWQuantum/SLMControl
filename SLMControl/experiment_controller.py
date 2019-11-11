from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QAction, QFileDialog
from PyQt5.QtCore import QSettings

from slm_controller import MultiSLMController, SplitSLMController
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
        forget_defaults_action = QAction("Forget defaults", self)
        forget_defaults_action.triggered.connect(self.reset_defaults_to_zero)
        forget_defaults_action.setToolTip("Forget the saved default values")
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
        file_menu.addAction(forget_defaults_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        file_menu.addSeparator()
        file_menu.addAction(save_last_measurement)

        experiment_menu = main_menu.addMenu("Experiments")
        for (name, tooltip, function) in self.experiment_functions:
            action = QAction(name, self)
            action.setToolTip(tooltip)
            action.triggered.connect(
                (lambda f: lambda: self.run_experiment(f))(function))
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

    def reset_defaults_to_zero(self):
        """Reset all the values in the default QSettings to empty
        """
        settings = QSettings("HWQuantum", "SLMControl")
        settings.setValue("slm_settings", {})
        settings.setValue("coincidence_settings", {})

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
        self.setEnabled(False)
        self.last_measurement_data.append(
            function(self.slm_controller, self.coincidence_counter, self.app))
        self.setEnabled(True)


class SplitSLMExperimentController(QMainWindow):
    def __init__(self, screens, display_size, experiment_functions,
                 application):
        """Pass:
        screens, the list of screens given by QApplication.screens()
        display_size: a tuples which give the resolution of the slm; (x, y)

        experiment_functions is a list of functions, names and tooltips 
        which are the experiments to run
        the type is: [(name, tooltip, function)]

        The function signature is
        f(multi_slm_controller, coincidence_counter, application) -> measurements
        """
        super().__init__()

        layout = QHBoxLayout()

        self.app = application

        self.slm_controller = SplitSLMController(screens, display_size)
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
        forget_defaults_action = QAction("Forget defaults", self)
        forget_defaults_action.triggered.connect(self.reset_defaults_to_zero)
        forget_defaults_action.setToolTip("Forget the saved default values")
        save_action = QAction("Save values", self)
        save_action.triggered.connect(self.save_values)
        load_action = QAction("Load values", self)
        load_action.triggered.connect(self.load_values)
        save_alice_dimension_action = QAction("Save Alice settings d", self)
        save_alice_dimension_action.triggered.connect(
            self.save_alice_dimension_settings)
        save_bob_dimension_action = QAction("Save Bob settings d", self)
        save_bob_dimension_action.triggered.connect(
            self.save_bob_dimension_settings)
        load_alice_dimension_action = QAction("Load Alice settings d", self)
        load_alice_dimension_action.triggered.connect(
            self.load_alice_dimension_settings)
        load_bob_dimension_action = QAction("Load Bob settings d", self)
        load_bob_dimension_action.triggered.connect(
            self.load_bob_dimension_settings)
        load_action = QAction("Load values", self)
        load_action.triggered.connect(self.load_values)
        save_last_measurement = QAction("Save last measurement", self)
        save_last_measurement.triggered.connect(self.save_last_measurement)
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu("File")
        file_menu.addAction(save_defaults_action)
        file_menu.addAction(load_defaults_action)
        file_menu.addAction(forget_defaults_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        file_menu.addSeparator()
        file_menu.addAction(save_alice_dimension_action)
        file_menu.addAction(save_bob_dimension_action)
        file_menu.addAction(load_alice_dimension_action)
        file_menu.addAction(load_bob_dimension_action)
        file_menu.addSeparator()
        file_menu.addAction(save_last_measurement)

        experiment_menu = main_menu.addMenu("Experiments")
        for (name, tooltip, function) in self.experiment_functions:
            action = QAction(name, self)
            action.setToolTip(tooltip)
            action.triggered.connect(
                (lambda f: lambda: self.run_experiment(f))(function))
            experiment_menu.addAction(action)
        open_split_controller_action = QAction("Open split controls")
        open_split_controller_action.triggered.connect(
            self.slm_controller.split_control.show)
        experiment_menu.addSeparator()
        experiment_menu.addAction(open_split_controller_action)

    def closeEvent(self, event):
        self.slm_controller.close()

        event.accept()

    def set_values(self, slm_values, coincidence_values):
        self.slm_controller.set_values(slm_values)
        self.coincidence_counter.set_values(coincidence_values)

    def load_values_from_default(self):
        settings = QSettings("HWQuantum", "SplitSLMControl")
        self.set_values(settings.value("slm_settings", {}),
                        settings.value("coincidence_settings", {}))

    def save_values_to_default(self):
        settings = QSettings("HWQuantum", "SplitSLMControl")
        settings.setValue("slm_settings", self.slm_controller.get_values())
        settings.setValue("coincidence_settings",
                          self.coincidence_counter.get_values())

    def save_alice_dimension_settings(self):
        """Save the brownie pattern settings for the current dimension for alice
        """
        d = self.slm_controller.alice.dimension.value()
        values = self.slm_controller.alice.patterns[2].get_values()
        settings = QSettings("HWQuantum", "SplitSLMControl")
        settings.setValue("alice/dim{}".format(d), values)

    def save_bob_dimension_settings(self):
        """Save the brownie pattern settings for the current dimension for bob
        """
        d = self.slm_controller.bob.dimension.value()
        values = self.slm_controller.bob.patterns[2].get_values()
        settings = QSettings("HWQuantum", "SplitSLMControl")
        settings.setValue("bob/dim{}".format(d), values)

    def load_alice_dimension_settings(self):
        """Load the saved settings for the current dimension for alice
        """
        d = self.slm_controller.alice.dimension.value()
        settings = QSettings("HWQuantum", "SplitSLMControl")
        self.slm_controller.alice.patterns[2].set_values(
            settings.value("alice/dim{}".format(d), [[0, 0, 0, 0]] * d))

    def load_bob_dimension_settings(self):
        """Load the saved settings for the current dimension for bob
        """
        d = self.slm_controller.bob.dimension.value()
        settings = QSettings("HWQuantum", "SplitSLMControl")
        self.slm_controller.bob.patterns[2].set_values(
            settings.value("bob/dim{}".format(d), [[0, 0, 0, 0]] * d))

    def reset_defaults_to_zero(self):
        """Reset all the values in the default QSettings to empty
        """
        settings = QSettings("HWQuantum", "SplitSLMControl")
        settings.setValue("slm_settings", {})
        settings.setValue("coincidence_settings", {})

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
        self.setEnabled(False)
        self.last_measurement_data.append(
            function(self.slm_controller, self.coincidence_counter, self.app))
        self.setEnabled(True)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import split_slm_experiments
    import inspect
    import sys

    app = QApplication(sys.argv)
    functions = [
        (f[1].__menu_name__, f[1].__tooltip__, f[1])
        for f in inspect.getmembers(split_slm_experiments, inspect.isfunction)
    ]

    # w = ExperimentController(app.screens(), [(512, 512), (512, 512)],
    #                          functions, app)
    w = SplitSLMExperimentController(app.screens(), (512, 512), functions, app)

    w.show()

    app.exec()
