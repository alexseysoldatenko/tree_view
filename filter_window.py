import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import  QVBoxLayout, QDialog, QLineEdit,  QPushButton, QLabel

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class FilterWindow(QDialog):
    def __init__(self, parent=None, *params):
        super(FilterWindow, self).__init__(parent)
        self.setWindowTitle('Input butterwoth filter parametrs')
        self.layout = QVBoxLayout()
        self.seismogram = params[0]


        self.param1_input = QLineEdit(self)
        self.param2_input = QLineEdit(self)
        self.param3_input = QLineEdit(self)
        self.param4_input = QLineEdit(self)

        self.layout.addWidget(QLabel("Parameter 1:"))
        self.layout.addWidget(self.param1_input)
        self.layout.addWidget(QLabel("Parameter 2:"))
        self.layout.addWidget(self.param2_input)
        self.layout.addWidget(QLabel("Parameter 3:"))
        self.layout.addWidget(self.param3_input)
        self.layout.addWidget(QLabel("Parameter 4:"))
        self.layout.addWidget(self.param4_input)

        ok_button = QPushButton('OK', self)
        ok_button.clicked.connect(self.send_parameters)
        

        self.fig, self.ax = plt.subplots()

        self.matplotlib_canvas = FigureCanvas(self.fig)
        self.layout.addWidget(self.matplotlib_canvas)

        self.layout.addWidget(ok_button)
        self.setLayout(self.layout)

        FilterWindow.calculate_spectrum(self)
        FilterWindow.plot(self)

    def send_parameters(self):
        param1 = self.param1_input.text()
        param2 = self.param2_input.text()
        param3 = self.param3_input.text()
        param4 = self.param4_input.text()
        self.parent().receive_butterworth_parameters(param1, param2, param3, param4)
        self.close()

    def calculate_spectrum(self):
        self.fourier = np.fft.fft(self.seismogram, axis = 1)

    def get_filter(self):
        param1 = self.param1_input.text()
        param2 = self.param2_input.text()
        param3 = self.param3_input.text()
        param4 = self.param4_input.text()

        
        
    def plot(self):
        self.ax.plot(np.sum(np.abs(self.fourier),axis = 1))
        self.matplotlib_canvas.draw()