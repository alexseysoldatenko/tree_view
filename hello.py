import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
import pyqtgraph as pg

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Real-Time Plotting")

        # Create PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)

        # Initialize variables for drawing
        self.drawing = False
        self.pen = pg.mkPen(color='r', width=2)
        self.curve = None
        self.points = []

    def mousePressEvent(self, event):
        if event.button() == 1:  # Left mouse button
            self.drawing = True
            self.points = []
            self.points.append(self.plot_widget.plotItem.vb.mapSceneToView(event.pos()))

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.points.append(self.plot_widget.plotItem.vb.mapSceneToView(event.pos()))
            if self.curve:
                self.plot_widget.removeItem(self.curve)
            self.curve = pg.PlotCurveItem(x=[p.x() for p in self.points], y=[p.y() for p in self.points], pen=self.pen)
            self.plot_widget.addItem(self.curve)

    def mouseReleaseEvent(self, event):
        if event.button() == 1:  # Left mouse button
            self.drawing = False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())