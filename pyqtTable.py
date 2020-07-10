import sys 
from PyQt5.QtWidgets import *

'''
This module is a Pyqt5 constructor fo Table creation and population with predefined data.
"setData" function populates a table with data from namedtuples list previously calculated '''


#Table Main Window 
class Table(QWidget): 
    def __init__(self, dev_list):
        self.dev_list = dev_list
        super().__init__() 
        self.title = 'Overloaded  Devices'
        self.left = 0
        self.top = 0
        self.width = 550
        self.height = 150
        self.setWindowTitle(self.title) 
        self.setGeometry(self.left, self.top, self.width, self.height) 
        self.createTable(dev_list) 
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tableWidget) 
        self.setLayout(self.layout) 
        self.setData(dev_list)
        self.show()                                            # show root window 
   
    def createTable(self, dev_list):                                     # create table in root window
        self.tableWidget = QTableWidget() 
  
        self.tableWidget.setRowCount(len(dev_list))          # rows count   
        self.tableWidget.setColumnCount(len(dev_list[1]))    # columns count   
  
        self.tableWidget.horizontalHeader().setStretchLastSection(True) 
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()
        

    def setData(self, dev_list):                                # insert data into the table from namedtuples
        for idx1, y  in enumerate(dev_list):
            for idx2, item in enumerate(dev_list[idx1]):
                if idx2 == 0:
                    newitem = QTableWidgetItem(item)
                else:
                    newitem = QTableWidgetItem(str(item)+'%')
                self.tableWidget.setItem(idx1, idx2, newitem)
        self.tableWidget.setHorizontalHeaderLabels(dev_list[1]._fields)
    
