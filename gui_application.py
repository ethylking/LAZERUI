from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6 import QtWidgets, uic, QtCore
from PyQt6.QtCore import QObject, QThread, pyqtSignal
import sys
import random
import pyqtgraph as pg
from spectramaker import *
from data_processor import DataProcessor
from threads import GenericThread, ExperimentThread, FileProcessingThread, EquipmentThreads
import os
import pyqtgraph as pg


Design, _ = uic.loadUiType('gui_window.ui')

class GenericWorker(QObject):
    finished = pyqtSignal() 
    error = pyqtSignal(tuple)  
    
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.function(*self.args, **self.kwargs)
        except Exception as e:
            self.error.emit((type(e), e.strerror))
        finally:
            self.finished.emit()


class MainWindow(QMainWindow, Design):

    class ExperimentWorker(QThread):

        newDataAvailable = pyqtSignal(str, float)
        experimentFinished = pyqtSignal()

        def __init__(self, spectramaker, params):
            super().__init__()
            self.sm = spectramaker
            self.params = params

        def run(self):
            self.sm.get_spectrum_with_signal(self.params, self.newDataAvailable)
            self.experimentFinished.emit()



    def __init__(self):
        self.thread = None
        self.sm = Spectramaker()
        #self.setup_processing_ui()
        super().__init__()

        self.setupUi(self)
        self._init_ui_components()
        self._setup_ui()
        self._setup_plots()
        self._connect_signals()
        
        self.current_oscilloscope_data = None
        self.current_folder_path = None
        self.wavelengths = []  
        self.intensities = []
        self.current_thread = None

    def _init_ui_components(self):
        self.wavemeterConnectButton = self.wavemeterConnectButton
        self.energymeterConnectButton = self.energymeterConnectButton
        self.motorConnectButton = self.motorConnectButton
        self.oscilloscopeConnectButton = self.oscilloscopeConnectButton
        self.getEnergyProfilePushButton = self.getEnergyProfilePushButton
        self.getSpectrumPushButton = self.getSpectrumPushButton
        self.warningWindowLineEdit = self.warningWindowLineEdit
        self.wavelengthStartSpinBox = self.wavelengthStartSpinBox
        self.wavelengthEndSpinBox = self.wavelengthEndSpinBox
        self.filenameLineEdit = self.filenameLineEdit
        self.folderLineEdit = self.folderLineEdit
        self.refreshRateSpinBox = self.refreshRateSpinBox
        self.wavelengthStepSpinBox = self.wavelengthStepSpinBox
        self.goHomeButton = self.goHomeButton
        self.wavemeterWavelengthLineEdit = self.wavemeterWavelengthLineEdit
        self.wavemeterWavelengthLineEdit_2 = self.wavemeterWavelengthLineEdit_2
        self.calibrationWavelengthLineEdit = self.calibrationWavelengthLineEdit
        self.calibrationWavelengthLineEdit_2 = self.calibrationWavelengthLineEdit_2
        self.recalibrateButton = self.recalibrateButton
        self.goToSpinBox = self.goToSpinBox
        self.goToPushButton = self.goToPushButton
        self.averageCountSpinBox = self.averageCountSpinBox
        self.InspecEnergy = self.InspecEnergy
        self.goToSpinBoxSecond = self.goToSpinBoxSecond
        self.goToPushButtonSecond = self.goToPushButtonSecond
        self.motorConnectButtonSecond = self.motorConnectButtonSecond
        self.UseDyeLazerRadioButton = self.UseDyeLazerRadioButton
        self.UseOPOLazerRadioButton = self.UseOPOLazerRadioButton
        self.Steps_MotorX = self.Steps_MotorX
        self.Steps_MotorZ = self.Steps_MotorZ
        self.GoSteps_MotorX = self.GoSteps_MotorX
        self.GoSteps_MotorZ = self.GoSteps_MotorZ
        self.FirstHarmonicEnergy = self.FirstHarmonicEnergy
        self.EnergyAccurace = self.EnergyAccurace
        self.FrequencySpinBox = self.FrequencySpinBox
        self.loadOscilloscopeFileButton = self.loadOscilloscopeFileButton
        self.plotFullSpectrumButton = self.plotFullSpectrumButton
        self.leftBoundarySpinBox = self.leftBoundarySpinBox
        self.rightBoundarySpinBox = self.rightBoundarySpinBox
        self.baselineComboBox = self.baselineComboBox

    def _setup_ui(self):
        self.setWindowTitle("Autospectromizer")
        self.show_warning_message('нет сообщений')
        
        buttons = [
            self.wavemeterConnectButton, 
            self.energymeterConnectButton, 
            self.motorConnectButton,
            self.motorConnectButtonSecond,
            self.oscilloscopeConnectButton
        ]
        for button in buttons:
            button.setStyleSheet("background-color: red;")
        
        self.Steps_MotorX.setRange(-1000, 1000)
        self.Steps_MotorZ.setRange(-1000, 1000)
        
        self.leftBoundarySpinBox.setRange(-0.001, 0.001)  
        self.leftBoundarySpinBox.setDecimals(9)           
        self.leftBoundarySpinBox.setSingleStep(1e-7)      
        
        self.rightBoundarySpinBox.setRange(-0.001, 0.001)
        self.rightBoundarySpinBox.setDecimals(9)
        self.rightBoundarySpinBox.setSingleStep(1e-7)
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_global)
        self.setMinimumSize(400, 400)
        self.setMaximumSize(1800, 800)
        self.timer.start(1000)
        self.refreshRateSpinBox.setValue(self.timer.interval())
        
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setVisible(False)
        self.cancelButton = QtWidgets.QPushButton("Отмена")
        self.cancelButton.clicked.connect(self.cancel_operation)
        self.cancelButton.setVisible(False)
        
        self.spinboxes_limits_init()

    def _setup_plots(self):
        self.oscilloscopePlotWidget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, 
                                                QtWidgets.QSizePolicy.Policy.Expanding)
        self.intensityPlotWidget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, 
                                                QtWidgets.QSizePolicy.Policy.Expanding)

        self.oscilloscopePlot = pg.PlotWidget(self.oscilloscopePlotWidget)
        self.oscilloscopePlot.setLabel('left', 'Амплитуда', 'V')
        self.oscilloscopePlot.setLabel('bottom', 'Время', 's')
        self.oscilloscopePlot.showGrid(x=True, y=True, alpha=0.3)
        self.oscilloscopeCurve = self.oscilloscopePlot.plot(pen='g')

        self.leftBoundaryLine = pg.InfiniteLine(pos=0, angle=90, pen='r', movable=True)
        self.rightBoundaryLine = pg.InfiniteLine(pos=0, angle=90, pen='r', movable=True)
        self.oscilloscopePlot.addItem(self.leftBoundaryLine)
        self.oscilloscopePlot.addItem(self.rightBoundaryLine)

        self.intensityPlot = pg.PlotWidget(self.intensityPlotWidget)
        self.intensityPlot.setLabel('left', 'Интенсивность', 'a.u.')
        self.intensityPlot.setLabel('bottom', 'Длина волны', 'nm')
        self.intensityPlot.showGrid(x=True, y=True, alpha=0.3)
        self.intensityCurve = self.intensityPlot.plot(pen='b', symbol='o', symbolSize=5)

        oscilloscope_layout = QtWidgets.QVBoxLayout(self.oscilloscopePlotWidget)
        oscilloscope_layout.addWidget(self.oscilloscopePlot)
    
        intensity_layout = QtWidgets.QVBoxLayout(self.intensityPlotWidget)
        intensity_layout.addWidget(self.intensityPlot)

    def _connect_signals(self):
        self.wavemeterConnectButton.clicked.connect(
            lambda: self.start_thread(EquipmentThreads.wavemeter_connect, self.sm, 
                                    button=self.wavemeterConnectButton, 
                                    progress_message="Подключение измерителя длины волны...")
        )
        self.energymeterConnectButton.clicked.connect(
            lambda: self.start_thread(EquipmentThreads.energymeter_connect, self.sm,
                                    button=self.energymeterConnectButton, 
                                    progress_message="Подключение энергомера...")
        )
        self.motorConnectButton.clicked.connect(
            lambda: self.start_thread(EquipmentThreads.motor_connect, self.sm,
                                    button=self.motorConnectButton, 
                                    progress_message="Подключение мотора...")
        )
        self.motorConnectButtonSecond.clicked.connect(
            lambda: self.start_thread(EquipmentThreads.motor_connect_second, self.sm,
                                    button=self.motorConnectButtonSecond, 
                                    progress_message="Подключение мотора 2...")
        )
        self.oscilloscopeConnectButton.clicked.connect(
            lambda: self.start_thread(EquipmentThreads.oscilloscope_connect, self.sm,
                                    button=self.oscilloscopeConnectButton, 
                                    progress_message="Подключение осциллографа...")
        )
        
        self.GoSteps_MotorX.clicked.connect(
            lambda: self.start_thread(EquipmentThreads.go_by_steps_motorX, self.sm, 
                                    self.Steps_MotorX.value(),
                                    button=self.GoSteps_MotorX,
                                    progress_message="Движение мотором X...")
        )
        self.GoSteps_MotorZ.clicked.connect(
            lambda: self.start_thread(EquipmentThreads.go_by_steps_motorZ, self.sm,
                                    self.Steps_MotorZ.value(),
                                    button=self.GoSteps_MotorZ,
                                    progress_message="Движение мотором Z...")
        )
        self.goHomeButton.clicked.connect(
            lambda: self.start_thread(EquipmentThreads.go_home_motors, self.sm,
                                    self.UseOPOLazerRadioButton.isChecked(),
                                    self.UseDyeLazerRadioButton.isChecked(),
                                    button=self.goHomeButton, 
                                    progress_message="Возврат моторов в начальное положение...")
        )
        self.goToPushButton.clicked.connect(
            lambda: self.start_thread(EquipmentThreads.goto_wavelength, self.sm,
                                    self.goToSpinBox.value(), 
                                    self.UseDyeLazerRadioButton.isChecked(),
                                    button=self.goToPushButton, 
                                    progress_message="Перемещение на длину волны...")
        )
        self.goToPushButtonSecond.clicked.connect(
            lambda: self.start_thread(EquipmentThreads.goto_wavelength_by_motor, self.sm,
                                    self.goToSpinBoxSecond.value(),
                                    button=self.goToPushButtonSecond, 
                                    progress_message="Перемещение motor 2...")
        )
        
        self.recalibrateButton.clicked.connect(
            lambda: self.start_thread(EquipmentThreads.recalibrate, self.sm,
                                    self.wavemeterWavelengthLineEdit_2.text(),
                                    self.calibrationWavelengthLineEdit_2.text(),
                                    button=self.recalibrateButton, 
                                    progress_message="Перекалибровка...")
        )
        
        self.getSpectrumPushButton.clicked.connect(self.get_spectrum)
        self.getEnergyProfilePushButton.clicked.connect(self.get_energy)
        self.plotFullSpectrumButton.clicked.connect(self.plot_spectrum_from_integration)
        self.loadOscilloscopeFileButton.clicked.connect(self.load_oscilloscope_file)

        self.leftBoundarySpinBox.valueChanged.connect(self.leftBoundaryLine.setValue)
        self.rightBoundarySpinBox.valueChanged.connect(self.rightBoundaryLine.setValue)
        self.leftBoundaryLine.sigPositionChanged.connect(self.on_left_boundary_changed)
        self.rightBoundaryLine.sigPositionChanged.connect(self.on_right_boundary_changed)
        self.leftBoundarySpinBox.valueChanged.connect(self.update_integration)
        self.rightBoundarySpinBox.valueChanged.connect(self.update_integration)
        self.baselineComboBox.currentIndexChanged.connect(self.update_integration)

    def start_thread(self, target_function, *args, button=None, progress_message="Выполнение..."):
        if button:
            button.setEnabled(False)
            
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 0)
        self.cancelButton.setVisible(True)
        self.warningWindowLineEdit.setText(progress_message)
        
        thread = GenericThread(target_function, *args)
        thread.progress_signal.connect(self.warningWindowLineEdit.setText)
        thread.error_signal.connect(lambda error: self.on_thread_error(error, button))
        thread.finished_signal.connect(
            lambda result: self.on_thread_finished(result, button, target_function.__name__)
        )
        thread.start()
        
        self.current_thread = thread

    def on_thread_error(self, error_message, button=None):
        self.progressBar.setVisible(False)
        self.cancelButton.setVisible(False)
        if button:
            button.setEnabled(True)
        self.warningWindowLineEdit.setText(f"Ошибка: {error_message}")

    def on_thread_finished(self, result, button, method_name):
        self.progressBar.setVisible(False)
        self.cancelButton.setVisible(False)
        
        if button:
            button.setEnabled(True)
            
        if result:
            self.warningWindowLineEdit.setText(str(result))
            
        if method_name == "wavemeter_connect" and self.sm.wavemeter.is_connected:
            self.wavemeterConnectButton.setStyleSheet("background-color: green;")
        elif method_name == "energymeter_connect" and self.sm.energymeter.is_connected:
            self.energymeterConnectButton.setStyleSheet("background-color: green;")
        elif method_name == "motor_connect" and self.sm.printer.is_connected:
            self.motorConnectButton.setStyleSheet("background-color: green;")
        elif method_name == "motor_connect_second" and self.sm.motor.is_connected:
            self.motorConnectButtonSecond.setStyleSheet("background-color: green;")
        elif method_name == "oscilloscope_connect" and self.sm.oscilloscope.is_connected:
            self.oscilloscopeConnectButton.setStyleSheet("background-color: green;")
        elif method_name == "go_home_motors":
            self.goHomeButton.setStyleSheet("background-color: green;")

    def calculate_integral(self, x, y):
        left_bound = self.leftBoundarySpinBox.value()
        right_bound = self.rightBoundarySpinBox.value()
        baseline_type = self.baselineComboBox.currentText()
        return DataProcessor.calculate_integral_with_bounds(x, y, left_bound, right_bound, baseline_type)

    def update_integration(self):
        if hasattr(self, 'current_x') and hasattr(self, 'current_y'):
            baseline_type = self.baselineComboBox.currentText()
            intensity = self.calculate_integral(self.current_x, self.current_y)
            self.plot_baseline_if_needed()
            self.warningWindowLineEdit.setText(f"Интеграл: {intensity:.6e} (baseline: {baseline_type})")

    def plot_baseline_if_needed(self):
        if hasattr(self, 'baseline_curve'):
            self.oscilloscopePlot.removeItem(self.baseline_curve)
        
        left_bound = self.leftBoundarySpinBox.value()
        right_bound = self.rightBoundarySpinBox.value()
        baseline_type = self.baselineComboBox.currentText()
        
        mask = (self.current_x >= left_bound) & (self.current_x <= right_bound)
        x_filtered = self.current_x[mask]
        y_filtered = self.current_y[mask]
        
        if len(x_filtered) == 0:
            return

        baseline = DataProcessor._calculate_baseline(x_filtered, y_filtered, baseline_type)
        if baseline is not None:
            self.baseline_curve = self.oscilloscopePlot.plot(
                x_filtered, baseline, 
                pen=pg.mkPen('r', style=pg.QtCore.Qt.PenStyle.DashLine)
            )

    def load_oscilloscope_file(self):
        try:
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Выберите файл осциллографа", "", "Text Files (*.txt);;All Files (*)"
            )
            
            if not file_path:
                return

            x_data, y_data, wavelength = DataProcessor.load_oscilloscope_data(file_path)

            self.current_x = x_data
            self.current_y = y_data
            self.current_oscilloscope_data = (x_data, y_data, wavelength)
            self.current_folder_path = os.path.dirname(file_path)
            self.folderLineEdit.setText(self.current_folder_path)

            self.oscilloscopePlot.clear()
            self.oscilloscopeCurve = self.oscilloscopePlot.plot(x_data, y_data, pen='g')
            self.oscilloscopePlot.addItem(self.leftBoundaryLine)
            self.oscilloscopePlot.addItem(self.rightBoundaryLine)

            self.set_auto_plot_bounds(x_data, y_data)
            self.set_smart_integration_bounds(x_data, y_data)
            
            filename = os.path.basename(file_path)
            self.warningWindowLineEdit.setText(f"Файл загружен: {filename}, λ={wavelength} нм")
            
        except Exception as e:
            self.warningWindowLineEdit.setText(str(e))

    def set_auto_plot_bounds(self, x_data, y_data):
        x_min, x_max, y_min, y_max = DataProcessor.get_auto_plot_bounds(x_data, y_data)
        self.oscilloscopePlot.setXRange(x_min, x_max, padding=0)
        self.oscilloscopePlot.setYRange(y_min, y_max, padding=0)

    def set_smart_integration_bounds(self, x_data, y_data):
        left_bound, right_bound = DataProcessor.get_smart_integration_bounds(x_data, y_data)
        
        self.leftBoundarySpinBox.blockSignals(True)
        self.rightBoundarySpinBox.blockSignals(True)
        
        self.leftBoundarySpinBox.setValue(left_bound)
        self.rightBoundarySpinBox.setValue(right_bound)
        
        self.leftBoundarySpinBox.blockSignals(False)
        self.rightBoundarySpinBox.blockSignals(False)
        
        self.leftBoundaryLine.setValue(left_bound)
        self.rightBoundaryLine.setValue(right_bound)

    def on_left_boundary_changed(self, line):
        value = line.value()
        self.leftBoundarySpinBox.blockSignals(True)
        self.leftBoundarySpinBox.setValue(value)
        self.leftBoundarySpinBox.blockSignals(False)
        self.update_integration()

    def on_right_boundary_changed(self, line):
        value = line.value()
        self.rightBoundarySpinBox.blockSignals(True)
        self.rightBoundarySpinBox.setValue(value)
        self.rightBoundarySpinBox.blockSignals(False)
        self.update_integration()

    @pyqtSlot()
    def get_spectrum(self) -> None:
        if not self.sm.oscilloscope.is_connected:
            self.warningWindowLineEdit.setText("Осциллограф не подключен!")
            return
        if not self.filenameLineEdit.text():
            self.warningWindowLineEdit.setText("Пустое имя файла!")
            return

        self.getSpectrumPushButton.setEnabled(False)
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 0)  
        self.cancelButton.setVisible(True)
    
        kwargs = {  
            'wavelength_min': self.wavelengthStartSpinBox.value(),
            'wavelength_max': self.wavelengthEndSpinBox.value(),
            'average_count': self.averageCountSpinBox.value(),
            'wavelength_step': self.wavelengthStepSpinBox.value(),
            'folder': self.folderLineEdit.text(),
            'inspect_energy': self.InspecEnergy.isChecked(),
            'energy_limit': self.EnergyAccurace.value() / 1000,
            'use_opo': self.UseOPOLazerRadioButton.isChecked()
        }

        self.experiment_thread = ExperimentThread(self.sm, "spectrum", **kwargs)
        self.experiment_thread.finished_signal.connect(self.on_experiment_finished)
        self.experiment_thread.progress_signal.connect(self.warningWindowLineEdit.setText)
        self.experiment_thread.error_signal.connect(self.on_experiment_error)
        self.experiment_thread.start()

    @pyqtSlot()
    def get_energy(self) -> None:
        if not self.sm.printer.is_connected:
            self.warningWindowLineEdit.setText("Мотор не подключен!")
            return
        if not self.sm.energymeter.is_connected:
            self.warningWindowLineEdit.setText("Энергомер не подключен!")
            return
        if not self.filenameLineEdit.text():
            self.warningWindowLineEdit.setText("Пустое имя файла!")
            return

        self.getEnergyProfilePushButton.setEnabled(False)
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 0)
        self.cancelButton.setVisible(True)
        
        kwargs = {
            'wavelength_min': self.wavelengthStartSpinBox.value(),
            'wavelength_max': self.wavelengthEndSpinBox.value(),
            'average_count': self.averageCountSpinBox.value(),
            'wavelength_step': self.wavelengthStepSpinBox.value(),
            'folder': self.folderLineEdit.text(),
            'first_harmonic_energy': self.FirstHarmonicEnergy.isChecked(),
            'energy_limit': self.EnergyAccurace.value(),
            'use_opo': self.UseOPOLazerRadioButton.isChecked()
        }
        
        self.experiment_thread = ExperimentThread(self.sm, "energy", **kwargs)
        self.experiment_thread.finished_signal.connect(self.on_experiment_finished)
        self.experiment_thread.progress_signal.connect(self.warningWindowLineEdit.setText)
        self.experiment_thread.error_signal.connect(self.on_experiment_error)
        self.experiment_thread.start()

    @pyqtSlot()
    def plot_spectrum_from_integration(self):
        try:
            if self.current_folder_path is None:
                folder_path = self.folderLineEdit.text()
                if not folder_path or not os.path.exists(folder_path):
                    self.warningWindowLineEdit.setText("Укажите корректный путь к папке!")
                    return
                self.current_folder_path = folder_path

            left_bound = self.leftBoundarySpinBox.value()
            right_bound = self.rightBoundarySpinBox.value()
            baseline_type = self.baselineComboBox.currentText()
            
            if left_bound >= right_bound:
                self.warningWindowLineEdit.setText("Левая граница должна быть меньше правой!")
                return

            self.plotFullSpectrumButton.setEnabled(False)
            self.progressBar.setVisible(True)
            self.progressBar.setRange(0, 0)
            self.cancelButton.setVisible(True)

            self.file_processing_thread = FileProcessingThread(
                DataProcessor,  
                self.current_folder_path, left_bound, right_bound, baseline_type
            )
            self.file_processing_thread.finished_signal.connect(self.on_spectrum_processed)
            self.file_processing_thread.progress_signal.connect(self.warningWindowLineEdit.setText)
            self.file_processing_thread.error_signal.connect(self.on_experiment_error)
            self.file_processing_thread.start()
            
        except Exception as e:
            self.warningWindowLineEdit.setText(f"Ошибка: {str(e)}")

    @pyqtSlot()
    def on_experiment_finished(self):
        self.progressBar.setVisible(False)
        self.getSpectrumPushButton.setEnabled(True)
        self.getEnergyProfilePushButton.setEnabled(True)
        self.cancelButton.setVisible(False)
        self.warningWindowLineEdit.setText("Эксперимент завершён!")

    @pyqtSlot(list, list)
    def on_spectrum_processed(self, wavelengths, intensities):
        self.progressBar.setVisible(False)
        self.plotFullSpectrumButton.setEnabled(True)
        self.cancelButton.setVisible(False)
        
        if wavelengths and intensities:
            self.intensityCurve.setData(wavelengths, intensities)
            self.intensityPlot.autoRange()
            self.spectrum_data = (wavelengths, intensities)
            self.warningWindowLineEdit.setText(f"Спектр построен: {len(wavelengths)} точек")
        else:
            self.warningWindowLineEdit.setText("Не удалось обработать файлы!")

    @pyqtSlot(str)
    def on_experiment_error(self, error_message):
        self.progressBar.setVisible(False)
        self.getSpectrumPushButton.setEnabled(True)
        self.getEnergyProfilePushButton.setEnabled(True)
        self.plotFullSpectrumButton.setEnabled(True)
        self.cancelButton.setVisible(False)
        self.warningWindowLineEdit.setText(f"Ошибка: {error_message}")

    @pyqtSlot()
    def cancel_operation(self):
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.terminate()
            self.current_thread.wait()
        self.progressBar.setVisible(False)
        self.cancelButton.setVisible(False)
        self.warningWindowLineEdit.setText("Операция отменена")

    def update_spectrum_display(self, x_data, y_data, wavelength):
        self.oscilloscopeCurve.setData(x_data, y_data)
        self.update_integration()
        self.wavelengths.append(wavelength)
        intensity = self.calculate_integral(x_data, y_data)
        self.intensities.append(intensity)
        self.intensityCurve.setData(self.wavelengths, self.intensities)

    def update_global(self) -> None:
        self.pushButton.setText("Random button")
        n = random.random()
        if n < 0.33:
            self.pushButton.setStyleSheet("background-color: green;")
        elif n > 0.66:
            self.pushButton.setStyleSheet("background-color: yellow;")
        else:
            self.pushButton.setStyleSheet("background-color: blue;")

        if self.sm.wavemeter.is_connected:
            wavelength = str(self.sm.wavemeter.get_wavelength(force=True))[:7]
            self.wavemeterWavelengthLineEdit.setText(wavelength)
            self.wavemeterWavelengthLineEdit_2.setText(wavelength)

    def real_talk(self) -> None:
        self.pushButton.setText("Clicked!")

    @pyqtSlot()
    def change_frequency(self):
        pass

    @pyqtSlot()
    def change_refresh_rate(self) -> None:
        self.timer.setInterval(self.refreshRateSpinBox.value())

    @pyqtSlot()
    def show_warning_message(self, message: str) -> None:
        self.warningWindowLineEdit.setText(message)
        self.warningWindowLineEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    def translate_to_wavelength(self, x: int) -> str:
        if (self.UseDyeLazerRadioButton.isChecked() == 1):
            file = open("full_calibration.txt", 'r')
        elif (self.UseOPOLazerRadioButton.isChecked() == 1):
            file = open("full_calibration_OPO.txt", 'r')
        for line in file:
            motor_1 = int(line.strip().split('\t')[2])
            if motor_1 == x:
                file.close()
                return (line.strip().split('\t')[0].replace(',', '.'))
        file.close()
        return "нет калибровки"

    def spinboxes_limits_init(self) -> None:
        k = 0
        if (self.UseDyeLazerRadioButton.isChecked() == 1):
            file = open("full_calibration.txt", 'r')
            for line in file:
                wavelength = (line.strip().split('\t')[0].replace(',', '.'))[:7]
                if k == 0:
                    self.goToSpinBox.setMinimum(float(wavelength))
                    self.wavelengthStartSpinBox.setMinimum(float(wavelength))
                    self.wavelengthEndSpinBox.setMinimum(float(wavelength))
                    k+=1
            self.goToSpinBox.setMaximum(float(wavelength))
            self.wavelengthStartSpinBox.setMaximum(float(wavelength))
            self.wavelengthEndSpinBox.setMaximum(float(wavelength))
            file.close()
        elif (self.UseOPOLazerRadioButton.isChecked() == 1):
            file = open("full_calibration_OPO.txt", 'r')
            for line in file:
                wavelength = (line.strip().split('\t')[0].replace(',', '.'))[:7]
                if k == 0:
                    self.goToSpinBoxSecond.setMinimum(float(wavelength))
                    self.wavelengthStartSpinBox.setMinimum(float(wavelength))
                    self.wavelengthEndSpinBox.setMinimum(float(wavelength))
                    k+=1
            self.goToSpinBoxSecond.setMaximum(float(wavelength))
            self.wavelengthStartSpinBox.setMaximum(float(wavelength))
            self.wavelengthEndSpinBox.setMaximum(float(wavelength))
            file.close()
    
    def go_relative_with_check(self, id: int, steps: int, target_wavelenght: float):
        step_number = 1
        if(abs(steps) <= 4000 and id !=1):
            step_number = 5
        elif (abs(steps) > 4000 and id !=1 and abs(steps) <= 12000): 
            step_number = 20
        elif(abs(steps) > 12000 and id !=1):
            step_number = 50
        if not self.sm.printer.is_connected:
            print("Устройство не подключено!")
            return
        step_tmp = steps/step_number
        
        while (abs(step_tmp) <= abs(steps)):
            mm_distance = -(steps/step_number) * self.sm.printer.mm_to_steps
            axis = "Z" if id == 1 else "X"
            self.sm.printer.set_position(axis, mm_distance, speed=50, relative=True)
            if (abs(step_tmp) > 5000):
                time.sleep(3.5)
            if (abs(step_tmp) > 1800):
                time.sleep(2.2)
            elif(abs(step_tmp) > 750):
                time.sleep(1.75)
            elif(abs(step_tmp) > 350):
                time.sleep(0.9)
            else:
                time.sleep(0.2)
            current_wavelenght = self.sm.wavemeter.get_wavelength()
            if (abs(target_wavelenght - current_wavelenght) < 0.5 and abs(target_wavelenght - current_wavelenght) > 0.1):
                break
            step_tmp += steps/step_number
    
    def get_average_wavelength(self):
        average_energy = 0
        for i in range(4):
            average_energy += self.sm.wavemeter.get_wavelength()
            time.sleep(0.2)
        return average_energy / 4

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
    window = MainWindow()
    window.show()
    app.exec()