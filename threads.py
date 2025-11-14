from PyQt6.QtCore import pyqtSignal, QThread
import contextlib
import time
from PyQt6.QtWidgets import QMessageBox
from data_processor import DataProcessor
import spectramaker as sm
import os

class GenericThread(QThread):
    finished_signal = pyqtSignal(object)
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, target_function, *args,  **kwargs):
        super().__init__()
        self.target_function = target_function
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            result = self.target_function(*self.args, **self.kwargs)
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))

class ExperimentThread(QThread):
    finished_signal = pyqtSignal()
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, sm, experiment_type, **kwargs):
        super().__init__()
        self.sm = sm
        self.experiment_type = experiment_type
        self.kwargs = kwargs
        
    def run(self):
        try:
            if self.experiment_type == "spectrum":
                self.progress_signal.emit("Начало измерения спектра...")
                if self.kwargs.get('use_opo', False):
                    self.sm.get_spectrum_by_motor(**self.kwargs)
                else:
                    self.sm.get_spectrum(**self.kwargs)
                    
            elif self.experiment_type == "energy":
                self.progress_signal.emit("Начало измерения энергетического профиля...")
                if self.kwargs.get('use_opo', False):
                    self.sm.get_energy_profile_by_motor(**self.kwargs)
                else:
                    self.sm.get_energy_profile(**self.kwargs)
                    
            self.finished_signal.emit()
            
        except Exception as e:
            self.error_signal.emit(str(e))

class FileProcessingThread(QThread):
    finished_signal = pyqtSignal(list, list)
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, data_processor, folder_path, left_bound, right_bound, baseline_type):
        super().__init__()
        self.data_processor = data_processor
        self.folder_path = folder_path
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.baseline_type = baseline_type
        
    def run(self):
        try:
            self.progress_signal.emit("Обработка файлов...")
            wavelengths, intensities = self.data_processor.process_spectrum_files(
                self.folder_path, self.left_bound, self.right_bound, self.baseline_type
            )
            self.progress_signal.emit(f"Успешно обработано: {len(wavelengths)} файлов")
            self.finished_signal.emit(wavelengths, intensities)
            
        except Exception as e:
            self.error_signal.emit(str(e))

class EquipmentThreads:
    
    @staticmethod
    def wavemeter_connect(sm):
        with contextlib.suppress(OSError):
            sm.wavemeter.connect()
            sm.wavemeter.is_connected = True
            return "Измеритель длины волны подключен!"
        raise Exception("Измеритель длины волны не подключен!")

    @staticmethod
    def energymeter_connect(sm):
        for i in range(3, 10):
            try:
                sm.energymeter.connect(i)
                sm.energymeter.is_connected = True
                return f"Энергомер подключен на COM{i}!"
            except:
                continue
        raise Exception("Энергомер не подключен!")

    @staticmethod
    def motor_connect(sm):
        success = sm.printer.connect()
        if success:
            sm.printer.is_connected = True
            return "Мотор подключен!"
        else:
            raise Exception("Мотор не подключен: сбой соединения")

    @staticmethod
    def motor_connect_second(sm):
        sm.motor.connect()
        sm.motor.is_connected = True
        return "Motor 2 connected!"

    @staticmethod
    def oscilloscope_connect(sm):
        sm.oscilloscope.connect()
        sm.oscilloscope.is_connected = True
        return "Осциллограф подключен!"

    @staticmethod
    def go_by_steps_motorX(sm, steps):
        sm.printer.go_relative(2, steps)
        return f"Мотор X перемещен на {steps} шагов"

    @staticmethod
    def go_by_steps_motorZ(sm, steps):
        sm.printer.go_relative(1, steps)
        return f"Мотор Z перемещен на {steps} шагов"

    @staticmethod
    def go_home_motors(sm, use_opo, use_dye):
        if not sm.printer.is_connected:
            raise Exception("Мотор не подключен!")
        
        if use_opo:
            sm.motor.go_home(1)
            sm.motor.go_home(2)
        elif use_dye:
            sm.printer.go_home(1)
            sm.printer.go_home(2)
        
        return "Моторы в начальном положении!"

    @staticmethod
    def goto_wavelength(sm, wavelength, use_dye_calibration=True):
        if not sm.printer.is_connected:
            raise Exception("Принтер не подключен!")

        new_wavelength = wavelength
        current_wavelength = sm.wavemeter.get_wavelength()
        if not isinstance(current_wavelength, float):
            raise Exception("Некорректное значение длины волны!")

        cal_file = "full_calibration.txt"
        
        calibration_data = []
        try:
            with open(cal_file, 'r') as file:
                for line in file:
                    parts = line.strip().split('\t')
                    wavelength_val = float(parts[0].replace(',', '.'))
                    motor_1_steps = int(parts[1])
                    motor_2_steps = int(parts[2])
                    calibration_data.append((wavelength_val, motor_1_steps, motor_2_steps))
        except FileNotFoundError:
            raise Exception("Калибровочный файл не найден!")

        current_steps_1 = 0
        current_steps_2 = 0
        target_steps_1 = 0
        target_steps_2 = 0
        found_current = False
        found_target = False
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
                raise Exception("Текущая или целевая длина волны не найдена в калибровочном файле!")

            z_steps = target_steps_1 - current_steps_1
            x_steps = target_steps_2 - current_steps_2

            if z_steps != 0:
                sm.printer.go_relative(1, z_steps)
            if x_steps != 0:
                EquipmentThreads._go_relative_with_check(sm, 2, x_steps, new_wavelength)

        return f"Перемещение на длину волны {new_wavelength} завершено"

    @staticmethod
    def _go_relative_with_check(sm, id, steps, target_wavelength):
        step_number = 1
        if abs(steps) <= 4000 and id != 1:
            step_number = 5
        elif abs(steps) > 4000 and id != 1 and abs(steps) <= 12000: 
            step_number = 20
        elif abs(steps) > 12000 and id != 1:
            step_number = 50
        
        step_tmp = steps / step_number
        
        while abs(step_tmp) <= abs(steps):
            mm_distance = -(steps / step_number) * sm.printer.mm_to_steps
            axis = "Z" if id == 1 else "X"
            sm.printer.set_position(axis, mm_distance, speed=50, relative=True)
            
            if abs(step_tmp) > 5000:
                time.sleep(3.5)
            elif abs(step_tmp) > 1800:
                time.sleep(2.2)
            elif abs(step_tmp) > 750:
                time.sleep(1.75)
            elif abs(step_tmp) > 350:
                time.sleep(0.9)
            else:
                time.sleep(0.2)
                
            current_wavelength = sm.wavemeter.get_wavelength()
            if (abs(target_wavelength - current_wavelength) < 0.5 and 
                abs(target_wavelength - current_wavelength) > 0.1):
                break
            step_tmp += steps / step_number

    @staticmethod
    def recalibrate(sm, real_wavelength_text, cal_wavelength_text):
        if not sm.wavemeter.is_connected or not sm.motor.is_connected:
            raise Exception("Оборудование не подключено!")
            
        if real_wavelength_text in ['under', 'over'] or cal_wavelength_text == 'no calibration here':
            raise Exception("Некорректные данные для калибровки")
            
        real_wavelength = int(float(real_wavelength_text) * 1000)
        cal_wavelength = int(float(cal_wavelength_text) * 1000)
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
        
        return "Перекалибровка завершена"

    @staticmethod
    def goto_wavelength_by_motor(sm, wavelength):
        if not sm.motor.is_connected:
            raise Exception("Motor 2 not connected")
            
        step = 35
        current_wavelength = EquipmentThreads._get_average_wavelength(sm)
        sm.motor.go_relative(1, step)
        time.sleep(2)
        
        for_test_current_wavelength = EquipmentThreads._get_average_wavelength(sm)
        new_wavelength = wavelength
        diff_wavelength = abs(new_wavelength - current_wavelength)
        right_way = True
        
        if abs(new_wavelength - for_test_current_wavelength) > diff_wavelength:
            right_way = False
            
        up = new_wavelength > current_wavelength
        down = new_wavelength < current_wavelength
        
        while abs(diff_wavelength) > 0.01:
            current_wavelength = EquipmentThreads._get_average_wavelength(sm)
            diff_wavelength = abs(new_wavelength - current_wavelength)
            
            if diff_wavelength > 100:
                step = 500
            elif diff_wavelength < 20:
                step = 300
            elif diff_wavelength <= 5:
                step = 30
            elif diff_wavelength <= 0.2:
                step = 5
                
            if not right_way:
                step = -step
                
            sm.motor.go_relative(1, step)
            time.sleep(0.5)
            
            if ((up and (new_wavelength < current_wavelength)) or 
                (down and (new_wavelength > current_wavelength))):
                break
                
        current_energy = sm.energymeter.get_average_energy(10)
        energy_1 = 0
        energy_2 = 0
        
        while True:
            current_energy = sm.energymeter.get_average_energy(20)
            if current_energy > 0 and current_energy < 0.0001:
                z_step = 30
            elif current_energy > 0.0001 and current_energy < 0.0003:
                z_step = 10
            elif current_energy > 0.0003:
                z_step = 2
                if energy_1 < energy_2 and current_energy < energy_1 and energy_2 > 0:
                    break
                energy_2 = energy_1
                energy_1 = current_energy
                
            if not right_way:
                z_step = -z_step
                
            sm.motor.go_relative(2, z_step)
            
        return "Перемещение motor 2 завершено"

    @staticmethod
    def _get_average_wavelength(sm):
        average_energy = 0
        for i in range(4):
            average_energy += sm.wavemeter.get_wavelength()
            time.sleep(0.2)
        return average_energy / 4