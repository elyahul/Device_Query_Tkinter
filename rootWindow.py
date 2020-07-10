import tkinter as tk
from tkinter import ttk
import time
from tkinter import messagebox
from tkinter import simpledialog
import netmiko
from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException
import sys
import ipaddress
from jinja2 import FileSystemLoader,Environment
from queue import Queue
from datetime import datetime
import threading
from Threaded_Tasks import Threading, ssh_connect

'''
Prefase: Configure main window.
 Phase1: Insert subnet to execute scanning (ping scan)
 Phase2: Scan for devices in the given network
  Postphase: Configure progress bar window and run the task (till queue is empty)
 Phase3: Get the list of reachable devices and proceed with SSH connection (threaded task)
 Phase4: Parse the configuration for each device and get expected data
 Phase5: Create queue object and fill with cfg data
  Postphase: Create named tupple class objects for each device to store cfg data
 Phase6: Get objects from the queue and assign to named tupple class instances
 Phase7: Define anomaly for each object in named tupple class instance
 Phase8: Loop through instances and select anomaly
 Phase9: Create Yaml file for detected anomaly devices
 Phase10: Get final results from the file
 Phase11: Create table and populate data from namedtuples
 '''


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
        self.var2 = tk.StringVar()
        self.input_window.pack()
        self.input_window.focus_set()

    @staticmethod                                          # function to check network address sanity
    def check_subnet(network):
        try:
            ipaddress.ip_network(network, strict=True)
            return True
        except ValueError as err:
            tk.messagebox.showerror(title="Prompt Error", message=err)
            return False

    def destroy_self(self, event=None):
        self.master.destroy()

    def clear_entry(self):
        self.net_entry.delete(0, 'end')

    def submit_net(self, event=None):                          # this function defines behavior when "submit_ip" button is pressed
        global subnet, hostlist, hostnum
        hostlist = []
        subnet = ipaddress.ip_network(self.net_entry.get())    # read subnet address and check sanity
        if self.check_subnet(subnet) == True:
            self.clear_entry()
            self.txtvar.set("Network Address is accepted ...")
            hostnum = len(list(subnet.hosts()))
            for host in list(subnet.hosts()):
                hostlist.append(host.compressed)
            self.master.iconify()
            self.start_progress()
            return subnet, hostlist, hostnum
        else:
            self.clear_entry()
            self.txtvar.set("Try Again. Input the correct Network adress")

    def start_progress(self):
        ''' Open modal window '''
        prgs_window = self.open_dialog()                  # create progress window
        self.master.wait_window(prgs_window)  # display the window and wait for it to close

##class ProgressWindow(simpledialog.Dialog):
##    def __init__(self, parent):
##        ''' Init progress window '''
##        tk.Toplevel.__init__(self, master=parent)
##        self.style = ttk.Style()
##        self.style.configure('TFrame', background ='#e1d8a1')
##        self.style.configure('TButton', background ='#b1d8b9')
##        self.style.configure('TLabel', background ='#e1d8b1', font=('Arial', 10, 'bold'))
##        self.style.configure('Header.TLabel', background ='#e1d8b9', font=('Arial', 15, 'bold'))
##        self.length = 400
##        self.create_window()
##        self.create_widgets()

    def open_dialog(self):
##        dialog = tk.simpledialog.Dialog(parent=self.master, title='Progress execution bar')
        self.dialog = tk.Toplevel(master=self.input_window)
        ''' Create progress window '''
        self.length = 400
##        dialog.focus_set()              # set focus on the ProgressWindow
##        dialog.grab_set()               # make a modal window, so all events go to the ProgressWindow
##        self.transient(self.master)   # show only one window in the task bar
##        self.title('Progress execution bar')
##        self.self.dialog.resizable(False, False)  # window is not resizable
##        # self.close gets fired when the window is destroyed
##        self.dialog.protocol(u'WM_DELETE_WINDOW', self.close)
##        self.dialog.bind(u'<Escape>', self.close)  # cancel progress when <Escape> key is pressed
##        self.create_window()
        self.create_widgets(hostlist)

##    def create_window(self):
##        ''' Create progress window '''
##        self.focus_set()              # set focus on the ProgressWindow
##        self.grab_set()               # make a modal window, so all events go to the ProgressWindow
##        self.transient(self.master)   # show only one window in the task bar
##        self.title('Progress execution bar')
##        self.resizable(False, False)  # window is not resizable
##        # self.close gets fired when the window is destroyed
##        self.protocol(u'WM_DELETE_WINDOW', self.close)
##        self.bind(u'<Escape>', self.close)  # cancel progress when <Escape> key is pressed

    def create_widgets(self, devlist):
        ''' Widgets for progress window are created here '''
        self.var1 = tk.StringVar()
        self.var2 = tk.StringVar()
        self.num = tk.IntVar()
        self.maximum = hostnum
        #ttk.Label(self, textvariable=self.var1).pack(anchor='w', padx=2)
        self.progress = ttk.Progressbar(master=self.dialog, maximum=self.maximum, orient='horizontal',
                                        length=self.length, variable=hostnum, mode='determinate')
        
        self.progress.pack(padx=5, pady=3)
        ttk.Label(self.dialog, textvariable=self.var2).pack(side='left', padx=2)
        #ttk.Button(self, text='Cancel', command=self.close).pack(anchor='e', padx=5, pady=(0, 3))
        self.next(devlist)


    def next(self, devlist):
        ''' Take next ip address and check for rachability '''
##        n = self.num.get()
##        self.do_something_with_file(devlist)  # some useful operation
        #self.var1.set('File name: ' + self.lst[n])
        #self.var2.set(devlist(n))
##        n += 1
##        self.num.set(n)
        th = Threading()
        for idx,host in enumerate(devlist):
            t = threading.Thread(target = th.threader(host))
            t.daemon = True
            t.start()
            t.join()
        if (idx+1) != self.maximum:
            self.after(100, self.next)        # call itself after some time
        else:
              self.close()                      # close window

##    def do_something_with_file(self, devlist):
##        th = Threading()
##        for host in hostlist:
##            t = threading.Thread(target = th.threader(host))
##            t.daemon = True
##            t.start()
##            t.join()

    def close(self, event=None):
        ''' Close progress window '''
        if progress['value'] == self.maximum:
            print('Ok: process finished successfully')
        else:
            print('Cancel: process is cancelled')
        self.master.focus_set()  # put focus back to the parent window
        self.destroy()  # destroy progress window

if __name__ == '__main__':
    root = tk.Tk()
    window = MainWindow(root)
    root.mainloop()

##    startTime = time.time()
##    th = Threading()
##    for host in hostlist:
##        t = threading.Thread(target = th.threader(host))
##        t.daemon = True
##        t.start()
##        t.join()
##
##    while not q.empty():
##        devices.append(q.get())
##    q.join()
