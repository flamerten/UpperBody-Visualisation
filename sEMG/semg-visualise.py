import paramiko
import os
from PyQt5 import QtWidgets, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import random

ubuntu_dir = "/home/ubuntu/UpperBodyPOC/sEMG/"

target_file = ubuntu_dir + "reading.txt"

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect("192.168.1.111", port = 22, username = "ubuntu",password="rosaparks")

sftp=ssh_client.open_sftp()

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        self.x = list(range(100))  # 100 time points
        self.y = [random.randint(0,100) for _ in range(100)]  # 100 data points
        self.graphWidget.setBackground('w')

        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line =  self.graphWidget.plot(self.x, self.y, pen=pen)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()


    def update_plot_data(self):

        self.x = self.x[1:]  # Remove the first y element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        res = ""
        while True:
            try:
                readfile = sftp.open(target_file)
                res=readfile.read()
                res = int(res)
                break
            except:
                pass

        self.y = self.y[1:]  # Remove the first 
        self.y.append(int(res))  # Add a new random value.

        self.data_line.setData(self.x, self.y)  # Update the data.

app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec_())

