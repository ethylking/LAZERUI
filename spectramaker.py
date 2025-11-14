from devices_control import *
import time
from printer_controller import PrinterController

class Spectramaker:
    def __init__(self):
        self.printer: PrinterController = PrinterController("COM3", 115200, 1)
        self.wavemeter: Wavemeter = Wavemeter()
        self.energymeter: Energiser = Energiser()
        self.oscilloscope: Oscilloscope = Oscilloscope()
        self.motor: Motor = Motor()
        self.max_wavelength = 450
        self.step = 500
        self.frequency = 5

    def set_frequency(self, frequency):
        self.frequency = frequency

    def save_parameters(self, file_wavelength: str, file_energy: str) -> None:
        self.energymeter.refresh()
        time.sleep(1)
        print('saving energy ', self.energymeter.get_average_energy(10))
        wavelength = str(self.wavemeter.get_wavelength()).replace('.', ',')[0:7]
        file_wavelength.write(f'{self.motor.get_position(1)}/{wavelength}/{self.motor.get_position(2)}/1\n')
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
                

            self.go_wavelength(target_wavelength, True)
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
    
    def energy_peak_check(self, energy_limit: float):
        z_step = 10
        current_energy = self.energymeter.get_average_energy(20) * 1000
        self.printer.go_relative(1, z_step)
        next_energy = self.energymeter.get_average_energy(20) * 1000
        self.printer.go_relative(1, -2*z_step)
        prev_energy = self.energymeter.get_average_energy(20) * 1000
        self.printer.go_relative(1, z_step)
        energy_1 = 0
        energy_2 = 0
        current_steps_z = 0
        rude_energy_limit = energy_limit * 0.2 
        precize_energy_limit = energy_limit * 0.5 
        while True:
            current_steps_z += z_step
            time.sleep(1)
            currrent_energy = self.energymeter.get_average_energy(20)
            if currrent_energy > 0 and currrent_energy < rude_energy_limit:
                z_step = 500
            if currrent_energy > rude_energy_limit and currrent_energy < precize_energy_limit:
                z_step = 10
            if currrent_energy > precize_energy_limit:
                z_step = 4
                print(f"Поиск пика энергии, Z-мотор: {current_steps_z} шагов, энергия: {currrent_energy}")
                if energy_1 < energy_2 and currrent_energy < energy_1 and energy_2 > 0:
                    #self.printer.go_relative(1, -10 * z_step)
                    current_steps_z -= 10 * z_step
                    break
                energy_2 = energy_1
                energy_1 = currrent_energy 
            if (prev_energy >  current_energy):
                z_step = -z_step
            elif(next_energy > current_energy):
                z_step = z_step
            else:
                break
            print("seeking next peak, ", z_step)
            self.printer.go_relative(1, z_step)  
    def go_wavelength(self, wavelength_goal: float, using_BBO_motor: bool) -> None:
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

            if z_steps != 0 and using_BBO_motor == True:
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
                     wavelength_step: float = 0., folder: str = "data", inspect_energy: int = 0, first_harmonic_energy: int = 0, energy_limit: float = 0.00003) -> None:
        if not self.printer.is_connected:
            print("Принтер не подключен!")
            return
        if not self.oscilloscope.is_connected:
            print("Осциллограф не подключен!")
            return

        dropboxFolder = f"C:\\Users\\219-PC\\Dropbox\\МФД\\Vladislav\\Изопрен\\Масс-спектры\\бутадиен\\{folder}"
        if (os.path.isdir(dropboxFolder)):
            pass
        else:
            os.mkdir(dropboxFolder)

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

        file_cal = open(f'{dropboxFolder}\\calibration_file.txt', 'w')
        
        res_file = open(f'{dropboxFolder}\\{wavelength_min}-{wavelength_max}_energy_profile.txt', 'w')
        target_wavelength = wavelength_min
        while (target_wavelength >= wavelength_min and target_wavelength <= (wavelength_max + 0.001)):
            self.energymeter.set_wavelength(target_wavelength/2)
            self.go_wavelength(target_wavelength, True)
            self.energy_peak_check(energy_limit)
            print(f"Перемещение на длину волны {target_wavelength} успешно")
            current_wavelenght = self.wavemeter.get_wavelength()
            time.sleep(1)
            self.oscilloscope.run_acquision()
            time.sleep(count / self.frequency + 2)
            wavelength_str = str(current_wavelenght)[:7].replace('.', ',')
            self.oscilloscope.save_file(f'{dropboxFolder}\\{wavelength_str}.txt')
            energy = self.energymeter.get_average_energy(20) * 1000
            if(inspect_energy != 0):
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
        time.sleep(count / self.frequency + 1.5)
        self.oscilloscope.save_file(f'spectrum_5\\only_dye_312.15_end_1.35mJ.txt')

    def get_energy_profile(self, wavelength_min: float, wavelength_max: float, average_count: int = 100,
                     wavelength_step: float = 0., folder: str = "data", first_harmonic_energy: int = 0, energy_limit: float = 0.00003) -> None:
        if not self.printer.is_connected:
            print("Принтер не подключен!")
            return
        if not self.energymeter.is_connected:
            print("Энергомер не подключен!")
            return

        if not os.path.isdir(folder):
            os.mkdir(folder)

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
            self.energymeter.set_wavelength(target_wavelength/2)
            if (first_harmonic_energy == 0):
                self.go_wavelength(target_wavelength, True)
                self.energy_peak_check(energy_limit)
            else:
                self.go_wavelength(target_wavelength, False)
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

    def get_average_wavelength(self):
        average_energy = 0
        for i in range(4):
            average_energy += self.wavemeter.get_wavelength()
            time.sleep(0.2)
        return average_energy / 4

    def go_to_wavelength_by_motor(self, wavelength: float, energy_limit: float):
        if self.motor.is_connected == False:
            pass
        else:
            print("here")
            step = 35
            current_wavelength = self.get_average_wavelength()
            self.motor.go_relative(1, step)
            time.sleep(2)
            for_test_current_wavelength = self.get_average_wavelength()
            new_wavelength = wavelength
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
                current_wavelength = self.get_average_wavelength()
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
                self.motor.go_relative(1, step)
                #self.motor.wait_for_free(1)
                #self.sm.motor.wait_for_free(2)
                if ((up and (new_wavelength < current_wavelength)) or (down and (new_wavelength > current_wavelength))):
                    break
            current_energy = self.energymeter.get_average_energy(10)
            energy_1 = 0
            energy_2 = 0
            while True:
                currrent_energy = self.energymeter.get_average_energy(20)
                if currrent_energy > 0 and currrent_energy < energy_limit * 0.2:
                    z_step = 150
                    print("Ищем, ", z_step)
                if currrent_energy > energy_limit * 0.2 and currrent_energy < energy_limit * 0.5:
                    z_step = 10
                    print("Ищем, ", z_step)
                if currrent_energy > energy_limit * 0.5:
                    z_step = 2
                    print(f"Поиск пика энергии, энергия: {currrent_energy}")
                    if energy_1 < energy_2 and currrent_energy < energy_1 and energy_2 > 0:
                    #self.printer.go_relative(1, -10 * z_step)
                        break
                    energy_2 = energy_1
                    energy_1 = currrent_energy 
                if (right_way == False):
                    z_step = -z_step
                self.motor.go_relative(2, z_step) 
            right_way = True

    def get_spectrum_by_motor(self, wavelength_min: float, wavelength_max: float, average_count: int = 100,
                      wavelength_step: float = 0., folder: str = "data", inspect_energy: int = 0, energy_limit: float = 0.0003) -> None:
        dropboxFolder = f"C:\\Users\\219-PC\\Dropbox\\МФД\\Vladislav\\Изопрен\\Масс-спектры\\бутадиен\\{folder}"
        if (os.path.isdir(dropboxFolder)):
            pass
        else:
            os.mkdir(dropboxFolder)
        self.oscilloscope.set_acquire_average_mode()
        self.oscilloscope.set_acquire_count(average_count)
        #self.motor.go_home(1)
        #self.motor.go_home(2)
        count = self.oscilloscope.get_acquire_count()
        wavelength_cur = wavelength_min
        self.go_to_wavelength_by_motor(wavelength_cur, energy_limit)
        time.sleep(5)
        res_file = open(f'{dropboxFolder}\\{wavelength_min}-{wavelength_max}_energy_profile.txt', 'w')
        while (wavelength_max + 0.01) > wavelength_cur:
            wavelength_cur += wavelength_step
            time.sleep(1)
            wavelength = self.get_average_wavelength()
            self.oscilloscope.run_acquision()
            time.sleep(count / self.frequency + 1.5) # частота лазера, обычно 10 Гц
            self.oscilloscope.save_file(f'{dropboxFolder}\\{str(wavelength)[:7]}.txt')
            wavelength_str = str(wavelength)[:7].replace('.', ',')
            energy = self.energymeter.get_average_energy(20) * 1000
            if(inspect_energy != 0):
                res_file.write(f'{wavelength_str}\t{energy}\n')
            print('got on ', wavelength)
            self.go_to_wavelength_by_motor(wavelength_cur, energy_limit)
            time.sleep(2)
        res_file.close()

    def get_energy_profile_by_motor(self, n) -> None:
        file_1 = open(f'spectrum_5\\energy_profile.txt', 'w')
        file = open('spectrum_5\\calibration_file.txt', 'r')
        self.motor.go_home(1)
        self.motor.go_home(2)
        for line in file:
            wave = line.strip().split('\t')[0].replace(',', '.')
            motor_1 = int(line.strip().split('\t')[1])
            motor_2 = int(line.strip().split('\t')[2])
            # if float(wave) < 588.63:
            #     continue
            # if float(wave) > 599.251:
            #     continue
            self.motor.go_absolute(1, motor_1)
            self.motor.go_absolute(2, motor_2)
            self.energymeter.refresh()
            time.sleep(1)
            wavelength = self.wavemeter.get_wavelength()
            self.energymeter.set_wavelength(wavelength / 2)
            energy = self.energymeter.get_average_energy(30)
            file_1.write(f'{wavelength}\t{energy * 1000}\n')

        file.close()
        file_1.close()

    def calibrate(self) -> None:
        self.max_wavwlenght = 75
        file_wavelength = open('calibration\\file_wavelength.txt', 'w')
        file_energy = open('calibration\\file_energy.txt', 'w')
        #self.motor.go_home_both()
        #self.motor.go_relative(1,69280)
        # self.motor.go_relative(2, 87960)
        time.sleep(5)
        wavelength = self.wavemeter.get_wavelength()

        self.energymeter.set_wavelength(wavelength / 2)
        self.energymeter.refresh()
        # self.go_until(1, target_wavelength=self.min_wavelength, step=self.step)
        sh_energy = self.energymeter.get_average_energy(10)
        while self.wavemeter.get_wavelength() < self.max_wavelength:
            self.energymeter.refresh()
            wavelength = self.wavemeter.get_wavelength()
            if(wavelength > 630.150):
                while input('Поменяйте положение зеркала и напечатайте \'next\': ') != 'next':
                    continue
            self.energymeter.set_wavelength(wavelength / 2)
            time.sleep(2)
            sh_energy = self.energymeter.get_average_energy(10)
            while sh_energy < 10**-4:
                self.motor.go_relative(2, 30)
                sh_energy = self.energymeter.get_average_energy(10)
                print(sh_energy)
            energy_down = 0
            while True:
                old_energy = sh_energy
                self.motor.go_relative(2, 10)
                print(self.motor.get_position(2))
                sh_energy = self.energymeter.get_average_energy(30)
                print(sh_energy)
                if sh_energy < old_energy:
                    if energy_down == 1:
                        self.motor.go_relative(2, -2000)
                        self.motor.go_relative(2, 1980)
                        self.save_parameters(file_wavelength, file_energy)
                        break # end of iteration
                    else:
                        energy_down = 1
                else:
                    energy_down = 0
            self.motor.go_relative(1, self.step)
            print('нексиль')
        file_wavelength.close()
        file_energy.close() 


