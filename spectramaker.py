from devices_control import *
import time
from printer_controller import PrinterController

class Spectramaker:
    def __init__(self):
        self.printer: PrinterController = PrinterController("COM3", 115200, 1)
        self.wavemeter: Wavemeter = Wavemeter()
        self.energymeter: Energiser = Energiser()
        self.oscilloscope: Oscilloscope = Oscilloscope()

    def save_parameters(self, file_wavelength: str, file_energy: str) -> None:
        self.energymeter.refresh()
        time.sleep(1)
        print(f'Сохранение энергии: {self.energymeter.get_average_energy(10)}')
        wavelength = str(self.wavemeter.get_wavelength()).replace('.', ',')[0:7]
        file_wavelength.write(f'{self.printer.get_steps_position(1)}/{wavelength}/{self.printer.get_steps_position(2)}/1\n')
        file_energy.write(f'{wavelength}\t{self.energymeter.get_average_energy(20)}\n')

    def go_until(self, id: int, target_wavelength: float, step: int = 10) -> None:
        current_wavelength = 400
        if current_wavelength > target_wavelength:
            direction = -1
        else:
            direction = 1
        difference = direction * (target_wavelength - current_wavelength)
        while difference > 0:
            if difference > 2:
                self.printer.go_relative(id, direction*700)
            elif difference > 0.2:
                self.printer.go_relative(id, direction*100)
            else:
                self.printer.go_relative(id, direction*15)
            self.printer.wait_for_free(1)
            time.sleep(0.2)
            self.printer.get_steps_position(2)
            print(f'Текущая длина волны: {self.wavemeter.get_wavelength()}')
            current_wavelength = self.wavemeter.get_wavelength()
            difference = direction * (target_wavelength - current_wavelength)

    def inspect_energy(self, wavelength_min: float, wavelength_max: float, average_count: int = 100,
                     wavelength_step: float = 0., folder: str = "data") -> None:
        if not self.printer.is_connected:
            print("Принтер не подключен!")
            return
        if not self.wavemeter.is_connected:
            print("Измеритель длины волны не подключен!")
            return
        if not self.energymeter.is_connected:
            print("Энергомер не подключен!")
            return

        calibration_data = []
        with open(f'full_calibration.txt', 'r') as file:
            for line in file:
                parts = line.strip().split('\t')
                wavelength = float(parts[0].replace(',', '.'))
                motor_1_steps = int(parts[1])
                motor_2_steps = int(parts[2])
                calibration_data.append((wavelength, motor_1_steps, motor_2_steps))
        res_file = open(f'{wavelength_min}-{wavelength_max} energy_profile.txt', 'w')
        file_cal = open(f'{folder}\\calibration_file.txt', 'w')
        target_wavelength = wavelength_min
        while (target_wavelength >= wavelength_min and target_wavelength <= (wavelength_max + 0.001)):
                

            self.go_wavelength(target_wavelength)
            print(f"Перемещение на длину волны {target_wavelength} успешно")
            current_wavelenght = self.wavemeter.get_wavelength()
            time.sleep(1)
            wavelength_str = str(current_wavelenght)[:7].replace('.', ',')
            time.sleep(1)
            energy = self.energymeter.get_average_energy(20) * 1000
            res_file.write(f'{wavelength_str}\t{energy}\n')
            #file_cal.write(f'{wavelength_str}\t{target_steps_1}\t{target_steps_2}\n')
            print(f'Получена энергия на длине волны {target_wavelength}')
            target_wavelength += wavelength_step
        file_cal.close()
            
            #print(f'Длина волны = {target_wavelength}, энергия = {energy}')
            

        res_file.close()

    def go_wavelength(self, wavelength_goal: float) -> None:
        if not self.printer.is_connected:
            print("Принтер не подключен!")
            return

        current_wavelength = self.wavemeter.get_wavelength()
        if not isinstance(current_wavelength, float):
            print("Некорректное значение длины волны!")
            return

        calibration_data = []
        with open("full_calibration.txt", 'r') as file:
            for line in file:
                parts = line.strip().split('\t')
                wavelength = float(parts[0].replace(',', '.'))
                motor_1_steps = int(parts[1])
                motor_2_steps = int(parts[2])
                calibration_data.append((wavelength, motor_1_steps, motor_2_steps))
        x_steps = 0
        z_steps = 0
        current_steps_1 = 0
        current_steps_2 = 0
        target_steps_1 = 0
        target_steps_2 = 0
        found_current = False
        found_target = False
        while (abs(wavelength_goal - current_wavelength) > 0.005):
            for wavelength_val, steps_1, steps_2 in calibration_data:
                if abs(wavelength_val - current_wavelength) < 0.001:
                    current_steps_1 = steps_1
                    current_steps_2 = steps_2
                    found_current = True
                if abs(wavelength_val - wavelength_goal) < 0.001:
                    target_steps_1 = steps_1
                    target_steps_2 = steps_2
                    found_target = True

            if not found_current or not found_target:
                print("Текущая или целевая длина волны не найдена в калибровочном файле!")
                return

            z_steps = target_steps_1 - current_steps_1
            x_steps = target_steps_2 - current_steps_2

            if z_steps != 0:
                self.printer.go_relative(1, z_steps)
            if x_steps != 0:
                self.go_relative_with_check(2, x_steps, wavelength_goal)
            x_steps = 0
            z_steps = 0
            if(z_steps > 400 or x_steps > 600):
                time.sleep(5)
            else:
                time.sleep(2)
            while (True):
                current_wavelength = self.wavemeter.get_wavelength()
                time.sleep(0.5)
                wavelength_tmp = self.wavemeter.get_wavelength()
                if (type(current_wavelength) == float and type(wavelength_tmp) == float and abs(wavelength_tmp - current_wavelength) < 0.01):
                    break
        print(f"Перемещение на длину волны {wavelength_goal}: Z-мотор на {z_steps} шагов, X-мотор на {x_steps} шагов")

    def get_spectrum(self, wavelength_min: float, wavelength_max: float, average_count: int = 100,
                     wavelength_step: float = 0., folder: str = "data", inspect_energy: int = 0) -> None:
        if not self.printer.is_connected:
            print("Принтер не подключен!")
            return
        if not self.oscilloscope.is_connected:
            print("Осциллограф не подключен!")
            return

        if not os.path.isdir(folder):
            os.mkdir(folder)

        self.oscilloscope.set_acquire_average_mode()
        self.oscilloscope.set_acquire_count(average_count)
        self.printer.go_home(1)
        self.printer.go_home(2)
        count = self.oscilloscope.get_acquire_count()

        calibration_data = []
        with open(f'full_calibration.txt', 'r') as file:
            for line in file:
                parts = line.strip().split('\t')
                wavelength = float(parts[0].replace(',', '.'))
                motor_1_steps = int(parts[1])
                motor_2_steps = int(parts[2])
                calibration_data.append((wavelength, motor_1_steps, motor_2_steps))

        file_cal = open(f'{folder}\\calibration_file.txt', 'w')
        res_file = open(f'{folder}\\{wavelength_min}-{wavelength_max}_energy_profile.txt', 'w')
        target_wavelength = wavelength_min
        while (target_wavelength >= wavelength_min and target_wavelength <= (wavelength_max + 0.001)):
                

            self.go_wavelength(target_wavelength)
            print(f"Перемещение на длину волны {target_wavelength} успешно")
            current_wavelenght = self.wavemeter.get_wavelength()
            time.sleep(1)
            self.oscilloscope.run_acquision()
            time.sleep(count / 10. + 1.5)
            wavelength_str = str(current_wavelenght)[:7].replace('.', ',')
            self.oscilloscope.save_file(f'{folder}\\{wavelength_str}.txt')
            energy = self.energymeter.get_average_energy(20) * 1000
            res_file.write(f'{wavelength_str}\t{energy}\n')
            #file_cal.write(f'{wavelength_str}\t{target_steps_1}\t{target_steps_2}\n')
            print(f'Получен спектр на длине волны {target_wavelength}')
            target_wavelength += wavelength_step
        file_cal.close()
        res_file.close()

    def get_nopump_signal(self) -> None:
        self.oscilloscope.set_acquire_average_mode()
        self.oscilloscope.set_acquire_count(200)
        count = self.oscilloscope.get_acquire_count()
        self.oscilloscope.run_acquision()
        time.sleep(count / 10 + 1.5)
        self.oscilloscope.save_file(f'spectrum_5\\only_dye_312.15_end_1.35mJ.txt')

    def get_energy_profile(self, wavelength_min: float, wavelength_max: float, average_count: int = 100,
                     wavelength_step: float = 0., folder: str = "data") -> None:
        if not self.printer.is_connected:
            print("Принтер не подключен!")
            return
        if not self.wavemeter.is_connected:
            print("Измеритель длины волны не подключен!")
            return
        if not self.energymeter.is_connected:
            print("Энергомер не подключен!")
            return

        calibration_data = []
        with open(f'full_calibration.txt', 'r') as file:
            for line in file:
                parts = line.strip().split('\t')
                wavelength = float(parts[0].replace(',', '.'))
                motor_1_steps = int(parts[1])
                motor_2_steps = int(parts[2])
                calibration_data.append((wavelength, motor_1_steps, motor_2_steps))
        res_file = open(f'{folder}\\{wavelength_min}-{wavelength_max}_energy_profile.txt', 'w')
        file_cal = open(f'{folder}\\calibration_file.txt', 'w')
        target_wavelength = wavelength_min
        while (target_wavelength >= wavelength_min and target_wavelength <= (wavelength_max + 0.001)):
                

            self.go_wavelength(target_wavelength)
            print(f"Перемещение на длину волны {target_wavelength} успешно")
            current_wavelenght = self.wavemeter.get_wavelength()
            time.sleep(1)
            wavelength_str = str(current_wavelenght)[:7].replace('.', ',')
            time.sleep(1)
            energy = self.energymeter.get_average_energy(20) * 1000
            res_file.write(f'{wavelength_str}\t{energy}\n')
            #file_cal.write(f'{wavelength_str}\t{target_steps_1}\t{target_steps_2}\n')
            print(f'Получена энергия на длине волны {target_wavelength}')
            target_wavelength += wavelength_step
        file_cal.close()
            
            #print(f'Длина волны = {target_wavelength}, энергия = {energy}')
            

        res_file.close()

    
    def go_relative_with_check(self, id: int, steps: int, target_wavelenght: float):
            step_number = 1
            if(abs(steps) <= 4000 and id !=1):
                step_number = 5
            elif (abs(steps) > 4000 and id !=1 and abs(steps) <= 12000): 
                step_number = 20
            elif(abs(steps) > 12000 and id !=1):
                step_number = 50
            if not self.printer.is_connected:
                print("Устройство не подключено!")
                return
            step_tmp = steps/step_number
        
            while (abs(step_tmp) <= abs(steps)):
                mm_distance = -(steps/step_number) * self.printer.mm_to_steps
                axis = "Z" if id == 1 else "X"
                self.printer.set_position(axis, mm_distance, speed=50, relative=True)
                if (abs(step_tmp) > 5000):
                    time.sleep(2.5)
                elif(abs(step_tmp) > 750):
                    time.sleep(1.75)
                elif(abs(step_tmp) > 350):
                    time.sleep(0.9)
                else:
                    time.sleep(0.2)
                current_wavelenght = self.wavemeter.get_wavelength()
                
                if (abs(target_wavelenght - current_wavelenght) < 0.5 and abs(target_wavelenght - current_wavelenght) > 0.1):
                    break
                step_tmp += steps/step_number