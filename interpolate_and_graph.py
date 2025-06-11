import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt

# Чтение данных с заменой запятых на точки
with open('full_calibration.txt', 'r') as f:
    content = f.read().replace(',', '.')
data = np.loadtxt(content.splitlines(), delimiter='\t')

# Разделение данных
wavelength = data[:, 0]  # Длина волны
motor1 = data[:, 1]      # Шаг мотора 1 (целое)
motor2 = data[:, 2]      # Шаг мотора 2 (целое)
energy = data[:, 3]      # Энергия (дробное)

# Интерполяция для всех столбцов
f_motor1 = interpolate.interp1d(wavelength, motor1, kind='cubic')
f_motor2 = interpolate.interp1d(wavelength, motor2, kind='cubic')
f_energy = interpolate.interp1d(wavelength, energy, kind='cubic')

# Новые точки с шагом 0.001
new_wavelength = np.arange(wavelength.min(), wavelength.max(), 0.001)
new_motor1 = np.round(f_motor1(new_wavelength)).astype(int)
new_motor2 = np.round(f_motor2(new_wavelength)).astype(int)
new_energy = f_energy(new_wavelength)

# Визуализация
plt.figure(figsize=(15, 10))

# 1. График энергии от длины волны
plt.subplot(2, 2, 1)
plt.plot(wavelength, energy, 'ro', label='Исходные данные')
plt.plot(new_wavelength, new_energy, 'b-', label='Интерполяция')
plt.xlabel('Длина волны')
plt.ylabel('Энергия')
plt.legend()
plt.grid(True)

# 2. График шагов моторов от длины волны
plt.subplot(2, 2, 2)
plt.plot(wavelength, motor1, 'go', label='Мотор 1 (исходные)')
plt.plot(new_wavelength, new_motor1, 'g-', label='Мотор 1 (интерполированный)')
plt.plot(wavelength, motor2, 'mo', label='Мотор 2 (исходные)')
plt.plot(new_wavelength, new_motor2, 'm-', label='Мотор 2 (интерполированный)')
plt.xlabel('Длина волны')
plt.ylabel('Шаги моторов')
plt.legend()
plt.grid(True)

# 3. График энергии от шага мотора 1
plt.subplot(2, 2, 3)
plt.plot(motor1, energy, 'ko', label='Исходные данные')
plt.plot(new_motor1, new_energy, 'c-', label='Интерполяция')
plt.xlabel('Шаг мотора 1')
plt.ylabel('Энергия')
plt.legend()
plt.grid(True)

# 4. График энергии от шага мотора 2
plt.subplot(2, 2, 4)
plt.plot(motor2, energy, 'yo', label='Исходные данные')
plt.plot(new_motor2, new_energy, 'r-', label='Интерполяция')
plt.xlabel('Шаг мотора 2')
plt.ylabel('Энергия')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

# Сохранение в файл (4 колонки)
interpolated_data = np.column_stack((new_wavelength, new_motor1, new_motor2, new_energy))
np.savetxt('interpolated_calibration_final.txt', interpolated_data, 
           fmt='%.3f\t%d\t%d\t%.10f',  # Формат: длина волны, шаги (целые), энергия (10 знаков)
           )