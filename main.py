from gui_application import *

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
    window = MainWindow()
    window.show()
    app.exec()
