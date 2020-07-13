from PyQt5.QtWidgets import *
from collections import namedtuple, deque
import re
from pyqtTable import Table
from rootWindow import MainWindow
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, simpledialog
import netmiko
from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException
import sys
import ipaddress
import threading
import socket
import json

   
if __name__ == '__main__':
    
    root = tk.Tk()
    window = MainWindow(root)
    root.mainloop()
    items_list = []
    alarm_list = []

    with open(r'/home/elil/GitRep/Device_Query_Tkinter/cfg_dict.json', 'r') as f:
        cfg_dict = ast.literal_eval(f.read())

    for value in cfg_dict.values():                                                            #  parse cfg data and arrange items into tuple per each device
        x,y,z = value.values()
        processor_memory_total_str = y.splitlines()[0].split(':')[1]
        processor_memory_total = int(re.search(('\d+'), processor_memory_total_str).group())
        processor_memory_used_str = y.splitlines()[0].split(':')[2]
        processor_memory_used = int(re.search(('\d+'), processor_memory_used_str).group())

        io_memory_total_str = y.splitlines()[1].split(':')[1]
        io_memory_total = int(re.search(('\d+'), io_memory_total_str).group())
        io_memory_used_str = y.splitlines()[1].split(':')[2]
        io_memory_used = int(re.search(('\d+'), io_memory_used_str).group())

        transient_memory_total_line = y.splitlines()[2].split(':')[1]
        transient_memory_total = int(re.search(('\d+'), transient_memory_total_line).group())
        transient_memory_used_str = y.splitlines()[2].split(':')[2]
        transient_memory_used = int(re.search(('\d+'), transient_memory_used_str).group())

        cpu_util = z.splitlines()[0].split()[-4]
        
        cpu = int(re.search(('\d+'), cpu_util).group())                                         # cpu utilisation
        processor_memory = round((processor_memory_used / processor_memory_total)*100, 3)       # available processor_memory
        io_memory = round((io_memory_used / io_memory_total)*100, 3)                            # available io_memory
        transient_memory = round((transient_memory_used / transient_memory_total)*100, 3)       # available transient_memory
        hostname = x.split()[1]                                                                 # hostname
        items_list.append((hostname, processor_memory, io_memory, transient_memory, cpu))                      


    router = namedtuple('router',['Hostname', 'Processor_Memory', 'Io_Memory', 'Transient_Memory', 'Cpu'])   #  create namedtuple class 
    for item in items_list:                                                                                  #  instaniate namedtuple class
        device = router(*item)
        #if (device.cpu  or device.io_memory or device.processor_memory  or device.transient_memory) >= 90:
        alarm_list.append(device)                                                                            # get list of devices with critical utilization       

    app = QApplication(sys.argv) 
    table = Table(alarm_list) 
    app.exec() 

