import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

class MyGraphicsLayout(pg.GraphicsLayoutWidget):
    def __init__(self):
        super().__init__()

        # Add a plot item
        self.plot = self.addPlot(title="Press 'R' to autoscale, 'Q' to quit")
        self.curve = self.plot.plot([1, 3, 2, 4])

        # Ensure the widget accepts keyboard focus
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_R:
            self.plot.getViewBox().autoRange()
            print("Auto-range triggered")
        elif key == QtCore.Qt.Key_Q:
            QtWidgets.QApplication.quit()
        else:
            print(f"Key pressed: {key}")

        super().keyPressEvent(event)