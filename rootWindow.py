import tkinter as tk
from tkinter import ttk
import time
from tkinter import messagebox
from tkinter import simpledialog
import netmiko
from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException
import sys
import ipaddress
from queue import Queue
from datetime import datetime
import threading
import json
import socket
from collections import deque



class Worker:
    def __init__(self):
        self.cfg = {}
        self.cfg_list = ['show run | include hostname', 'show processes memory | include  Total',
                         'show processes cpu | include CPU']
        self.dq = deque([])
        
    access_lock = threading.Lock()
    def portscan(self, host, port):
        address = (host, port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.25)
        connect = s.connect_ex(address)
        with self.access_lock:
            if connect == 0:
                s.close()
                return True
            else:
                return False
        
    def threader(self, host):
       if self.portscan(host,22) == True:
            self.dq.append(host)
                
    def ssh_connect(self, ip, conf_list):
       params = {'device_type': 'cisco_ios',
                  'ip': ip,
                  'username': 'elil',
                  'password': 'cisco'}
       try:
           ssh = netmiko.ConnectHandler(**params)
           for command in conf_list:
               result = ssh.send_command(command)
               time.sleep(0.9)
               self.cfg[command] = result
           ssh.disconnect()
       except OSError as err:
           messagebox.showinfo(title='Fatal Error', message=err)
       except NetMikoTimeoutException as err:
           messagebox.showinfo(title='Fatal Error', message=err)
       return self.cfg
     

class MainWindow(ttk.Frame):
    ''' Main GUI window '''
    def __init__(self, master):
        ''' Init main window '''
        ttk.Frame.__init__(self, master=master)
        self.master.title('Main Window')
        self.master.style = ttk.Style()
        self.master.style.configure('TFrame', background ='#e1d8a1')
        self.master.style.configure('TButton', background ='#b1d8b9')
        self.master.style.configure('TLabel', background ='#e1d8b1', font=('Arial', 10, 'bold'))
        self.master.style.configure('Header.TLabel', background ='#e1d8b9', font=('Arial', 15, 'bold'))
        self.input_window = ttk.Frame(self.master, width=500, height=100, relief=tk.SUNKEN)
        self.net_entry = ttk.Entry(self.input_window, width=15)
        self.net_entry.grid(row=2, columnspan=2, padx=15,pady=(2,7))
        self.txtvar = tk.StringVar()
        self.txtvar.set('Please Input Network Address')
        self.message = tk.Message(self.input_window, width=350, bd=10, bg='#e1d8a1',
                                  relief=tk.RIDGE, textvariable=self.txtvar, font=('Arial', 12, 'bold'))
        self.message.grid(row=1, columnspan=2, padx=10, pady=5)
        self.clear_button = ttk.Button(self.input_window, text='Clear', command=self.clear_entry)
        self.clear_button.grid(row=3, column=1, padx=5, pady=(12,5), sticky='w')
        self.submit_button = ttk.Button(self.input_window, text='Submit', command=self.submit_net)
        self.submit_button.grid(row=3, column=0, padx=5, pady=(12,5), sticky='e')
        self.master.bind('<Escape>', func=self.destroy_self)
        self.master.bind("<Return>", func=self.submit_net)
        self.master.bind("<KP_Enter>", func=self.submit_net)
        self.input_window.pack()
        self.input_window.focus_set()

    @staticmethod                                             # function to check network address sanity
    def check_subnet(network):
        try:
            ipaddress.ip_network(network, strict=True)
            return True
        except ValueError as err:
            messagebox.showerror(title="Prompt Error", message=err)
            return False

    def destroy_self(self, event=None):
        self.master.destroy()

    def clear_entry(self):
        self.net_entry.delete(0, 'end')

    def submit_net(self, event=None):                          # this function defines behavior when "submit_ip" button is pressed
        global hostlist
        hostlist = []
        ip_subnet = self.net_entry.get()                       # read subnet address and check sanity
        if self.check_subnet(ip_subnet) == True:
            self.clear_entry()
            _network = ipaddress.ip_network(ip_subnet)    
            if _network.num_addresses == 4294967296:
               self.txtvar.set("Zero subnet mask is not allowed. Try Again")
            elif _network.num_addresses == 1:
                self.txtvar.set("Network Address is Accepted")
                hostlist.append(_network.broadcast_address.compressed)
                self.master.iconify()
                self.start_progress()
            else:
                self.txtvar.set("Network Address is Accepted")
                for host in list(_network.hosts()):
                        hostlist.append(host.compressed)
                self.master.iconify()
                self.start_progress()
        else:
            self.clear_entry()
            self.txtvar.set("Wrong Input. Try again ")
        return hostlist
        

    def start_progress(self):
        ''' Open modal window '''
        prgs_window = ProgressWindow(self)                      # create progress window
        self.wait_window(prgs_window)
        

class ProgressWindow(simpledialog.Dialog):
    def __init__(self, parent):
        ''' Init progress window '''
        tk.Toplevel.__init__(self, master=parent)
        self.style = ttk.Style()
        self.style.configure('TFrame', background ='#e1d8a1')
        self.style.configure('TButton', background ='#b1d8b9')
        self.style.configure('TLabel', background ='#e1d8b1', font=('Arial', 10, 'bold'))
        self.style.configure('Header.TLabel', background ='#e1d8b9', font=('Arial', 15, 'bold'))
        self.length = 400
        self.active_hosts = []
        self.devlist = globals()['hostlist']
        self.create_window()
        self.create_widgets()
        self.launcher_foo()
              

    def create_window(self):
        ''' Create progress window '''
        self.focus_set()              # set focus on the ProgressWindow
        self.grab_set()               # make a modal window, so all events go to the ProgressWindow
        self.transient(self.master)   # show only one window in the task bar
        self.title('Progress execution bar')
        self.resizable(False, False)  # window is not resizable
        self.protocol(u'WM_DELETE_WINDOW', self.destroy_self)
        self.bind(u'<Escape>', self.destroy_self)  # cancel progress when <Escape> key is pressed

    def create_widgets(self):
        ''' Widgets for progress window are created here '''  
        self.var1 = tk.StringVar()
        self.var2 = tk.StringVar()
        self.num = tk.IntVar()
        self.maximum = len(self.devlist)
        ttk.Label(self, textvariable=self.var1).pack(padx=2)
        ttk.Label(self, textvariable=self.var2).pack(padx = 130)
        self.progress = ttk.Progressbar(master=self, maximum=self.maximum, orient='horizontal',
                                        length=self.length, variable=self.num, mode='determinate')
        self.progress.pack(padx=5, pady=3)
        ttk.Button(self, text='Cancel', command=self.destroy).pack(anchor='e', padx=5, pady=(0, 3))
       
 
    def launcher_foo(self):
        ''' Take next ip address and check for rachability '''
        n = self.num.get()
        host = self.devlist[n]                  # get host ip addresse from a GLOBAL variable 
        self.var1.set('Host ' + host) 
        self.num.set(n+1)
        worker = Worker()
        if worker.portscan(host, 22) == True:  # if host is reachable via ssh
            self.active_hosts.append(host)     # add host ip-address to "Hostlist"
            self.var2.set('is reachable')
            time.sleep(1)
        else:
            self.var2.set('is unreachable')
     
        if n < (self.maximum-1):                                     # while counter is less then number of hosts 
            self.after(300, self.launcher_foo)                       # return the func proccess after 300ms
        elif len(self.active_hosts) == 0:                            # finish if no active hosts found
            messagebox.showinfo('Info', message='No active hosts found') 
            self.destroy_self()   
        else:
            self.close()
            self.do_something(self.active_hosts)                     # next function initialize after all active hosts found
            
             
    def do_something(self, _hostlist):
        cfg_dict = {}
        for host in _hostlist:
            worker = Worker()
            messagebox.showinfo(title='Execution Stage Window', message='Connecting to host {}'.format(host))
            worker.ssh_connect(host, worker.cfg_list)                 # connect to active devices and get configuration
            cfg_dict[host] = worker.cfg
        with open(r'/home/eli/GitRep/Device_Query_Tkinter/cfg_dict.json', 'w') as f:
            f.write(json.dumps(cfg_dict))

    def close(self, event=None):
        ''' Close progress window '''
        if self.progress['value'] == (self.maximum):
            messagebox.showinfo(title='Info', message='Ok: process finished successfully') 
        else:
            messagebox.showinfo(message='Cancel: process is cancelled')
        self.master.focus_set()  # put focus back to the parent window
        self.destroy_self()      # destroy progress window
        
    def destroy_self(self, event=None):
        self.destroy()

