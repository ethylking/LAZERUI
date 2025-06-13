from libraries import *
import serial
import re

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
