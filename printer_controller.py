from libraries import *
import serial
import re
from devices_control import Wavemeter

class PrinterController:
    
    def __init__(self, port, baudrate, timeout):
        self.serial = None
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.steps_to_mm = 400
        self.mm_to_steps = 1 / self.steps_to_mm
        self.is_connected = False
        
        
       

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

    def set_position(self, axis, position, speed=150, relative=False):
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

    def go_relative(self, id: int, steps: int) -> None:
        
        step_number = 1
        if(abs(steps) <= 4000 and id !=1):
            step_number = 5
        elif (abs(steps) > 4000 and id !=1 and abs(steps) <= 12000): 
            step_number = 20
        elif(abs(steps) > 12000 and id !=1):
            step_number = 50
        if not self.is_connected:
            print("Устройство не подключено!")
            return
        step_tmp = steps/step_number
        
        while (abs(step_tmp) <= abs(steps)):
            mm_distance = -(steps/step_number) * self.mm_to_steps
            axis = "Z" if id == 1 else "X"
            self.set_position(axis, mm_distance, speed=50, relative=True)
            step_tmp += steps/step_number
        
            

    def go_absolute(self, id: int, steps: int) -> None:
        if not self.is_connected:
            print("Устройство не подключено!")
            return
        mm_position = steps * self.mm_to_steps
        axis = "Z" if id == 1 else "X"
        self.set_position(axis, mm_position, speed=50, relative=False)