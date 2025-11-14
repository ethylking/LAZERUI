import os
import numpy as np
from scipy import integrate

class DataProcessor:
    
    @staticmethod
    def calculate_integral_with_bounds(x, y, left_bound, right_bound, baseline_type):
        mask = (x >= left_bound) & (x <= right_bound)
        x_filtered = x[mask]
        y_filtered = y[mask]
        
        if not len(x_filtered):
            return 0

        baseline = DataProcessor._calculate_baseline(x_filtered, y_filtered, baseline_type)
        y_corrected = y_filtered - baseline
        return integrate.trapz(y_corrected, x_filtered)

    @staticmethod
    def _calculate_baseline(x, y, baseline_type):
        if baseline_type == "Линейная" and len(x) >= 2:
            try:
                coef = np.polyfit(x[[0, -1]], y[[0, -1]], 1)
                return np.polyval(coef, x)
            except Exception:
                return 0
        elif baseline_type == "Полином 2-й степени" and len(x) >= 3:
            try:
                coef = np.polyfit(x, y, 2)
                return np.polyval(coef, x)
            except Exception:
                return 0
        else:
            return 0

    @staticmethod
    def load_oscilloscope_data(file_path):
        try:
            try:
                data = np.loadtxt(file_path)
            except:
                try:
                    data = np.loadtxt(file_path, delimiter=',')
                except:
                    data = np.loadtxt(file_path, delimiter='\t')
            
            if data.ndim != 2 or data.shape[1] < 2:
                raise ValueError("Неверный формат файла")
            
            x_data = data[:, 0]  
            y_data = data[:, 1]

            if np.max(np.abs(x_data)) > 1000: 
                x_data = x_data / 1e6

            filename = os.path.basename(file_path)
            try:
                wavelength = float(os.path.splitext(filename)[0].replace(',', '.'))
            except ValueError:
                wavelength = 0.0

            return x_data, y_data, wavelength
            
        except Exception as e:
            raise ValueError(f"Ошибка загрузки файла: {str(e)}")

    @staticmethod
    def get_smart_integration_bounds(x_data, y_data):
        if len(x_data) == 0:
            return 0, 0
        
        peak_idx = np.argmax(np.abs(y_data))
        x_center = x_data[peak_idx]
        
        x_range = x_data[-1] - x_data[0]
        
        if x_range < 1e-6:  
            integration_width = 5e-7 
        elif x_range < 1e-5:  
            integration_width = 2e-6  
        elif x_range < 0.001:  
            integration_width = x_range * 0.5
        else:                  
            integration_width = x_range * 0.1
        
        left_bound = float(x_center - integration_width / 2)
        right_bound = float(x_center + integration_width / 2)

        left_bound = max(float(x_data[0]), left_bound)
        right_bound = min(float(x_data[-1]), right_bound)

        return left_bound, right_bound

    @staticmethod
    def get_auto_plot_bounds(x_data, y_data):
        if len(x_data) == 0:
            return 0, 0, 0, 0

        peak_idx = np.argmax(np.abs(y_data))
        x_center = x_data[peak_idx]
        
        x_range = x_data[-1] - x_data[0]
        if x_range == 0:
            view_range = 0.01  
            x_min = x_center - view_range / 2
            x_max = x_center + view_range / 2
        else:
            view_margin = x_range * 0.2
            x_min = max(x_data[0], x_center - view_margin)
            x_max = min(x_data[-1], x_center + view_margin)

        y_margin = (np.max(y_data) - np.min(y_data)) * 0.1
        y_min = np.min(y_data) - y_margin
        y_max = np.max(y_data) + y_margin
        
        return x_min, x_max, y_min, y_max

    @staticmethod
    def process_spectrum_files(folder_path, left_bound, right_bound, baseline_type):
        spectrum_files = []
        
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Папка не существует: {folder_path}")
            
        files = os.listdir(folder_path)
        
        for file in files:
            if file.endswith('.txt'):
                try:
                    filename_without_ext = os.path.splitext(file)[0]
                    filename_clean = filename_without_ext.replace(',', '.')
                    wavelength = float(filename_clean)
                    full_path = os.path.join(folder_path, file)
                    spectrum_files.append((wavelength, full_path))
                except ValueError:
                    continue
                except Exception:
                    continue
        
        if not spectrum_files:
            raise ValueError("Не найдено файлов с длинами волн в именах!")
        
        spectrum_files.sort(key=lambda x: x[0])
        
        wavelengths = []
        intensities = []
        
        for wavelength, file_path in spectrum_files:
            try:
                x_data, y_data, _ = DataProcessor.load_oscilloscope_data(file_path)
                
                mask = (x_data >= left_bound) & (x_data <= right_bound)
                x_filtered = x_data[mask]
                y_filtered = y_data[mask]
                
                if len(x_filtered) == 0:
                    continue
                
                intensity = DataProcessor.calculate_integral_with_bounds(
                    x_data, y_data, left_bound, right_bound, baseline_type
                )
                
                wavelengths.append(wavelength)
                intensities.append(intensity)
                
            except Exception:
                continue
        
        if not wavelengths:
            raise ValueError("Не удалось обработать ни один файл!")
        
        return wavelengths, intensities