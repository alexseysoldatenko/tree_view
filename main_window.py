import cv2
from scipy import signal
import numpy as np
import matplotlib.pyplot as plt
from read_window import ReadWindow
from PyQt5.QtWidgets import QCheckBox, QMainWindow, QGridLayout, QWidget, QPushButton
from filter_window import FilterWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from scipy.signal import hilbert


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_read_config = False

        self.setWindowTitle("Wood viewer 3000")
        self.setGeometry(100, 100, 950, 800)

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)

        layout = QGridLayout(centralWidget)

        self.fig, self.ax = plt.subplots()
        read_file_button = QPushButton("Read File", self)
        layout.addWidget(read_file_button, 0, 0)

        receive_batterwoth_params_button = QPushButton("Butterworth Filter", self)
        receive_batterwoth_params_button.clicked.connect(self.__open_second_window)
        layout.addWidget(receive_batterwoth_params_button, 0, 1)
        self.setLayout(layout)

        amplitude_correction_button = QPushButton("Add amplitude correction", self)
        amplitude_correction_button.clicked.connect(
            self.__add_linear_amplitude_correction
        )
        layout.addWidget(amplitude_correction_button, 0, 2)

        median_filter_button = QPushButton("Median filter", self)
        median_filter_button.clicked.connect(self.__add_median_filter)
        layout.addWidget(median_filter_button, 0, 3)

        transform_to_circle_button = QPushButton("Circle transform", self)
        transform_to_circle_button.clicked.connect(self.__circle_transform)
        layout.addWidget(transform_to_circle_button, 0, 4)

        svd_button = QPushButton("SVD mute transform", self)
        svd_button.clicked.connect(self.__SVD_transform)
        layout.addWidget(svd_button, 1, 3)

        cut_button = QPushButton("Cut", self)
        cut_button.clicked.connect(self.__cut)
        layout.addWidget(cut_button, 1, 0)

        # def add save image button
        save_image_button = QPushButton("Save image", self)
        save_image_button.clicked.connect(self.__save_image)
        layout.addWidget(save_image_button, 1, 4)

        # pick_checkbox = QCheckBox('Check me', self)
        # pick_checkbox.stateChanged.connect(self.__checkBoxChanged)
        # layout.addWidget(pick_checkbox, 2, 5)

        read_file_button.clicked.connect(self.__read_file)

        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas, 2, 0, 1, 4)

    def __read_file(self):
        self.__open_read_file_window()

    def __save_image(self):
        cv2.imwrite("image.png", self.seismogram)

    def __plot_graph(self, mode="raw"):
        if self.seismogram is not None:
            self.ax.clear()
            if mode == "raw":
                self.ax.imshow(self.seismogram * -1, cmap="gray", aspect="auto")
                if not self.is_cutted:
                    red_line = np.argmax(np.diff(self.seismogram, axis=0), axis=0) - 5
                    self.ax.plot(
                        np.arange(self.seismogram.shape[1]),
                        np.ones(self.seismogram.shape[1]) * red_line,
                        "r",
                    )
                if self.markers is not None:
                    for marker in self.markers:
                        self.ax.plot(
                            marker * np.ones(self.seismogram.shape[0]),
                            np.arange(self.seismogram.shape[0]),
                            "r",
                        )
            elif mode == "circle":
                self.ax.scatter(
                    self.x_new,
                    self.y_new,
                    c=self.color,
                    cmap="gray",
                    marker="s",
                )
                locs_x, _ = plt.xticks()
                locs_y, _ = plt.yticks()
                radius = np.round(self.length / 2 / np.pi, 2)
                IMAGE_CONSTANT = 6 / 5
                labels = list(
                    np.round(
                        np.linspace(
                            -radius * IMAGE_CONSTANT,
                            radius * IMAGE_CONSTANT,
                            len(locs_x),
                            2,
                        )
                    )
                )
                plt.xticks(locs_x, labels)
                plt.xlabel("radius, sm")
                plt.ylabel("radius, sm")
                plt.yticks(locs_y, labels)
                plt.title(
                    self.path.split("/")[-1].replace(".gpr2", "").replace(".sgy", "")
                )
                plt.savefig(
                    f'image_folder/{self.path.split("/")[-1].replace(".gpr2", "").replace(".sgy", "")}.png'
                )

            self.canvas.draw()
            # image_from_plot = np.frombuffer(self.canvas., dtype=np.uint8)
            # image_from_plot = image_from_plot.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            # self.ax.imshow(image_flat)
            # self.canvass.draw()

    def __SVD_transform(self):
        P, L, U = np.linalg.svd(self.seismogram, full_matrices=False)
        L[: self.svd_components] = L[: self.svd_components] * np.sin(
            np.arange(self.svd_components) * np.pi / (self.svd_components * 2)
        )
        self.seismogram = P @ np.diag(L) @ U
        self.seismogram = signal.medfilt2d(self.seismogram, kernel_size=5)
        self.__plot_graph()

    def __checkBoxChanged(self):
        pass

    def __circle_transform(self):
        if hasattr(self, "seismogram"):
            self.seismogram = Window.interpolate_data(self.seismogram)[:, ::-1]
            xs, ys = self.seismogram.shape
            xs_range = np.tile(np.arange(xs), ys)
            ys_range = np.repeat(np.arange(ys), xs)
            x_new = ys_range * np.sin(2 * np.pi * xs_range / xs - np.pi)
            y_new = ys_range * np.cos(2 * np.pi * xs_range / xs - np.pi)
            self.x_new = x_new
            self.y_new = y_new
            self.color = self.seismogram[::-1, :]
            self.__plot_graph(mode="circle")

    @staticmethod
    def interpolate_data(data: np.array):
        max_shape = max(data.shape)
        return cv2.resize(data, (max_shape, max_shape))

    def __open_second_window(self):
        self.second_window = FilterWindow(self, self.seismogram)
        self.second_window.show()

    def __open_read_file_window(self):
        self.__read_file_window = ReadWindow(self)
        self.__read_file_window.show()

    def __add_linear_amplitude_correction(self):
        if hasattr(self, "seismogram"):
            self.seismogram = self.seismogram * np.linspace(
                0.1, 1, self.seismogram.shape[0]
            ).reshape((-1, 1))
            self.__plot_graph()

    def __add_median_filter(self):
        if hasattr(self, "seismogram"):
            self.seismogram -= np.median(self.seismogram, axis=1).reshape((-1, 1))
            self.__plot_graph()

    def receive_butterworth_parameters(self, param1, param2, param3, param4):
        self.butterwoth_low_first = param1
        self.butterwoth_high_first = param2
        self.butterwoth_low_second = param3
        self.butterwoth_high_second = param4
        # self.apply_butterwoth_filter()
        # self.__plot_graph()

    def receive_read_file(
        self, seismogram, svd_components, markers, path=None, length=None
    ):
        self.seismogram = seismogram
        self.markers = markers
        self.svd_components = svd_components
        self.is_cutted = False
        self.path = path
        self.length = length
        self.__plot_graph(mode="raw")

    def __cut(self):
        if hasattr(self, "seismogram"):
            red_line = np.mean(np.argmax(np.diff(self.seismogram, axis=0), axis=0) - 5)
            new_left = self.markers[1]
            new_right = self.markers[-2]
            self.markers = np.array(self.markers[1:-1]) - new_left
            self.seismogram = self.seismogram[int(red_line) :, new_left:new_right]
            self.is_cutted = True
            self.__plot_graph(mode="raw")
