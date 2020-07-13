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
        self.cfg_list = ['show run | include hostname', 'show processes memory', 'show processes cpu']
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
        
    def threader(self,host):
       if self.portscan(host,22) == True:
            self.dq.append(host)
                
    def ssh_connect(self, ip, cfg_list):
       params = {'device_type': 'cisco_ios',
                  'ip': ip,
                  'username': 'elil',
                  'password': 'cisco'}
       try:
           ssh = netmiko.ConnectHandler(**params)
           for command in cfg_list:
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
            ipaddress.ip_network(network)
            return True
        except Exception as err:
            messagebox.showerror(title="Prompt Error", message=err)
            return False

    def destroy_self(self, event=None):
        self.master.destroy()

    def clear_entry(self):
        self.net_entry.delete(0, 'end')

    def submit_net(self, event=None):                          # this function defines behavior when "submit_ip" button is pressed
        global subnet, hostlist
        hostlist = []
        subnet = self.net_entry.get()                          # read subnet address and check sanity
        if self.check_subnet(subnet) == True:
            self.clear_entry()
            self.txtvar.set("Network Address is accepted ...")
            for host in list((ipaddress.ip_network(subnet)).hosts()):
                hostlist.append(host.compressed)
            self.master.iconify()
            self.start_progress()
            return hostlist
        else:
            self.clear_entry()
            self.txtvar.set("Try Again. Input the correct Network adress")

    def start_progress(self):
        ''' Open modal window '''
        prgs_window = ProgressWindow(self)                      # create progress window
        

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
        self.next()
        self.destroy_self()

    def create_window(self):
        ''' Create progress window '''
        self.focus_set()              # set focus on the ProgressWindow
        self.grab_set()               # make a modal window, so all events go to the ProgressWindow
        self.transient(self.master)   # show only one window in the task bar
        self.title('Progress execution bar')
        self.resizable(False, False)  # window is not resizable
        # self.close gets fired when the window is destroyed
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
        ttk.Button(self, text='Cancel', command=self.close).pack(anchor='e', padx=5, pady=(0, 3))
 
    def next(self):
        ''' Take next ip address and check for rachability '''
        n = self.num.get()
        n += 1
        host = self.devlist[n]
        worker = Worker()
        self.var1.set('Host ' + self.devlist[n]) 
        self.num.set(n+1)
        if worker.portscan(host, 22) == True:
            self.active_hosts.append(host)
            self.var2.set('is reachable')
            time.sleep(1)
        else:
            self.var2.set('is unreachable')

        if n < (self.maximum-1):
            self.after(30, self.next)                                 # call itself after some time
        else:
            self.destroy_self()                                       # close progress window 
            messagebox.showinfo('Info', message='Ok: process finished successfully')
            time.sleep(0.3)
            self.do_something(self.active_hosts)                      # connect to live devices and get configuration
      
    def do_something(self, hostlist):
        cfg_dict = {}
        for host in hostlist:
            worker = Worker()
            messagebox.showinfo(title='Execution Stage Window', message='Connecting to host {}'.format(host))
            worker.ssh_connect(host, worker.cfg_list)
            cfg_dict[host] = worker.cfg
        with open(r'/home/elil/GitRep/Device_Query_Tkinter/cfg_dict.json', 'w') as f:
            f.write(json.dumps(cfg_dict))

    def close(self, event=None):
        ''' Close progress window '''
        if self.progress['value'] == (self.maximum-1):
            self.destroy_self()      # destroy progress window
            messagebox.showinfo(title='Info', message='Ok: process finished successfully') 
        else:
            self.destroy_self()      # destroy progress window
            messagebox.showinfo(message='Cancel: process is cancelled')
        self.master.focus_set()  # put focus back to the parent window
        
    def destroy_self(self, event=None):
        self.destroy()

##if __name__ == '__main__':
##    root = tk.Tk()
##    window = MainWindow(root)
##    root.mainloop()
##
