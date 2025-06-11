import numpy as np
from scipy.interpolate import interp1d
import pandas as pd

data = pd.read_csv('full_calibration.txt', sep='\t', header=None, names=['wavelength', 'motor1_steps', 'motor2_steps'])

wavelengths = data['wavelength'].values
motor1_steps = data['motor1_steps'].values
motor2_steps = data['motor2_steps'].values

interp_motor1 = interp1d(wavelengths, motor1_steps, kind='linear', fill_value='extrapolate')
interp_motor2 = interp1d(wavelengths, motor2_steps, kind='linear', fill_value='extrapolate')

new_wavelengths = np.arange(float(min(wavelengths))- 3.000, float(max(wavelengths)) + 3.000, 0.001)

new_motor1_steps = interp_motor1(new_wavelengths)
new_motor2_steps = interp_motor2(new_wavelengths)

new_motor1_steps = np.round(new_motor1_steps).astype(int)
new_motor2_steps = np.round(new_motor2_steps).astype(int)

result = pd.DataFrame({
    'wavelength': new_wavelengths,
    'motor1_steps': new_motor1_steps,
    'motor2_steps': new_motor2_steps
})

result.to_csv('interpolated_calibration.txt', sep='\t', header=False, index=False, float_format='%.3f')

print(result.head())