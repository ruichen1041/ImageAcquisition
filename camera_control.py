from simple_pyspin import Camera
from PIL import Image
import os
import numpy as np
import threading
import time
import serial
import time

############### Set the camera parameters here  ##################
img_width = 1440                                                 #
img_height = 1024                                                #
offset_x = 0                                                     #
offset_y = 0                                                    #
cameraExposureTime=150                                           #
captureFrameRate=25 
Gain_value=35                                          #
num_frames=500                                                  #
#port_id="/dev/cu.usbmodem1101"    
port_id="COM11"
baudrate=9600                                                  #
valve_open="sAbs"
valve_close="saBs"
signal_interval=5*captureFrameRate ####how many frames between each valve open signal######
communicate_withArduino=0
##################################################################

if communicate_withArduino==1:
    valve=serial.Serial()
    valve.port=port_id
    valve.baudrate=baudrate
    valve.open()
    time.sleep(1)
    valve.write(bytes(str('sABss'),'utf-8'))
    time.sleep(1)
    valve.write(bytes(str('sABs'),'utf-8'))
    time.sleep(1)
    global valve_flag
    valve_flag=0

log_file=open("log.txt","w")


import PySpin
global log_flag
log_flag=0
LOGGING_LEVEL = PySpin.LOG_LEVEL_DEBUG
class LoggingEventHandler(PySpin.LoggingEventHandler):

    def __init__(self):    
        super(LoggingEventHandler, self).__init__()

    def OnLogEvent(self, logging_event_data):
        global log_flag
        log_flag=log_flag+1
        if log_flag==2:
            print('Timestamp: %s' % logging_event_data.GetTimestamp())
            log_file.write('Timestamp: %s\n' % logging_event_data.GetTimestamp())
            #log_flag=0


####                Acquire Background Image Sequence                 ####
bg_num = 50
bg_save_dir = 'bg_imgs'
raw_save_dir = 'raw_imgs'
enh_save_dir = 'enh_imgs'

class myThread(threading.Thread):
    def __init__(self,threadID,name,current_img,bg_img,index):
        threading.Thread.__init__(self)
        self.threadID=threadID
        self.name=str(name)
        self.current_img=current_img
        self.bg_img=bg_img
        self.index=index
    def run(self):
        saveImage(self.name,self.current_img,self.bg_img,self.index)
def saveImage(threadName,current_img,bg_img,index):
    #current_raw = imgs[bg_num-1]
    print(np.shape(current_img))
    #current_bg = np.mean(np.array(imgs).astype(float),axis=0)
    current_enh = np.abs((current_img.astype(float)-bg_img)*2+100)
    current_enh = current_enh.astype(np.uint8)
    Image.fromarray(current_enh).save(os.path.join(enh_save_dir,'enh_%08d.png'%index)) 
    #Image.fromarray(current_img.astype(np.uint8)).save(os.path.join(raw_save_dir,'raw_%08d.png'%index))
    #threadName.exit()


if not os.path.exists(bg_save_dir):
    os.makedirs(bg_save_dir)
if not os.path.exists(raw_save_dir):
    os.makedirs(raw_save_dir)
if not os.path.exists(enh_save_dir):
    os.makedirs(enh_save_dir)
print("Begin acquire background sequence")
thread_list=[]

with Camera() as cam:
    system = PySpin.System.GetInstance()
    version = system.GetLibraryVersion()
    print('Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))
    logging_event_handler = LoggingEventHandler()
    system.RegisterLoggingEventHandler(logging_event_handler)
    system.SetLoggingEventPriorityLevel(LOGGING_LEVEL)
    cam.Width = img_width
    cam.Height = img_height
    cam.OffsetX = offset_x
    cam.OffsetY = offset_y
    #cam.PixelFormat.SetValue(PySpin.PixelFormat_BGR8)
    #if 'Bayer' in cam.PixelFormat:
    #cam.PixelFormat = "BGR8"
    #cam.AcquisitionFrameRateEnable = 'True'
    cam.AcquisitionFrameRate = captureFrameRate
    cam.ExposureAuto = 'Off'
    cam.ExposureTime = cameraExposureTime # microseconds
    cam.GainAuto = 'Off'
    cam.Gain = Gain_value
    cam.start()
    imgs = [cam.get_array() for n in range(bg_num)]
    #for n, img in enumerate(imgs):
        #Image.fromarray(img).save(os.path.join(bg_save_dir,'bg_%08d.png'%n))
    print("Finish saving bg image sequence")
    
    bg_img=np.mean(np.array(imgs).astype(float),axis=0)
    begin_time=time.time()
    log_file.write("Finish background acquisition\n")
    for index in range(1,num_frames+1):
        #imgs = np.roll(imgs,-1,axis=0)
        #imgs[bg_num-1]=cam.get_array()
        #current_img=imgs[bg_num-1]
        #bg_img=np.mean(np.array(imgs).astype(float),axis=0)
        log_flag=1
        current_img=cam.get_array()
        seconds=time.time()
        print(seconds)
        log_file.write("%f\n"%seconds)
        print("Current index:%d"%index)
        log_file.write("Current index:%d\n"%index)
        if communicate_withArduino==1:
            if index%signal_interval==0:
                if valve_flag==0:
                    valve.write(bytes(str(valve_open),'utf-8'))
                    seconds=time.time()
                    print(seconds)
                    log_file.write("Command time:%f\n"%seconds)
                    print("Valve is open\n")
                    log_file.write("Valve is open\n")
                    valve_flag=1
                else:
                    valve.write(bytes(str(valve_close),'utf-8'))
                    seconds=time.time()
                    print(seconds)
                    log_file.write("Command time:%f\n"%seconds)
                    print("Valve is closed\n")
                    log_file.write("Valve is closed\n")
                    valve_flag=0
        
            
        #log_flag=0
        #thread=myThread(index,str('thread')+str(index),current_img,bg_img,index)
        #thread_list.append(thread)
        current_enh = np.abs((current_img.astype(float)-bg_img)*2+100)
        Image.fromarray(current_enh.astype(np.uint8)).save(os.path.join(enh_save_dir,'enh_%08d.tif'%index)) 
        Image.fromarray(current_img.astype(np.uint8)).save(os.path.join(raw_save_dir,'raw_%08d.tif'%index)) 
        log_file.write("\n")
        #current_enh = current_enh.astype(np.uint8)
        #thread_list[index-1].start()
        #current_raw = imgs[bg_num-1]
        #current_bg = np.mean(np.array(imgs).astype(float),axis=0)
        #current_enh = np.abs((current_raw.astype(float)-current_bg)*2+100)
        #current_enh = current_enh.astype(np.uint8)
        #Image.fromarray(current_raw).save(os.path.join(raw_save_dir,'raw_%08d.png'%index))
        #Image.fromarray(current_enh).save(os.path.join(enh_save_dir,'enh_%08d.png'%index))
    log_file.close()
    end_time=time.time()
    print((end_time-begin_time)/num_frames)
    cam.stop()
    system.UnregisterLoggingEventHandler(logging_event_handler)
    system.ReleaseInstance()
