from PyQt5.QtWidgets import QMainWindow, QTextEdit, QAction, QApplication, QFileDialog
import sys
import design
import os

class Example(QMainWindow, design.Ui_MainWindow):
    def __init__(self, parent=None):
        super(Example, self).__init__(parent)
        self.setupUi(self)
        self.btnBrowse.clicked.connect(self.browse_folder)

    def browse_folder(self):
        self.listWidget.clear()
        directory = QFileDialog.getExistingDirectory(self,
                                                           "Pick a folder")
        if directory: # if user didn't pick a directory don't continue
            for file_name in os.listdir(directory): # for all files, if any, in the directory
                self.listWidget.addItem(file_name)  # add file to the listWidget
        


def main():
    app = QApplication(sys.argv)
    form = Example()
    form.show()
    app.exec_()

main()

