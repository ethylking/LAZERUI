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
        self.wavemeterWavelengthLineEdit_2: QtWidgets.QLineEdit = self.wavemeterWavelengthLineEdit_2
        self.calibrationWavelengthLineEdit: QtWidgets.QLineEdit = self.calibrationWavelengthLineEdit
        self.calibrationWavelengthLineEdit_2: QtWidgets.QLineEdit = self.calibrationWavelengthLineEdit_2
        self.recalibrateButton: QPushButton = self.recalibrateButton
        self.goToSpinBox: QtWidgets.QDoubleSpinBox = self.goToSpinBox
        self.goToPushButton: QPushButton = self.goToPushButton
        self.averageCountSpinBox: QtWidgets.QSpinBox = self.averageCountSpinBox
        self.InspecEnergy: QtWidgets.QCheckBox = self.InspecEnergy
        self.goToSpinBoxSecond: QtWidgets.QDoubleSpinBox = self.goToSpinBoxSecond
        self.goToPushButtonSecond: QPushButton = self.goToPushButtonSecond
        self.motorConnectButtonSecond: QPushButton = self.motorConnectButtonSecond
        self.UseDyeLazerRadioButton: QtWidgets.QAbstractButton = self.UseDyeLazerRadioButton
        self.UseOPOLazerRadioButton: QtWidgets.QAbstractButton = self.UseOPOLazerRadioButton
        self.Steps_MotorX: QtWidgets.QSpinBox = self.Steps_MotorX
        self.Steps_MotorZ: QtWidgets.QSpinBox = self.Steps_MotorZ
        self.GoSteps_MotorX: QPushButton = self.GoSteps_MotorX
        self.GoSteps_MotorZ: QPushButton = self.GoSteps_MotorZ
        self.FirstHarmonicEnergy: QtWidgets.QCheckBox = self.FirstHarmonicEnergy
        self.EnergyAccurace: QtWidgets.QDoubleSpinBox = self.EnergyAccurace
        self.FrequencySpinBox: QtWidgets.QDoubleSpinBox = self.FrequencySpinBox

        self.Steps_MotorX.setMinimum(-1000)
        self.Steps_MotorX.setMaximum(1000)
        self.Steps_MotorZ.setMinimum(-1000)
        self.Steps_MotorZ.setMaximum(1000)
        self.setWindowTitle("Autospectromizer")
        self.show_warning_message('нет сообщений')
        self.pushButton.clicked.connect(self.real_talk)
        self.wavemeterConnectButton.setStyleSheet("background-color: red;")
        self.energymeterConnectButton.setStyleSheet("background-color: red;")
        self.motorConnectButton.setStyleSheet("background-color: red;")
        self.motorConnectButtonSecond.setStyleSheet("background-color: red;")
        self.oscilloscopeConnectButton.setStyleSheet("background-color: red;")
        self.wavemeterConnectButton.clicked.connect(self.wavemeter_connect)
        self.refreshRateSpinBox.valueChanged.connect(self.change_refresh_rate)
        self.FrequencySpinBox.valueChanged.connect(self.change_frequency)
        self.energymeterConnectButton.clicked.connect(self.energymeter_connect)
        self.wavemeterConnectButton.clicked.connect(self.wavemeter_connect)
        self.motorConnectButton.clicked.connect(self.motor_connect)
        self.motorConnectButtonSecond.clicked.connect(self.motor_connect_second)
        self.oscilloscopeConnectButton.clicked.connect(self.oscilloscope_connect)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_global)
        self.setMinimumSize(400,400)
        self.setMaximumSize(1800,800)
        self.timer.start(1000)
        self.refreshRateSpinBox.setValue(self.timer.interval())
        self.GoSteps_MotorX.clicked.connect(self.go_by_steps_motorX)
        self.GoSteps_MotorZ.clicked.connect(self.go_by_steps_motorZ)
        self.goHomeButton.clicked.connect(self.go_home_motors)
        self.goToPushButton.clicked.connect(self.goto_wavelength)
        self.goToPushButtonSecond.clicked.connect(self.goto_wavelength_by_motor)
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
            self.wavemeterWavelengthLineEdit_2.setText(str(self.sm.wavemeter.get_wavelength(force=True))[0:7])
        #if (self.sm.printer.is_connected and self.UseDyeLazerRadioButton.isChecked() == 1):
         #   self.calibrationWavelengthLineEdit.setText(self.translate_to_wavelength(self.sm.printer.get_steps_position(2)))
          #  self.calibrationWavelengthLineEdit_2.setText(self.translate_to_wavelength(self.sm.printer.get_steps_position(2)))
        if (self.sm.motor.is_connected and self.UseOPOLazerRadioButton.isChecked() == 1):
            self.calibrationWavelengthLineEdit_2.setText(self.translate_to_wavelength(self.sm.motor.get_position(1)))

    def real_talk(self) -> None:
        self.pushButton.setText("Clicked!")

    @pyqtSlot()
    def change_frequency(self):
        pass
        # self.sm.set_frequency(self.FrequencySpinBox.value())

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
    def motor_connect_second(self) -> None:
        try:
            self.sm.motor.connect()
            self.motorConnectButtonSecond.setStyleSheet("background-color: green;")
            self.warningWindowLineEdit.setText('motor 2 connected!')
            self.sm.motor.is_connected = True
        except:
            self.warningWindowLineEdit.setText(f'motor 2 not connected')
            self.motorConnectButtonSecond.setStyleSheet("background-color: red;")

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
            if(self.UseOPOLazerRadioButton.isDown()):
                self.sm.motor.go_home(1)
                self.sm.motor.go_home(2)
            elif(self.UseDyeLazerRadioButton.isDown()):
                self.sm.printer.go_home(1)
                self.sm.printer.go_home(2)
            self.warningWindowLineEdit.setText('Моторы в начальном положении!')
            self.goHomeButton.setStyleSheet("background-color: green;")
        else:
            self.goHomeButton.setStyleSheet("background-color: red;")

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
        z_check = 0
        while (abs(new_wavelength - current_wavelength) > 0.01):
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

            if z_steps != 0 and z_check != 1:
                self.sm.printer.go_relative(1, z_steps)
                z_check += 1
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
    def goto_wavelength_by_motor(self) -> None:
        if self.sm.motor.is_connected == False:
            pass
        else:
            print("here")
            step = 50
            # file = open("full_calibration_OPO.txt", 'r')
            # for line in file:
            #     wavelength = (line.strip().split('\t')[0].replace(',', '.'))[:7]
            #     if (float(new_wavelength) == float(wavelength)):
            #         print("bebebe")
            #         motor_1 = int(line.strip().split('\t')[1])
            #         motor_2 = int(line.strip().split('\t')[2])
            #         self.sm.motor.go_absolute(1, motor_1)
            #         self.sm.motor.go_absolute(2, motor_2)
            #         break
            # file.close()
            current_wavelength = self.sm.wavemeter.get_wavelength()
            self.sm.motor.go_relative(1, step)
            time.sleep(2)
            for_test_current_wavelength = self.sm.wavemeter.get_wavelength()
            new_wavelength = self.goToSpinBoxSecond.value()
            diff_wavelength = abs(new_wavelength - current_wavelength)
            right_way = True
            if (abs(new_wavelength - for_test_current_wavelength) > diff_wavelength):
                right_way = False
            up = False
            down = False
            if (new_wavelength > current_wavelength):
                up = True
            if (new_wavelength < current_wavelength):
                down = True
            while (abs(diff_wavelength) > 0.01):
                current_wavelength = self.sm.wavemeter.get_wavelength()
                time.sleep(1)
                diff_wavelength = abs(new_wavelength - current_wavelength)
                if (diff_wavelength > 100):
                    step = 500
                if (diff_wavelength < 20):
                    step = 300
                if (diff_wavelength <= 5):
                    step = 30
                if (diff_wavelength <= 0.2):
                    step = 5
                if (right_way == False):
                    step = -step
                self.sm.motor.go_relative(1, step)
                self.sm.motor.wait_for_free(1)
                self.sm.motor.go_relative(2, step)
                #self.sm.motor.wait_for_free(2)
                if ((up and (new_wavelength < current_wavelength)) or (down and (new_wavelength > current_wavelength))):
                    break
            right_way = True

                

    @pyqtSlot()
    def recalibrate(self) -> None:
        if self.sm.wavemeter.is_connected and self.sm.motor.is_connected:
            real_wavelength = self.wavemeterWavelengthLineEdit_2.text()
            cal_wavelength = self.calibrationWavelengthLineEdit_2.text()
            if (real_wavelength in ['under', 'over'] or cal_wavelength == 'no calibration here'):
                return
            else:
                real_wavelength = int(float(real_wavelength) * 1000)
                cal_wavelength = int(float(cal_wavelength) * 1000)
                diff = real_wavelength - cal_wavelength
                file = open("full_calibration_OPO.txt", 'r')
                new_file = open("temp_calibration_OPO.txt", 'w')
                for line in file:
                    wavelength = (int(float((line.strip().split('\t')[0].replace(',', '.'))[:7]) * 1000) + diff) / 1000
                    motor_1 = int(line.strip().split('\t')[1])
                    motor_2 = int(line.strip().split('\t')[2])
                    new_file.write(f"{str(wavelength)[:7]}\t{motor_1}\t{motor_2}\n")
                file.close()
                new_file.close()
                os.remove('full_calibration_OPO.txt')
                os.rename('temp_calibration_OPO.txt', 'full_calibration_OPO.txt')
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
        inspect_energy = self.InspecEnergy.isChecked()
        # energy_limit = self.EnergyAccurace.value()
        if (self.UseOPOLazerRadioButton.isChecked() == 1):
            self.sm.get_spectrum_by_motor(wavelength_min=wavelength_min, wavelength_max=wavelength_max, average_count=average_count,
                             wavelength_step=wavelength_step, folder=folder)
        elif(self.UseDyeLazerRadioButton.isChecked() == 1):
            self.sm.get_spectrum(wavelength_min=wavelength_min, wavelength_max=wavelength_max, average_count=average_count,
                             wavelength_step=wavelength_step, folder=folder, inspect_energy = inspect_energy, energy_limit = 0.0002)
        
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
        energy_limit = self.EnergyAccurace.value()
        first_harmonic_energy = self.FirstHarmonicEnergy.isChecked()
        if (self.UseOPOLazerRadioButton.isChecked()):
            self.sm.get_energy_profile_by_motor(wavelength_min=wavelength_min, wavelength_max=wavelength_max, average_count=average_count,
                                wavelength_step=wavelength_step, folder=folder)
        elif(self.UseDyeLazerRadioButton.isChecked()):
            self.sm.get_energy_profile(wavelength_min=wavelength_min, wavelength_max=wavelength_max, average_count=average_count,
                                wavelength_step=wavelength_step, folder=folder, first_harmonic_energy = first_harmonic_energy, energy_limit = energy_limit)
        self.warningWindowLineEdit.setText("Эксперимент завершён!")
    
    @pyqtSlot()
    def go_by_steps_motorX(self):
        steps = self.Steps_MotorX.value()
        self.sm.printer.go_relative(2 , steps)

    @pyqtSlot()
    def go_by_steps_motorZ(self):
        steps = self.Steps_MotorZ.value()
        self.sm.printer.go_relative(1 , steps)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
    window = MainWindow()
    window.show()
    app.exec()
