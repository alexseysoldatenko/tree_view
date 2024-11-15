import segyio
import gpr_file
import json
import struct
import cv2
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import  QVBoxLayout, QDialog, QLineEdit, QPushButton, QFileDialog, QLabel


class ReadWindow(QDialog):
    def __init__(self, parent=None):

        self.base_configs = ConfigWorker()
        self.markers = None

        super(ReadWindow, self).__init__(parent)
        self.setWindowTitle('Read file parametrs')
        self.layout = QVBoxLayout()

        self.permittivity_param_window = QLineEdit(self)
        self.permittivity_param_window.setText(str(self.base_configs.read_configs['Permittivity']))
        self.svd_param_window = QLineEdit(self)
        self.svd_param_window.setText(str(self.base_configs.read_configs['SVD components']))
        self.length_wood_param_window = QLineEdit(self)
        self.length_wood_param_window.setText(str(self.base_configs.read_configs['Length of wood']))
        self.dt_window = QLineEdit(self)
        self.dt_window.setText(str(self.base_configs.read_configs['Distance between trace']))

        self.layout.addWidget(QLabel("Permittivity:"))
        self.layout.addWidget(self.permittivity_param_window)
        self.layout.addWidget(QLabel("SVD components:"))
        self.layout.addWidget(self.svd_param_window)
        self.layout.addWidget(QLabel("Length of wood sm:"))
        self.layout.addWidget(self.length_wood_param_window)
        self.layout.addWidget(QLabel("dt ns:"))
        self.layout.addWidget(self.dt_window)
        
        choose_file_button = QPushButton('Choose File', self)
        self.layout.addWidget(choose_file_button)

        ok_button = QPushButton('OK', self)
        ok_button.clicked.connect(self.send_parameters)

        choose_file_button.clicked.connect(self.__choose_file)

        self.layout.addWidget(ok_button)
        self.setLayout(self.layout)

    def __read_segy_data(self, path):
        
        if self.__is_read_config:
            try:
                with segyio.open(path, ignore_geometry=True, endian='little') as segyfile:
                    seismogram = segyfile.trace.raw[:]
            except:
                with segyio.open(path, ignore_geometry=True, endian='big') as segyfile:
                    seismogram = segyfile.trace.raw[:]
            seism_markers = ReadWindow.get_markers_sgy(path)
            seismogram = seismogram.T
            seismogram, seism_markers = ReadWindow.interpolate_sgy(seismogram, seism_markers, 10, 0.1, seismogram.shape[0])
            red_line = int(np.mean(np.argmax(np.diff(seismogram, axis=0),axis = 0) - 5))
            return seismogram[:self.__calculate_crop_param()+red_line], seism_markers
        else:
            return None, None
    
    @staticmethod
    def interpolate_sgy(image, marker_id, dbm, dbt, NSamples):
        number_of_traces = len(marker_id) * int(dbm/dbt)
        chunks = []
        new_markers = []
        for i in range(len(marker_id)-1):
            chunks.append(image[:,marker_id[i]:marker_id[i+1]].astype('float32'))
        interpolated_image = np.zeros((NSamples, number_of_traces))
        number_of_traces_in_chunk = int(number_of_traces / len(chunks))
        new_markers.append(0)
        for num, chunk in enumerate(chunks):
            left = number_of_traces_in_chunk*num
            right = number_of_traces_in_chunk*(num+1)
            new_markers.append(right)
            interpolated_image[:,left:right] = cv2.resize(chunk, ( number_of_traces_in_chunk,NSamples),
                                    interpolation=cv2.INTER_NEAREST)
        image = interpolated_image
        return image, new_markers
    
    @staticmethod
    def get_markers_sgy(path):
        markers = []
        trace_number = 0
        with open(path, 'rb') as f:
            f.seek(3600) 
            while True:
                trace_file_header = f.read(240)

                if trace_file_header == b'':
                    break
                trace_len = struct.unpack('H', trace_file_header[114:116])[0]
                is_trace_marked = struct.unpack('H', trace_file_header[238:240])[0]
                if is_trace_marked != 0:
                    markers.append(trace_number)
                trace_number+=1
                f.seek(trace_len*2, 1)
                
        return markers
            
            

    def __read_gpr_data(self, path):
        if self.__is_read_config:
            gpr = gpr_file.GPR_file(path)
            gpr.read_file()
            _,_,length_of_wood,_ = self.__get_parameters()
            sup_config = {
                            "length_of_wood" : length_of_wood,
                            "distance_between_trace": 0.1 # TODO
                         }
            gpr.interpolate(sup_config)
            red_line = int(np.mean(np.argmax(np.diff(gpr.image, axis=0),axis = 0) - 5))
            return gpr.image[:self.__calculate_crop_param()+red_line], gpr.marker_id
        else:
            return None, None
    
    def __choose_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose File", "", "All Files (*);;Text Files (*.txt)", options=options)
        self.file_path = file_path
        if file_path:
            if file_path.endswith('.sgy'):
                self.seismogram, self.markers = self.__read_segy_data(file_path)
            elif file_path.endswith('.gpr') or file_path.endswith('.gpr2'):
                self.seismogram, self.markers = self.__read_gpr_data(file_path)
        
    def __get_parameters(self):
        permittivity = self.permittivity_param_window.text()
        svd = self.svd_param_window.text()
        length = self.length_wood_param_window.text()
        dt = self.dt_window.text()
        self.base_configs.set_configs(permittivity, svd, length, dt)
        return float(permittivity), int(svd), int(length), float(dt)
    
    def __is_read_config(self):
        if None in self.__get_parameters():
            return False
        else:
            return True

    def __calculate_crop_param(self):
        if self.__is_read_config():
            permittivity, _, length, dt = self.__get_parameters()
            BASE_SPEED = 30.0 # sm/ns
            velocity = BASE_SPEED / permittivity**0.5
            distance = length / np.pi
            self.length = length
            return np.round(distance / velocity / dt, 0).astype(int)
            
        
    def send_parameters(self):
        if self.seismogram is not None and self.__is_read_config():
            _, svd_components, _, _ = self.__get_parameters()
            self.parent().receive_read_file(self.seismogram, svd_components, self.markers, self.file_path, self.length)
            self.close()


class ConfigWorker():
    def __init__(self):
        self.CONFIG_PATH = "base_values.json"
        with open(self.CONFIG_PATH) as f:
            self.read_configs = json.load(f)

    def set_configs(self, permittivity, svd, length, dt):
        configs = {
                    "Permittivity": permittivity,
                    "SVD components": svd,
                    "Length of wood" : length,
                    "Distance between trace": dt
        }
        with open(self.CONFIG_PATH, 'w') as f:
            json.dump(configs, f)