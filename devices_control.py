from libraries import *
import serial
import re

class PrinterController:
    
    def __init__(self, port, baudrate, timeout):
        self.serial = None
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.steps_to_mm = 400
        self.mm_to_steps = 1 / self.steps_to_mm
        self.is_connected = False
        self.wm: HighFinesse
       

    def connect(self):
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print("Подключение успешно!")
            time.sleep(2)
            self._clear_buffer()
            #self.send_command("G90")
            #self.send_command("M17")
            self.is_connected = True
            return True
        except serial.SerialException as e:
            print(f"Ошибка подключения: {e}")
            return False

    def get_wavelength(self, force: bool = False):
        wl = self.wm.get_wavelength(error_on_invalid=False)
        while True:
            if type(wl) == float:
                return wl * 10**9
            else:
                if force:
                    return wl
                else:
                    time.sleep(self.get_exposure() * 4)
                wl = self.wm.get_wavelength(error_on_invalid=False)

    def get_exposure(self) -> float:
        return self.wm.get_exposure()

    def set_exposure(self, exposure_time: float) -> float:
        self.wm.set_exposure(exposure_time)
        return self.get_exposure()

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.send_command("M18")
            self.serial.close()
            print("Соединение закрыто.")
            self.is_connected = False

    def send_command(self, command):
        if not self.serial or not self.serial.is_open:
            print("Не подключено к устройству!")
            return None
        try:
            self.serial.write(f"{command}\n".encode())
            response = []
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                line = self.serial.readline().decode().strip()
                if line:
                    response.append(line)
                    if "ok" in line.lower():
                        break
            return response
        except serial.SerialException as e:
            print(f"Ошибка отправки команды: {e}")
            return None

    def _clear_buffer(self):
        if self.serial and self.serial.is_open:
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()

    def set_position(self, axis, position, speed=50, relative=False):
        if relative:
            self.send_command("G91")
        else:
            self.send_command("G90")
        command = f"G1 {axis}{position:.2f} F{speed}"
        print(f"Устанавливаем позицию: {command}")
        response = self.send_command(command)
        if response and any("ok" in line.lower() for line in response):
            print("Позиция установлена.")
            return True
        else:
            print(f"Ошибка установки позиции: {response}")
            return False

    def reset(self, axis=None):
        print("Устанавливаем текущую позицию как 0...")
        command = "G92 Z0" if axis == "Z" else "G92 X0 Y0 Z0"
        response = self.send_command(command)
        if response and any("ok" in line.lower() for line in response):
            print("Позиция сброшена.")
            return True
        else:
            print(f"Ошибка сброса: {response}")
            return False

    def stop(self):
        print("Останавливаем движение...")
        response = self.send_command("M112")
        if response and any("ok" in line.lower() for line in response):
            print("Движение остановлено.")
            return True
        else:
            print(f"Ошибка остановки: {response}")
            return False

    def get_position(self):
        print("Запрашиваем текущую позицию...")
        response = self.send_command("M114")
        if response is None:
            print("Ошибка: нет ответа от устройства")
            return None
        print(f"Получен ответ: {response}")
        for line in response:
            print(f"Обрабатываем строку: {line}")
            match = re.match(r"X:([\d.-]+)\s+Y:([\d.-]+)\s+Z:([\d.-]+)", line)
            if match:
                position = {
                    "X": float(match.group(1)),
                    "Y": float(match.group(2)),
                    "Z": float(match.group(3))
                }
                print(f"Текущая позиция: {position}")
                return position
        print(f"Не удалось разобрать позицию: {response}")
        return None

    def go_home(self, id: int) -> None:
        if not self.is_connected:
            print("Устройство не подключено!")
            return
        axis = "Z" if id == 1 else "X"
        self.reset(axis=axis)
        print(f"Мотор {id} успешно установлен в начальное положение")

    def go_home_both(self) -> None:
        if not self.is_connected:
            print("Устройство не подключено!")
            return
        self.reset()
        print("Оба мотора успешно установлены в начальное положение")

    def get_steps_position(self, id: int) -> int:
        if not self.is_connected:
            print("Устройство не подключено!")
            return 0
        position = self.get_position()
        if position is None:
            return 0
        axis = "Z" if id == 1 else "X"
        mm_position = position[axis]
        steps_position = int(mm_position / self.mm_to_steps)
        return steps_position

    def get_state(self, id: int) -> int:
        return 0

    def wait_for_free(self, id: int) -> None:
        time.sleep(0.2)

    def go_relative(self, id: int, steps: int, wave_use: int, wavelenght: float) -> None:
        
        step_number = 1
        if(steps <= 4000 and id !=1):
            step_number = 5
        elif (steps > 4000 and id !=1): 
            step_number = 20
        elif(steps > 12000 and id !=1):
            step_number = 50
        if not self.is_connected:
            print("Устройство не подключено!")
            return
        step_tmp = steps/step_number
        
        while (abs(step_tmp) <= abs(steps)):
            mm_distance = -(steps/step_number) * self.mm_to_steps
            axis = "Z" if id == 1 else "X"
            self.set_position(axis, mm_distance, speed=50, relative=True)
            time.sleep(1)
            current_wavelenght = self.get_wavelength()
            
            if (wave_use == 1 and abs(current_wavelenght - wavelenght) < 0.1):
                break
            step_tmp += steps/step_number
        
            

    def go_absolute(self, id: int, steps: int) -> None:
        if not self.is_connected:
            print("Устройство не подключено!")
            return
        mm_position = steps * self.mm_to_steps
        axis = "Z" if id == 1 else "X"
        self.set_position(axis, mm_position, speed=50, relative=False)

class Energiser:
    def __init__(self):
        self.em: Gentec_Maestro
        self.is_connected: bool = False

    def connect(self, com_adress: int) -> None:
        self.em = Gentec_Maestro(name="Gentec", address=f'ASRL{com_adress}::INSTR')
        print(f"connected COM{com_adress}")

    def get_wavelength(self) -> float:
        return self.em.wavelength.get()

    def set_wavelength(self, wavelength: any) -> None:
        self.em.wavelength.set(int(wavelength))

    def get_average_energy(self, n: int) -> float:
        sum = 10**11
        while sum > 10**10:
            sum = 0
            for i in range(n):
                sum += self.em.power.get()
                time.sleep(0.1)
        return sum / n

    def get_power_unit(self) -> str:
        return self.em.power.unit

    def clear_zero_offset(self) -> None:
        self.em.clear_zero_offset()

    def set_zero_offset(self) -> None:
        self.em.set_zero_offset()

    def refresh(self) -> None:
        self.em.set_zero_offset()
        self.em.clear_zero_offset()

class Wavemeter:
    integral_constant = 69280 / (419.963 - 410)

    def __init__(self):
        self.wm: HighFinesse
        self.is_connected: bool = False

    def connect(self) -> None:
        app_folder = r"C:\Program Files (x86)\Angstrom\Wavelength Meter WS6 3153"
        dll_path = os.path.join(app_folder, "Projects", "64")
        app_path = os.path.join(app_folder, "wlm_ws6.exe")
        self.wm = HighFinesse.WLM(1234, dll_path=dll_path, app_path=app_path)

    def get_wavelength(self, force: bool = False):
        wl = self.wm.get_wavelength(error_on_invalid=False)
        while True:
            if type(wl) == float:
                return wl * 10**9
            else:
                if force:
                    return wl
                else:
                    time.sleep(self.get_exposure() * 4)
                wl = self.wm.get_wavelength(error_on_invalid=False)

    def get_exposure(self) -> float:
        return self.wm.get_exposure()

    def set_exposure(self, exposure_time: float) -> float:
        self.wm.set_exposure(exposure_time)
        return self.get_exposure()

class Oscilloscope:
    def __init__(self):
        self.osc: Oscilloscope
        self.is_connected = False

    def connect(self) -> None:
        rm = pyvisa.ResourceManager()
        my_instrument = rm.open_resource('USB0::0x0957::0x17A4::MY52103114::INSTR')
        my_instrument.read_termination = '\n'
        my_instrument.write_termination = '\n'
        print(my_instrument.query('*IDN?'))
        self.osc = my_instrument

    def get_acquire_count(self) -> int:
        return int(self.osc.query(':ACQuire:COUNt?'))

    def set_acquire_count(self, count: int) -> None:
        self.osc.write(f':ACQuire:COUNt {count}')

    def set_acquire_normal_mode(self) -> None:
        self.osc.write(':ACQuire:TYPE NORMal')

    def set_acquire_average_mode(self) -> None:
        self.osc.write(':ACQuire:TYPE AVERage')

    def get_acquire_mode(self) -> str:
        return self.osc.query(':ACQuire:TYPE?')

    def set_channel_status(self, id: int, status: int) -> None:
        self.osc.write(f':CHANnel{id}:DISPlay {status}')

    def get_channel_status(self, id: int) -> int:
        return int(self.osc.query(f':CHANnel{id}:DISPlay?'))

    def get_channel_scale(self, id: int) -> int:
        return int(float(self.osc.query(f':CHANnel{id}:SCALe?')) * 1000)

    def set_channel_scale(self, id: int, scale: int) -> None:
        self.osc.write(f':CHANnel{id}:SCALe {scale}')

    def refresh(self) -> None:
        self.osc.write(':DISPlay:CLEar')

    def set_timebase(self, timebase: float) -> None:
        self.osc.write(f':TIMebase:DELay {timebase}')

    def get_timebase(self) -> str:
        return self.osc.query(':TIMebase:DELay?')

    def set_timescale(self, timescale: float) -> None:
        self.osc.write(f':TIMebase:SCALe {timescale}')

    def get_timescale(self) -> float:
        return float(self.osc.query(':TIMebase:SCALe?'))

    def run_acquision(self) -> None:
        self.osc.write(':WAVeform:SOURce CHANnel1')
        self.osc.write(':WAVeform:FORMat ASCII')
        self.osc.write(':WAVeform:POINts 2000')
        self.osc.write(':DIGitize CHANnel1')

    def save_usb(self, filename: str) -> None:
        self.osc.write(':SAVE:WAVeform:FOMat CSV')
        self.osc.write(f":SAVE:WAVeform:STARt \'{filename}_{datetime.today().strftime(r'%Y_%m_%d_%H_%M_%S')}\'")

    def get_x_axis(self) -> list:
        increment = float(self.osc.query(':WAVeform:XINCrement?'))
        x_start = float(self.osc.query(':WAVeform:XORigin?'))
        points_number = int(self.osc.query(':WAVeform:POINts?'))
        x_axis = [x_start + increment * i for i in range(points_number)]
        return x_axis

    def get_y_axis(self) -> list:
        y_axis = self.osc.query(':WAVeform:DATA?')[11:].strip().split(',')
        y_axis = [float(i) for i in y_axis]
        return y_axis

    def save_file(self, filename: str) -> None:
        file = open(filename, 'w')
        x_axis = self.get_x_axis()
        y_axis = self.get_y_axis()
        for i in range(len(x_axis)):
            file.write(f'{x_axis[i]}\t{y_axis[i]}\n')
        file.close()
