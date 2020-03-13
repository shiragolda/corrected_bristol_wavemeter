import time
import numpy as np
import os
import urllib.request, urllib.error, urllib.parse # (for Python 3)
import scipy.constants
from datetime import datetime
import ast
import tkinter as tk
from tkinter import font

from bristol_fos_v2 import FOS
from zmqPublisher import zmqPublisher

"""
List of hyperfine cs D2 F=4->F' lines in GHz:
F' = 3          351721.5083
F' = 3/4 c/o    351721.6089
F' = 4          351721.7095
F' = 3/5 c/o    351721.7344
F' = 4/5 c/o    351721.8350
F' = 5          351721.9605
"""


REF_FREQ = 351721.6089
REF_CHAN = 0
LASER_CHAN = 1

class Wavemeter():
    def __init__(self,address = "192.168.0.109"):
        self.address = address
        self.fos = FOS()
        self.ref_freq = REF_FREQ
        self.ref_chan = REF_CHAN
        self.laser_chan = LASER_CHAN

        self.publisher_started = False


    def set_ref_freq(self,new_freq):
        """Set the reference laser frequency in GHz."""
        self.ref_freq = new_freq

    def read_wavemeter(self):
        '''This function reads the wavelength by probing the value it streams to the
        static IP and converts it to GHz for the Bristol 671B wavemeter
        '''
        new_value = urllib.request.urlopen("http://{}/v1/measurement/wavelength".format(self.address)).readline()
        try:
            return scipy.constants.c/float(new_value)
        except:
            return 0.0 #if no signal, will raise "float division by zero error"

    def read_wavemeter_until_read(self,max_tries = 25):
        i = 0
        found_value = False
        freq = 0.0
        while(not found_value and i<max_tries):
            new_value = urllib.request.urlopen("http://{}/v1/measurement/wavelength".format(self.address)).readline()
            try:
                freq = scipy.constants.c/float(new_value)
                found_value = True
            except:
                pass #if no signal, will raise "float division by zero error"
        return freq

    def read_frequency_power(self):
        new_value = urllib.request.urlopen("http://{}/v1/measurement/summary".format(self.address)).readline()
        new_value = new_value.replace(b'false',b'False') #this dictionary prob came from javascript
        new_value = new_value.replace(b'true',b'True')
        dict_summary = ast.literal_eval(new_value.decode())
        frequency = scipy.constants.c/float(dict_summary['wavelength'])
        power = float(dict_summary['power'])
        return frequency, power

    def stream_wavemeter(self,save=False,sleep_time=1.0):
        if save:
            now = datetime.fromtimestamp(time.time())
            time_stamp = str(now.year)+"-"+str(now.month)+"-"+str(now.day)+"-"+str(now.hour)+"-"+str(now.minute)+"-"+str(now.second)
            os.chdir(self.save_folder)
            self.filepath = os.path.join(time_stamp+'.txt')
        while(True):
            try:
                frequency,power = self.read_frequency_power()
                new_value = (frequency,power)
                if(save):
                    now = time.time()
                    new_line=str(now)+','+str(new_value)
                    fp = open(self.filepath, 'a+')
                    fp.write(new_line+'\n')
                    fp.close()
            except(KeyboardInterrupt):
                break
            except Exception as e:
                print(e)
                pass
            time.sleep(sleep_time)

    def get_corrected_frequency(self):
        self.fos.change_channel(self.ref_chan)  #set initial input laser as the ref laser
        time.sleep(0.25)
        measured_ref_freq = self.read_wavemeter_until_read()
        self.fos.change_channel(self.laser_chan)
        time.sleep(0.25)
        measured_laser_freq = self.read_wavemeter_until_read()
        ref_err = measured_ref_freq - self.ref_freq
        laser_err = ref_err * measured_laser_freq / measured_ref_freq
        correct_laser_freq = measured_laser_freq - laser_err
        return correct_laser_freq,measured_laser_freq,ref_err

    def start_publisher(self):
        self.publisher = zmqPublisher(5554,'wavemeter')
        self.publisher_started = True

    def publish_data(self,data):
        if not self.publisher_started:
            self.start_publisher()
        self.publisher.publish_data(data)

    def launch_gui(self,publish=False):
        gui = WavemeterGUI(self,publish=publish)

class WavemeterGUI():
    def __init__(self,wm,publish=False):
        self.wm = wm
        self.publish = publish
        self.open_display()

    def open_display(self):
        self.root = tk.Tk()
        self.root.title("Corrected Wavemeter")
        self.window = tk.Frame(width=20,height=10)
        #self.window.grid_propagate(False)
        self.window.pack()
        tk.Label(self.window,text='FOS Channel: %i'%self.wm.laser_chan,font=("Arial Bold", 20)).pack()

        self.frequency_font = ("Arial Bold", 60)
        self.frequency_info_font = ("Arial Bold", 30)

        start_frequency,start_meas,start_err = self.wm.get_corrected_frequency()

        self.frequency_label = tk.Label(self.window,text='%.3f GHz'%start_frequency,font=self.frequency_font)
        self.frequency_info_label = tk.Label(self.window,text='Measured Frequency: %.3f GHz \n Reference Error: %.3f GHz'%(start_meas,start_err),font=self.frequency_info_font)
        self.frequency_font = font.Font(size=100)
        self.frequency_info_font = font.Font(size=50)

        self.frequency_label.pack()
        self.frequency_info_label.pack()

        self.create_font_size_array()

        self.root.after(100, self.refresh_frequency)
        self.root.bind("<Configure>",self.font_resize)
        self.root.mainloop()

    def refresh_frequency(self):
        new_freq,new_meas,new_err = self.wm.get_corrected_frequency()
        self.frequency_label.config(text='%.3f GHz'%new_freq)
        self.frequency_info_label.config(text='Measured Frequency: %.3f GHz \n Reference Error: %.3f GHz'%(new_meas,new_err))

        if self.publish:
            self.wm.publish_data((new_freq,new_meas,new_err))

        self.root.after(100, self.refresh_frequency)


    def create_font_size_array(self):
        font_size_array = np.linspace(200,1,num=50,dtype=int)
        self.font_obj_list = [font.Font(size=i) for i in font_size_array]
        placeholder_text = '500000.000 GHz'
        self.text_widths = [i.measure(placeholder_text) for i in self.font_obj_list]


    def calc_best_font_size(self,x):

        diff_array = [(x-i) for i in self.text_widths]
        item_index = diff_array.index(np.min([n for n in diff_array if n>0]))
        self.frequency_font = self.font_obj_list[item_index]

    def font_resize(self,event=None):
        x = self.root.winfo_width()
        y = self.root.winfo_height()
        xp = self.frequency_label.winfo_width()
        yp = self.frequency_label.winfo_height()

        self.calc_best_font_size(x)
        self.frequency_label.config(font=self.frequency_font)



if __name__ == "__main__":
    wm = Wavemeter()
