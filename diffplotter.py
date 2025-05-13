# -*- coding: utf-8 -*-

import logging
import os
import sys
import json
import numpy as np
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cod_helpers import search_cif, download_cifs
from opts import PLOTOPTIONS, PENS, CROSSHAIR_OPTIONS, UNITS
import dmath
#from graphics_items import MyGraphicsLayout
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QRunnable, QThreadPool
#from multiprocessing import Queue
#from threading import Thread
from search_ui import Ui_MainWindow
from pymatgen.analysis.diffraction.xrd import XRDCalculator
from pymatgen.core.structure import Structure
import pyqtgraph as pg

#from PyQt5.uic import loadUi


logFormatter = logging.Formatter(
    "%(asctime)-25.25s %(threadName)-12.12s %(name)-25.24s %(levelname)-10.10s %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)
# logging.getLogger().setLevel(logging.DEBUG)
fileHandler = logging.FileHandler(os.path.join(os.getcwd(), 'log.log'))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)




class cod_search_worker(QObject):
    """
    This solution sort of quits after the first search, and does not allow for
    multiple searches.
    A possible solution is to use a thread pool, and run the search in a separate thread.

    Args:
        QObject (_type_): _description_
    """
    result = pyqtSignal(list)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs = kwargs
        logging.debug("Worker initialized with arguments:")
        logging.debug(self.kwargs)

    @pyqtSlot()
    def run(self):
        """
        Executes a worker process to perform a search operation and handle results.
        This method attempts to execute a search operation using the provided keyword arguments.
        It emits the search results if successful, or an error message if no results are found
        or an exception occurs. The method ensures that the `finished` signal is emitted
        regardless of the outcome.
        Emits:
            result: Emits the search results as a list. Emits an empty list if no results are found
                    or an exception occurs.
            error: Emits an error message as a string if an exception occurs or no results are found.
            finished: Emits a signal indicating that the worker process has completed execution.
        Logs:
            Logs debug messages indicating the start and end of the worker process.
        """
        try:
            results = search_cif(**self.kwargs)
            if results is not None:
                self.result.emit(results)
            else:
                self.error.emit("No entries found.")
                self.result.emit([])
        except Exception as e:
            self.error.emit(str(e))
            self.result.emit([])
        finally:
            pass  # Remove redundant emit call
        logging.debug("Worker finished")

class _cod_search_signal(QObject):
    result = pyqtSignal(list)
    finished = pyqtSignal()
    error = pyqtSignal(str)

class cod_search_worker2(QRunnable):
    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs = kwargs
        self.signals = _cod_search_signal()
        logging.debug("Worker initialized with arguments:")
        logging.debug(self.kwargs)

    @pyqtSlot()
    def run(self):
        """
        Executes a worker process to perform a search operation and handle results.
        This method attempts to execute a search operation using the provided keyword arguments.
        It emits the search results if successful, or an error message if no results are found
        or an exception occurs. The method ensures that the `finished` signal is emitted
        regardless of the outcome.
        Emits:
            result: Emits the search results as a list. Emits an empty list if no results are found
                    or an exception occurs.
            error: Emits an error message as a string if an exception occurs or no results are found.
            finished: Emits a signal indicating that the worker process has completed execution.
        Logs:
            Logs debug messages indicating the start and end of the worker process.
        """
        try:
            results = search_cif(**self.kwargs)
            if results is not None:
                self.signals.result.emit(results)
            else:
                self.signals.error.emit("No entries found.")
                self.signals.result.emit([])
        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.result.emit([])
        finally:
            pass  # Remove redundant emit call
        logging.debug("Worker finished")
        self.signals.finished.emit()


class cod_download_worker(QRunnable):
    def __init__(self, cod_id, save_path="./cif"):
        super().__init__()
        self.cod_id = cod_id
        self.save_path = save_path

    @pyqtSlot()
    def run(self):
        try:
            download_cifs([self.cod_id], self.save_path)
            logging.debug(f"Downloaded {self.cod_id} to {self.save_path}")
        except Exception as e:
            logging.error(f"Error downloading CIFs: {e}")
    

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)  # initialize the UI elements

        # setting up ui details
        self.setWindowTitle("COD Search")
        self.ui.tableWidget.setColumnCount(4)
        self.ui.splitter.setSizes([300, 200])
        self.ui.splitter_2.setSizes([300, 200])

        self.ui.pushButton_search.clicked.connect(self.search_button_clicked2)
        self.ui.pushButton_reset.clicked.connect(self.reset_button_clicked)
        self.ui.pushButton_add_to_selected.clicked.connect(self.add_to_selected)
        self.ui.pushButton_remove_from_selected.clicked.connect(self.remove_from_selected)

        self.ui.pushButton_download_selected.clicked.connect(self.download_selected)
        self.ui.pushButton_download_all.clicked.connect(self.download_all)

        self.ui.tableWidget.currentItemChanged.connect(self.fill_detailed_view)
        self.ui.tableWidget_selected.currentItemChanged.connect(self.fill_detailed_view)

        # setting up internal variables
        self.results = []
        self.selected_cifs = []
        self.threadPool = QThreadPool.globalInstance()

        # plot

        # Trying to set up the graphics layout widget with a custom class for keyboard events.
        # not yet operational

        # layout = self.ui.gLW.parent().layout()
        # index = layout.indexOf(self.ui.gLW)
        # size_policy = self.ui.gLW.sizePolicy()
        # layout.removeWidget(self.ui.gLW)
        # self.ui.gLW.deleteLater()
        # self.ui.graphicsLayoutWidget = MyGraphicsLayout()
        # layout.insertWidget(index, self.ui.graphicsLayoutWidget)
        # self.ui.graphicsLayoutWidget.setSizePolicy(size_policy)


        self.prep_plot()
        self.ui.pushButton_add.clicked.connect(self.add_all_curves)
        self.ui.pushButton_add.setText("Add all curves")
        self.ui.pushButton_delete.setText("----")
        #self.ui.pushButton_delete.clicked.connect(self.remove_curve)

        self.ui.comboBox_peak_shape.addItems(["Lorentzian", "Voigt", "Gaussian"])
        self.ui.comboBox_peak_shape.setCurrentIndex(0)
        self.ui.comboBox_peak_shape.currentIndexChanged.connect(self.update_peak_shape_width)
        self.ui.doubleSpinBox_peak_width.setValue(PLOTOPTIONS['peak_width'])
        self.ui.doubleSpinBox_peak_width.setRange(0.001, 0.1)
        self.ui.doubleSpinBox_peak_width.setSingleStep(0.001)
        self.ui.doubleSpinBox_peak_width.setDecimals(3)
        self.ui.doubleSpinBox_peak_width.valueChanged.connect(self.update_peak_shape_width)

        self.ui.checkBox_autoscale.setChecked(PLOTOPTIONS['autoscale'])
        self.ui.checkBox_autoscale.stateChanged.connect(self.update_autoscale)
        
        #proxy = pg.SignalProxy(self.plot.getViewBox().scene().sigMouseMoved, rateLimit=60, slot=self.cursorMove)
        self.plot.getViewBox().scene().sigMouseMoved.connect(self.cursorMove)

        self.label2dR = self.ui.graphicsLayoutWidget.addLabel(text="", row=1, col=0, colspan=1, justify='left')
        self.label2dC = self.ui.graphicsLayoutWidget.addLabel(text="", row=1, col=1, colspan=1, justify='left')
        self.label2dL = self.ui.graphicsLayoutWidget.addLabel(text="", row=1, col=2, colspan=1, justify='left')

        self.plotVline = pg.InfiniteLine(angle=90, movable=False, pen=CROSSHAIR_OPTIONS['color'])
        self.plotHline = pg.InfiniteLine(angle=0, movable=False, pen=CROSSHAIR_OPTIONS['color'])
        self.ui.checkBox_crosshair.setChecked(False)
        self.ui.checkBox_crosshair.stateChanged.connect(self.crosshair_visibility)

        self.ui.comboBox_unit.addItems(UNITS)
        self.current_unit = self.ui.comboBox_unit.currentText()
        self.ui.comboBox_unit.setEnabled(False)

    def search_button_clicked(self):
        '''
        This is great, but does not allow for multiple searches.
        A possible solution is to use a thread pool, and run the search in a separate thread.
        '''
        self.statusBar().showMessage("Searching...")

        cod_id = self.ui.lineEdit_cod_id.text()
        formula = self.ui.lineEdit_formula.text()
        elements = self.ui.lineEdit_elements.text()
        notelements = self.ui.lineEdit_notelements.text()
        minelements = self.ui.spinBox_minelements.value()
        maxelements = self.ui.spinBox_maxelements.value()

        logging.debug(f"COD ID: {cod_id}")
        logging.debug(f"Formula: {formula}")
        logging.debug(f"Elements: {elements}")
        logging.debug(f"Number of elements: {notelements}")
        logging.debug(f"Minimum number of elements: {minelements}")
        logging.debug(f"Maximum number of elements: {maxelements}")

        self.thread = QThread()
        self.worker = cod_search_worker(cod_id=cod_id,
                              formula=formula,
                              elements=elements.split(",") if elements else [],
                              notelements=notelements.split(",") if notelements else [],
                              minelements=minelements,
                              maxelements=maxelements)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.result.connect(self.handle_results)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        qApp = QApplication.instance()
        if qApp is not None:
            qApp.aboutToQuit.connect(self.thread.quit)
        self.thread.start()


    def search_button_clicked2(self):
        self.statusBar().showMessage("Searching...")

        cod_id = self.ui.lineEdit_cod_id.text()
        formula = self.ui.lineEdit_formula.text()
        elements = self.ui.lineEdit_elements.text()
        notelements = self.ui.lineEdit_notelements.text()
        minelements = self.ui.spinBox_minelements.value()
        maxelements = self.ui.spinBox_maxelements.value()

        logging.debug(f"COD ID: {cod_id}")
        logging.debug(f"Formula: {formula}")
        logging.debug(f"Elements: {elements}")
        logging.debug(f"Number of elements: {notelements}")
        logging.debug(f"Minimum number of elements: {minelements}")
        logging.debug(f"Maximum number of elements: {maxelements}")

        worker = cod_search_worker2(cod_id=cod_id,
                              formula=formula,
                              elements=elements.split(",") if elements else [],
                              notelements=notelements.split(",") if notelements else [],
                              minelements=minelements,
                              maxelements=maxelements)

        worker.signals.result.connect(self.handle_results)
        #worker.signals.error.connect(self.handle_error)
        
        self.threadPool.start(worker)

    def handle_results(self, result):
        self.results = result
        if self.results:
            if len(self.results) == 1:
                logging.debug("Found 1 entry.")
                self.statusBar().showMessage("Found 1 entry.")
            else:
                logging.debug(f"Found {len(self.results)} entries.")
                self.statusBar().showMessage(f"Found {len(self.results)} entries.")
        else:
            logging.debug("No entries found.")
            self.statusBar().showMessage("No entries found.")
        self.fill_table(self.results)


    def reset_button_clicked(self):
        self.ui.lineEdit_cod_id.clear()
        self.ui.lineEdit_formula.clear()
        self.ui.lineEdit_elements.clear()
        self.ui.lineEdit_notelements.clear()
        self.ui.spinBox_minelements.setValue(0)
        self.ui.spinBox_maxelements.setValue(0)
        logging.debug("Reset button clicked!")

    def fill_table(self, results):
        if not results:
            self.ui.tableWidget.setRowCount(0)
            self.ui.tableWidget_detail.setRowCount(0)
            return
        # Clear the table before filling it with new data
        self.ui.tableWidget.clear()

        self.ui.tableWidget.setRowCount(len(self.results))
        self.ui.tableWidget.setHorizontalHeaderLabels(["COD ID", "Formula", "Spacegroup", "a, b, c, alpha, beta, gamma"])
        for i, result in enumerate(self.results):
            self.ui.tableWidget.setItem(i, 0, QTableWidgetItem(result["file"]))
            self.ui.tableWidget.setItem(i, 1, QTableWidgetItem(result["formula"]))
            self.ui.tableWidget.setItem(i, 2, QTableWidgetItem(result["sgHall"]))
            cell_pars = f"{result['a']}, {result['b']}, {result['c']}, {result['alpha']}, {result['beta']}, {result['gamma']}"
            self.ui.tableWidget.setItem(i, 3, QTableWidgetItem(cell_pars))
    
    def fill_detailed_view(self):
        # Here you can implement the logic to fill the detailed view with the selected entry
        current_row = self.ui.tableWidget.currentRow()
        if current_row >= 0:
            for i,(k,v) in enumerate(self.results[current_row].items()):
                self.ui.tableWidget_detail.setRowCount(len(self.results[current_row]))
                self.ui.tableWidget_detail.setColumnCount(2)
                self.ui.tableWidget_detail.setHorizontalHeaderLabels(["Property", "Value"])
                self.ui.tableWidget_detail.setItem(i, 0, QTableWidgetItem(k))
                self.ui.tableWidget_detail.setItem(i, 1, QTableWidgetItem(str(v)))
        else:
            self.ui.tableWidget_detail.setRowCount(0)
        
        current_selected_row = self.ui.tableWidget_selected.currentRow()
        if current_selected_row >= 0:
            for i,(k,v) in enumerate(self.selected_cifs[current_selected_row].items()):
                self.ui.tableWidget_selected_detail.setRowCount(len(self.selected_cifs[current_selected_row]))
                self.ui.tableWidget_selected_detail.setColumnCount(2)
                self.ui.tableWidget_selected_detail.setHorizontalHeaderLabels(["Property", "Value"])
                self.ui.tableWidget_selected_detail.setItem(i, 0, QTableWidgetItem(k))
                self.ui.tableWidget_selected_detail.setItem(i, 1, QTableWidgetItem(str(v)))
        else:
            self.ui.tableWidget_selected_detail.setRowCount(0)
            

            #text_str = json.dumps(self.results[current_row]).replace(",", ",\n")
            #self.ui.textBrowser.setPlainText(text_str)

    def add_to_selected(self):
        current_row = self.ui.tableWidget.currentRow()
        if current_row >= 0:
            selected_item = self.results[current_row]
            if selected_item not in self.selected_cifs:
                self.selected_cifs.append(selected_item)
                logging.debug(f"Added to selected: {selected_item['file']}")
            else:
                logging.debug(f"Already in selected: {selected_item['file']}")
        else:
            logging.debug("No item selected.")
            self.statusBar().showMessage("No item selected.")
        self.update_selected_table()


    def remove_from_selected(self):
        current_selected_row = self.ui.tableWidget_selected.currentRow()
        if current_selected_row >= 0:
            selected_item = self.selected_cifs[current_selected_row]
            self.selected_cifs.remove(selected_item)
            logging.debug(f"Removed from selected: {selected_item['file']}")
        else:
            logging.debug("No item selected.")
            self.statusBar().showMessage("No item selected.")
        self.update_selected_table()

    def update_selected_table(self):
        # Update the selected table
        self.ui.tableWidget_selected.clear()
        self.ui.tableWidget_selected.setRowCount(len(self.selected_cifs))
        self.ui.tableWidget_selected.setColumnCount(4)
        self.ui.tableWidget_selected.setHorizontalHeaderLabels(["COD ID", "Formula", "Spacegroup", "a, b, c, alpha, beta, gamma"])
        for i, selected_item in enumerate(self.selected_cifs):
            self.ui.tableWidget_selected.setItem(i, 0, QTableWidgetItem(selected_item["file"]))
            self.ui.tableWidget_selected.setItem(i, 1, QTableWidgetItem(selected_item["formula"]))
            self.ui.tableWidget_selected.setItem(i, 2, QTableWidgetItem(selected_item["sgHall"]))
            cell_pars = f"{selected_item['a']}, {selected_item['b']}, {selected_item['c']}, {selected_item['alpha']}, {selected_item['beta']}, {selected_item['gamma']}"
            self.ui.tableWidget_selected.setItem(i, 3, QTableWidgetItem(cell_pars))
        self.fill_detailed_view()

    def download_selected(self):
        cifs = self.selected_cifs
        self.download_cifs(cifs)

    def download_all(self):
        cifs = self.results
        self.download_cifs(cifs)

    def download_cifs(self, cifs):
        for c in cifs:
            cod_id = c["file"]
            if cod_id:
                worker = cod_download_worker(cod_id=cod_id, save_path="./cif")
                self.threadPool.start(worker)
                logging.debug(f"Started download for {cod_id}")
                self.statusBar().showMessage(f"Downloading {cod_id}...", 1000) # messages for 1 second
            else:
                logging.error("Invalid COD ID.")


    def prep_diffractograms(self):
        '''
        This function should be placed in a separate thread, and a separate file.

        If plotting with gaussian peaks is required, this should also be done here
        '''
        # download cifs
        self.download_selected()

        self.diffractograms = {}
        xrd_calculator = XRDCalculator(wavelength=0.1)

        #logging.debug(f'{self.selected_cifs=}')

        x = np.linspace(PLOTOPTIONS['xrange'][0], PLOTOPTIONS['xrange'][1], PLOTOPTIONS['npoints'])

        for selected_cif in self.selected_cifs:
            cif_id = selected_cif["file"]
            cif_file = os.path.join("./cif", cif_id + ".cif")
            if os.path.exists(cif_file):
                try:
                    structure = Structure.from_file(cif_file)
                    pattern = xrd_calculator.get_pattern(structure, scaled=False, two_theta_range=(0, 20))
                    self.diffractograms[cif_id] = {
                        "dhkl": pattern.d_hkls,
                        "hkls": pattern.hkls,
                        "2theta": x,
                        "peak_position": pattern.x,
                        "peak_height": pattern.y,
                        #"2theta": pattern.x,
                        "intensity": dmath.combine_peaks(x, 
                                                   peak_func=PLOTOPTIONS['peak_shape'],
                                                   x0=pattern.x,
                                                   amp=pattern.y,
                                                   offset=PLOTOPTIONS['offset'],
                                                   sig=PLOTOPTIONS['peak_width']
                                                   ),

                        #"intensity": pattern.y
                        }
                    logging.debug(f"Generated diffractogram for {cif_id}")
                except Exception as e:
                    logging.error(f"Error generating diffractogram for {cif_id}: {e}")

    def prep_plot(self):
        self.plot = self.ui.graphicsLayoutWidget.addPlot(title=PLOTOPTIONS['title'], colspan=3, row=0)
        self.plot.setLabel('left', PLOTOPTIONS['ylabel'])
        self.plot.setLabel('bottom', PLOTOPTIONS['xlabel'])
        self.plot.showGrid(x=True, y=True)
        self.plot.setXRange(0, 20)
        self.plot.setYRange(-2, 2)
        #plot.setTitle("XRD Pattern")
        self.plot.addLegend()

    def add_curve(self):
        self.prep_diffractograms()
        num_curves = len(self.plot.listDataItems())
        #self.plot.plot(self.x, self.y[len(plots)], pen='r', name="XRD Pattern", symbol='o', symbolPen='r', symbolBrush=('b'), symbolSize=5)        
        #logging.debug(self.diffractograms)
        th = self.diffractograms[self.selected_cifs[num_curves]["file"]]["2theta"]
        I = self.diffractograms[self.selected_cifs[num_curves]["file"]]["intensity"]
        cifID = self.selected_cifs[num_curves]["file"]
        formula = self.selected_cifs[num_curves]["formula"]
        self.plot.plot(th, I, pen=PENS[num_curves], name=f"{cifID} {formula}")
        logging.debug('rescaling')
        self.plot.getViewBox().autoRange()

        # adding floating legend on the top right corner, seems a bit buggy
        # self.legend = pg.LegendItem(offset=(-10, 10), verSpacing=10)
        # self.legend.setParentItem(self.plot)
        # self.legend.anchor((1, 0), (1, 0))
        # self.legend.addItem(self.plot.listDataItems()[-1], f"{cifID} {formula}")
        

    def remove_curve(self):
        plots = self.plot.listDataItems()
        if len(plots) > 0:
            self.plot.removeItem(plots[-1])
            #self.legend.removeItem(plots[-1])
        else:
            logging.debug("No plots to delete.")
        logging.debug("Curve removed.")

    def add_all_curves(self):
        self.prep_diffractograms()
        logging.debug(f'{self.diffractograms.keys()=}')
        logging.debug(f'selected CIF files: {[c['file'] for c in self.selected_cifs]}')
        # remove curves
        plots = self.plot.listDataItems()
        if len(plots) > 0:
            for plot in plots:
                self.plot.removeItem(plot)
        for i, selected_cif in enumerate(self.selected_cifs):
            th = self.diffractograms[selected_cif["file"]]["2theta"]
            I = self.diffractograms[selected_cif["file"]]["intensity"]
            cifID = selected_cif["file"]
            formula = selected_cif["formula"]
            self.plot.plot(th, I, pen=PENS[i], name=f"{cifID} {formula}", autoDownsample=True)
        logging.debug('rescaling')
        self.plot.getViewBox().autoRange()

    def update_peak_shape_width(self):
        # Update the peak shape based on the selected option
        PLOTOPTIONS['peak_shape'] = self.ui.comboBox_peak_shape.currentText().lower()
        PLOTOPTIONS['peak_width'] = self.ui.doubleSpinBox_peak_width.value()
        PLOTOPTIONS['autoscale'] = self.ui.checkBox_autoscale.isChecked()
        # Replot the curves with the new peak shape
        for i, (diffr, plot) in enumerate(zip(self.diffractograms.keys(), self.plot.listDataItems())):
            th = self.diffractograms[diffr]["2theta"]
            I = dmath.combine_peaks(th, 
                                    peak_func=PLOTOPTIONS['peak_shape'],
                                    x0=self.diffractograms[diffr]["peak_position"],
                                    amp=self.diffractograms[diffr]["peak_height"],
                                    sig=PLOTOPTIONS['peak_width'],
                                    offset=PLOTOPTIONS['offset'])
            # update the plot data
            plot.setData(th, I)
        if PLOTOPTIONS['autoscale']:
            self.plot.getViewBox().autoRange()

    def update_autoscale(self):
        PLOTOPTIONS['autoscale'] = self.ui.checkBox_autoscale.isChecked()
        if PLOTOPTIONS['autoscale']:
            self.plot.getViewBox().autoRange()

    def crosshair_visibility(self):
        if self.ui.checkBox_crosshair.isChecked():
            self.plot.addItem(self.plotVline, ignoreBounds=True)
            self.plot.addItem(self.plotHline, ignoreBounds=True)
        else:
            self.plot.removeItem(self.plotVline)
            self.plot.removeItem(self.plotHline)

    def cursorMove(self, event):
        pos = event
        view_box = self.plot.getViewBox()

        if view_box.sceneBoundingRect().contains(pos):
            mouse_point = view_box.mapSceneToView(pos)
            #self.label2dR.setText(f"X: {mouse_point.x():6.2f}, Y: {mouse_point.y():6.2f}")
            #self.label2dC.setText(f"X: {mouse_point.x():6.2f}, Y: {mouse_point.y():6.2f}")
            self.label2dL.setText(f"X: {mouse_point.x():6.3f}, Y: {mouse_point.y():6.2e}")

            if self.ui.checkBox_crosshair.isChecked():
                self.plotVline.setPos(mouse_point.x())
                self.plotHline.setPos(mouse_point.y())
            #print(mouse_point)
            # index = int(mouse_point.x())
            # if 0 <= index < len(self.diffractograms):
            #     # Update the cursor position
            #     self.cursor.setPos(mouse_point.x(), mouse_point.y())
            #     # Update the text item with the new coordinates
            #     self.text_item.setHtml(f"<div style='background-color: white; padding: 5px;'>"
            #                            f"X: {mouse_point.x():.2f}<br>"
            #                            f"Y: {mouse_point.y():.2f}</div>")
            #     self.text_item.setPos(mouse_point.x(), mouse_point.y())
    



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
