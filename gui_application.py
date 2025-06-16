from PyQt6.QtWidgets import QMainWindow, QMessageBox, QApplication
from PyQt6 import QtWidgets, uic, QtCore
import sys
import random
import contextlib
import os
from spectramaker import *

Design, _ = uic.loadUiType('gui_window.ui')

class MainWindow(QMainWindow, Design):
    def __init__(self):
        self.sm = Spectramaker()
        super().__init__()

        self.setupUi(self)
        self.wavemeterConnectButton: QPushButton = self.wavemeterConnectButton
        self.energymeterConnectButton: QPushButton = self.energymeterConnectButton
        self.motorConnectButton: QPushButton = self.motorConnectButton
        self.oscilloscopeConnectButton: QPushButton = self.oscilloscopeConnectButton
        self.getEnergyProfilePushButton: QPushButton = self.getEnergyProfilePushButton
        self.getSpectrumPushButton: QPushButton = self.getSpectrumPushButton
        self.warningWindowLineEdit: QtWidgets.QLineEdit = self.warningWindowLineEdit
        self.wavelengthStartSpinBox: QtWidgets.QDoubleSpinBox = self.wavelengthStartSpinBox
        self.wavelengthEndSpinBox: QtWidgets.QDoubleSpinBox = self.wavelengthEndSpinBox
        self.filenameLineEdit: QtWidgets.QLineEdit = self.filenameLineEdit
        self.folderLineEdit: QtWidgets.QLineEdit = self.folderLineEdit
        self.refreshRateSpinBox: QtWidgets.QSpinBox = self.refreshRateSpinBox
        self.wavelengthStepSpinBox: QtWidgets.QDoubleSpinBox = self.wavelengthStepSpinBox
        self.goHomeButton: QPushButton = self.goHomeButton
        self.wavemeterWavelengthLineEdit: QtWidgets.QLineEdit = self.wavemeterWavelengthLineEdit
        self.calibrationWavelengthLineEdit: QtWidgets.QLineEdit = self.calibrationWavelengthLineEdit
        self.recalibrateButton: QPushButton = self.recalibrateButton
        self.goToSpinBox: QtWidgets.QDoubleSpinBox = self.goToSpinBox
        self.goToPushButton: QPushButton = self.goToPushButton
        self.averageCountSpinBox: QtWidgets.QSpinBox = self.averageCountSpinBox
        self.InspecEnergy: QtWidgets.QCheckBox = self.InspecEnergy

        self.setWindowTitle("Autospectromizer")
        self.show_warning_message('нет сообщений')
        self.pushButton.clicked.connect(self.real_talk)
        self.wavemeterConnectButton.setStyleSheet("background-color: red;")
        self.energymeterConnectButton.setStyleSheet("background-color: red;")
        self.motorConnectButton.setStyleSheet("background-color: red;")
        self.oscilloscopeConnectButton.setStyleSheet("background-color: red;")
        self.wavemeterConnectButton.clicked.connect(self.wavemeter_connect)
        self.refreshRateSpinBox.valueChanged.connect(self.change_refresh_rate)
        self.energymeterConnectButton.clicked.connect(self.energymeter_connect)
        self.wavemeterConnectButton.clicked.connect(self.wavemeter_connect)
        self.motorConnectButton.clicked.connect(self.motor_connect)
        self.oscilloscopeConnectButton.clicked.connect(self.oscilloscope_connect)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_global)
        self.setMinimumSize(915,600)
        self.setMaximumSize(1800,800)
        self.timer.start(1000)
        self.refreshRateSpinBox.setValue(self.timer.interval())
        self.goHomeButton.clicked.connect(self.go_home_motors)
        self.goToPushButton.clicked.connect(self.goto_wavelength)
        self.recalibrateButton.clicked.connect(self.recalibrate)
        self.getSpectrumPushButton.clicked.connect(self.get_spectrum)
        self.getEnergyProfilePushButton.clicked.connect(self.get_energy)

        self.spinboxes_limits_init()

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
            self.wavemeterWavelengthLineEdit.setText(str(self.sm.wavemeter.get_wavelength(force=True))[0:7])
        #if self.sm.printer.is_connected:
            #self.calibrationWavelengthLineEdit.setText(self.translate_to_wavelength(self.sm.printer.get_steps_position(2)))

    def real_talk(self) -> None:
        self.pushButton.setText("Clicked!")

    @pyqtSlot()
    def change_refresh_rate(self) -> None:
        self.timer.setInterval(self.refreshRateSpinBox.value())

    @pyqtSlot()
    def energymeter_connect(self) -> None:
        for i in range(3, 10):
            try:
                self.sm.energymeter.connect(i)
                self.energymeterConnectButton.setStyleSheet("background-color: green;")
                self.warningWindowLineEdit.setText('энергомер подключен!')
                self.sm.energymeter.is_connected = True
                break
            except:
                self.warningWindowLineEdit.setText(f'энергомер не подключен на COM{i}')
                self.energymeterConnectButton.setStyleSheet("background-color: red;")

    @pyqtSlot()
    def wavemeter_connect(self) -> None:
        with contextlib.suppress(OSError):
            try:
                self.sm.wavemeter.connect()
                self.wavemeterConnectButton.setStyleSheet("background-color: green;")
                self.warningWindowLineEdit.setText('измеритель длины волны подключен!')
                self.sm.wavemeter.is_connected = True
            except:
                self.wavemeterConnectButton.setStyleSheet("background-color: red;")
                self.warningWindowLineEdit.setText('измеритель длины волны не подключен!')

    @pyqtSlot()
    def motor_connect(self) -> None:
        try:
            success = self.sm.printer.connect()
            if success:
                self.motorConnectButton.setStyleSheet("background-color: green;")
                self.warningWindowLineEdit.setText('мотор подключен!')
                self.sm.printer.is_connected = True
            else:
                self.warningWindowLineEdit.setText('мотор не подключен: сбой соединения')
                self.motorConnectButton.setStyleSheet("background-color: red;")
        except Exception as e:
            self.warningWindowLineEdit.setText(f'мотор не подключен: {str(e)}')
            self.motorConnectButton.setStyleSheet("background-color: red;")

    @pyqtSlot()
    def oscilloscope_connect(self) -> None:
        try:
            self.sm.oscilloscope.connect()
            self.oscilloscopeConnectButton.setStyleSheet("background-color: green;")
            self.warningWindowLineEdit.setText('осциллограф подключен!')
            self.sm.oscilloscope.is_connected = True
        except:
            self.warningWindowLineEdit.setText('осциллограф не подключен')
            self.oscilloscopeConnectButton.setStyleSheet("background-color: red;")

    @pyqtSlot()
    def show_warning_message(self, message: str) -> None:
        self.warningWindowLineEdit.setText(message)
        self.warningWindowLineEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)

    @pyqtSlot()
    def go_home_motors(self) -> None:
        if self.sm.printer.is_connected:
            self.update()
            self.sm.printer.go_home(1)
            self.sm.printer.go_home(2)
            self.warningWindowLineEdit.setText('Моторы в начальном положении!')
            self.goHomeButton.setStyleSheet("background-color: green;")
        else:
            self.goHomeButton.setStyleSheet("background-color: red;")

    def translate_to_wavelength(self, x: int) -> str:
        file = open("full_calibration.txt", 'r')
        for line in file:
            motor_1 = int(line.strip().split('\t')[2])
            if motor_1 == x:
                file.close()
                return (line.strip().split('\t')[0].replace(',', '.'))
        file.close()
        return "нет калибровки"

    def spinboxes_limits_init(self) -> None:
        file = open("full_calibration.txt", 'r')
        k = 0
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

    @pyqtSlot()
    def goto_wavelength(self) -> None:
        if not self.sm.printer.is_connected:
            QMessageBox.critical(self, "Ошибка", "Принтер не подключен!")
            return

        new_wavelength = self.goToSpinBox.value()
        current_wavelength = self.sm.wavemeter.get_wavelength()
        if not isinstance(current_wavelength, float):
            QMessageBox.critical(self, "Ошибка", "Некорректное значение длины волны!")
            return

        calibration_data = []
        try:
            with open("full_calibration.txt", 'r') as file:
                for line in file:
                    parts = line.strip().split('\t')
                    wavelength_val = float(parts[0].replace(',', '.'))
                    motor_1_steps = int(parts[1])
                    motor_2_steps = int(parts[2])
                    calibration_data.append((wavelength_val, motor_1_steps, motor_2_steps))
        except FileNotFoundError:
            QMessageBox.critical(self, "Ошибка", "Калибровочный файл не найден!")
            return

        current_steps_1 = 0
        current_steps_2 = 0
        target_steps_1 = 0
        target_steps_2 = 0
        found_current = False
        found_target = False
        while (abs(new_wavelength - current_wavelength) > 0.005):
            for wavelength_val, steps_1, steps_2 in calibration_data:
                if abs(wavelength_val - current_wavelength) < 0.001:
                    current_steps_1 = steps_1
                    current_steps_2 = steps_2
                    found_current = True
                if abs(wavelength_val - new_wavelength) < 0.001:
                    target_steps_1 = steps_1
                    target_steps_2 = steps_2
                    found_target = True

            if not found_current or not found_target:
                QMessageBox.critical(self, "Ошибка", "Текущая или целевая длина волны не найдена в калибровочном файле!")
                return

            z_steps = target_steps_1 - current_steps_1
            x_steps = target_steps_2 - current_steps_2

            if z_steps != 0:
                self.sm.printer.go_relative(1, z_steps)
            if x_steps != 0:
                self.go_relative_with_check(2, x_steps, new_wavelength)
            x_steps = 0
            z_steps = 0
            if(z_steps > 400 or x_steps > 600):
                time.sleep(5)
            else:
                time.sleep(2)
            while (True):
                current_wavelength = self.sm.wavemeter.get_wavelength()
                time.sleep(0.5)
                wavelength_tmp = self.sm.wavemeter.get_wavelength()
                if (type(current_wavelength) == float and type(wavelength_tmp) == float and abs(wavelength_tmp - current_wavelength) < 0.01):
                    break
        QMessageBox.information(self, "Успех", f"Перемещение на длину волны {new_wavelength}: Z-мотор на {z_steps} шагов, X-мотор на {x_steps} шагов")

    @pyqtSlot()
    def recalibrate(self) -> None:
        if self.sm.wavemeter.is_connected and self.sm.printer.is_connected:
            real_wavelength = self.wavemeterWavelengthLineEdit.text()
            cal_wavelength = self.calibrationWavelengthLineEdit.text()
            if (real_wavelength in ['under', 'over'] or cal_wavelength == 'нет калибровки'):
                return
            else:
                real_wavelength = int(float(real_wavelength) * 1000)
                cal_wavelength = int(float(cal_wavelength) * 1000)
                diff_wave = real_wavelength - cal_wavelength
                
                file = open("full_calibration.txt", 'r')
                new_file = open("temp_calibration.txt", 'w')
                for line in file:
                    wavelength = (int(float((line.strip().split('\t')[0].replace(',', '.'))[:7]) * 1000) + diff_wave) / 1000
                    motor_1 = int(line.strip().split('\t')[1])
                    motor_2 = int(line.strip().split('\t')[2])
                    new_file.write(f"{str(wavelength)[:7]}\t{motor_1}\t{motor_2}\n")
                file.close()
                new_file.close()
                os.remove('full_calibration.txt')
                os.rename('temp_calibration.txt', 'full_calibration.txt')
                self.spinboxes_limits_init()

    @pyqtSlot()
    def get_spectrum(self) -> None:
        if self.sm.printer.is_connected == False:
            self.warningWindowLineEdit.setText("Мотор не подключен!")
            return
        if self.sm.oscilloscope.is_connected == False:
            self.warningWindowLineEdit.setText("Осциллограф не подключен!")
            return
        if self.filenameLineEdit.text() == "":
            self.warningWindowLineEdit.setText("Пустое имя файла!")
            return
        folder = self.folderLineEdit.text()
        average_count = self.averageCountSpinBox.value()
        wavelength_step = self.wavelengthStepSpinBox.value()
        wavelength_min = self.wavelengthStartSpinBox.value()
        wavelength_max = self.wavelengthEndSpinBox.value()
        inspect_energy = self.InspecEnergy.checkState()
        self.sm.get_spectrum(wavelength_min=wavelength_min, wavelength_max=wavelength_max, average_count=average_count,
                             wavelength_step=wavelength_step, folder=folder, inspect_energy = inspect_energy)
        self.warningWindowLineEdit.setText("Эксперимент завершён!")

    @pyqtSlot()
    def get_energy(self) -> None:
        if self.sm.printer.is_connected == False:
            self.warningWindowLineEdit.setText("Мотор не подключен!")
            return
        if self.sm.energymeter.is_connected == False:
            self.warningWindowLineEdit.setText("энергомер не подключен!")
            return
        if self.filenameLineEdit.text() == "":
            self.warningWindowLineEdit.setText("Пустое имя файла!")
            return
        folder = self.folderLineEdit.text()
        average_count = self.averageCountSpinBox.value()
        wavelength_step = self.wavelengthStepSpinBox.value()
        wavelength_min = self.wavelengthStartSpinBox.value()
        wavelength_max = self.wavelengthEndSpinBox.value()
        self.sm.get_energy_profile(wavelength_min=wavelength_min, wavelength_max=wavelength_max, average_count=average_count,
                             wavelength_step=wavelength_step, folder=folder)
        self.warningWindowLineEdit.setText("Эксперимент завершён!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
    window = MainWindow()
    window.show()
    app.exec()
