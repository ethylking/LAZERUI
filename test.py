from spectramaker import Spectramaker
from devices_control import Energiser
import time

def generate_calibration_file(min_wavelength=679.0, max_wavelength=711.0, x_step=1000, z_step=100):
    sm = Spectramaker()
    
    print("Подключение к устройствам...")
    if not sm.printer.connect():
        print("Принтер не подключен!")
        return
    if not sm.wavemeter.is_connected:
        try:
            sm.wavemeter.connect()
        except Exception as e:
            print(f"Измеритель длины волны не подключен: {e}")
            return
    if not sm.energymeter.is_connected:
        try:
            sm.energymeter.connect(5)
        except Exception as e:
            print(f"Энергомер не подключен: {e}")
            return

    sm.printer.go_home_both()
    time.sleep(3)

    with open('full_calibration.txt', 'w') as cal_file:
        current_steps_x = 0
        current_steps_z = 0
        while True:
            sm.printer.go_relative(2, x_step)
            
            current_steps_x += x_step
            time.sleep(2)

            wavelength = sm.wavemeter.get_wavelength()
            if not isinstance(wavelength, float):
                print(f"Некорректное значение длины волны: {wavelength}")
                time.sleep(sm.wavemeter.get_exposure() * 4)
                continue
            if wavelength < min_wavelength or wavelength > max_wavelength:
                break

            sm.energymeter.set_wavelength(wavelength / 2)
            sm.energymeter.refresh()
            time.sleep(2)

            
            energy_1 = 0
            energy_2 = 0
            while True:
                sm.printer.go_relative(1, z_step)
                current_steps_z += z_step
                time.sleep(1)
                current_energy = sm.energymeter.get_average_energy(20)
                if current_energy > 0 and current_energy < 0.0001:
                    z_step = 100
                if current_energy > 0.0001 and current_energy < 0.0005:
                    z_step = 10
                if current_energy > 0.0005:
                    z_step = 4
                    print(f"Поиск пика энергии, Z-мотор: {current_steps_z} шагов, энергия: {current_energy}")
                    if energy_1 < energy_2 and current_energy < energy_1 and energy_2 > 0:
                        sm.printer.go_relative(1, -10 * z_step)
                        current_steps_z -= 10 * z_step
                        wavelength_str = str(wavelength)[:7].replace('.', ',')
                        cal_file.write(f"{wavelength_str}\t{current_steps_z}\t{current_steps_x}\t{energy_2}\n")
                        print(f"Калибровочная точка сохранена: длина волны={wavelength_str}, Z-шаги={current_steps_z}, X-шаги={current_steps_x}")
                        break
                    energy_2 = energy_1
                    energy_1 = current_energy    
                

    sm.printer.disconnect()
    print("Калибровка завершена, данные сохранены в full_calibration.txt")

if __name__ == "__main__":
    
    generate_calibration_file()
    # sm = Spectramaker()
    # a = 0
    # sm.printer.connect()
    # sm.energymeter.connect(5)
    # while a < 0.0005:
    #     sm.printer.go_relative(1, -1500)

    #     #a = sm.energymeter.get_average_energy(10)
    #     time.sleep(4)

