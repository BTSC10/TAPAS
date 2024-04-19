print("BEAM PROFILER | IDS PEAK")

from ids_peak import ids_peak
from ids_peak import ids_peak_ipl_extension
from ids_peak_ipl import ids_peak_ipl as ip

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


import qt_modules
import aruco_module
from opencv_modules import *

import numpy as np
import time, math, threading, os, datetime

import sys, os #for error traceback?

import cv2

print("Imports:\tDONE")

RAW_RESULTS_DIR = "..\\7 - Results\\2 - Raw Test Images\\"


class MainCam():
    def __init__(self):
        self.__dataStream = None

        self.raw_w = None
        self.raw_h = None
        self.raw_min_size = None

        self.__image_label = None

        self.__frame_counter = 0
        self.__error_counter = 0

        self.__Markers = aruco_module.Aruco_Handler()
        self._Analyser = BeamAnalyser()


        self.__new_bg_flag = False
        self.__bg_image = None #for subtraction

        self.recording_flag = False
        self.recording_last_frame_time = 0
        self.save_to_ram_flag = True

        self.frame_timer = 0 #for debug (so probably can be deleted later)

        self.__autoexpose_running = False
        self.__AUTOEXPOSE_LOWER_LIMIT = int(255*0.8)
        self.__AUTOEXPOSE_UPPER_LIMIT = int(255*0.9)

    def main(self):

        app = QApplication([])
        self.__image_label = QLabel("hello")

        self.__frame_timer = QTimer()

        
        # Initialize IDS library
        ids_peak.Library.Initialize()

        # Create a DeviceManager object
        device_manager = ids_peak.DeviceManager.Instance()

     
        try:
            # Update the DeviceManager
            attempted = False
            for i in range(2):
                device_manager.Update()
                if device_manager.Devices().empty():
                    if not attempted:
                        attempted = True
                        print("No device found. Retrying...")
                        time.sleep(1.5)
                    else:
                        print("Failed. Exiting program")
                        return -1
                    
     
            #Open the first device
            self.__device = device_manager.Devices()[0].OpenDevice(ids_peak.DeviceAccessType_Control)
            if self.__device is None:
                print("main: Couldnt open device")
                return -1
            node_map = self.__device.RemoteDevice().NodeMaps()[0]
            cam_model = node_map.FindNode("DeviceModelName").Value()
            print("CONNECTED to", cam_model)

            #Open device datastream
            dataStreams = self.__device.DataStreams()
            if dataStreams.empty():
                print("REEEEEEEE no data streams, ERROR")
                return -2
            self.__dataStream = dataStreams[0].OpenDataStream()
            self.__nodemapDataStream = self.__dataStream.NodeMaps()[0]
            print("datastream open")

            #set default config
            try:
                node_map.FindNode("UserSetSelector").SetCurrentEntry("Default")
                node_map.FindNode("UserSetLoad").Execute()
                node_map.FindNode("UserSetLoad").WaitUntilDone()
            except ids_peak.Exception:
                print("Userset is not available")
                return -1
            print("Default settings loaded")

                
            #set_param(device, "ExposureTime", 160.45, v=0)
            self.set_param("AcquisitionFrameRate", 30, v=0)
            node_map.FindNode("GainSelector").SetCurrentEntry("All") #sets gain selector so Master gain can be adjusted
            self.__frame_timer.setInterval(int((1/30.0)*1000))
            self.__frame_timer.setSingleShot(False)
            self.__frame_timer.timeout.connect(self.on_frame_timer)

            self.raw_w = self.get_param("Width")
            self.raw_h = self.get_param("Height")
            self.raw_min_size = min(self.raw_w, self.raw_h)
            #self.__image_label.resize(self.raw_w, self.raw_h)
            self.__image_label.resize(self.raw_min_size, self.raw_min_size)
            print("Image size: " + str(self.raw_w) + "x" + str(self.raw_h))

            #open buffers
            payload_size = node_map.FindNode("PayloadSize").Value()
            num_buffers = self.__dataStream.NumBuffersAnnouncedMinRequired()
            for i in range(num_buffers):
                buffer = self.__dataStream.AllocAndAnnounceBuffer(payload_size)
                self.__dataStream.QueueBuffer(buffer)
            print(str(num_buffers) + " buffers queued")

            '''x = node_map.FindNode("PixelFormat").Entries()
            for i in x:
                print("--- " + i.SymbolicValue())
                print(i.Value())

            print("Current: " + node_map.FindNode("PixelFormat").CurrentEntry().SymbolicValue())

            node_map.FindNode("PixelFormat").SetCurrentEntry(17825795)
            print("Current: " + node_map.FindNode("PixelFormat").CurrentEntry().SymbolicValue())
            '''
            #start acq
            try:
                node_map.FindNode("TLParamsLocked").SetValue(1)

                self.__dataStream.StartAcquisition()
                node_map.FindNode("AcquisitionStart").Execute()
                node_map.FindNode("AcquisitionStart").WaitUntilDone()
                self._Analyser.thread.start()
                self.__frame_timer.start()
            except Exception as e:
                print("ERROR: " + str(e))
            print("acq started\n\n")

            self.display = QWidget()
            self.display.setWindowTitle("TAPAS")
            #self.display.setStyleSheet("background:gray")
            self.display.resize(1500, 600)
            
            self.updater = qt_modules.update_manager()

            grid = QGridLayout()
            self.tabs = QTabWidget()

            grid.setRowStretch(0, 1) #TOP BAR
            top = QLabel('Top Menu')
            top.setStyleSheet("background:white")
            top.setAlignment(Qt.AlignCenter)
            #grid.addWidget(top, 0, 0, 1, 2)
 

            grid.setRowStretch(1, 10)
            grid.addWidget(self.__image_label, 1, 0)

            grid.addWidget(self.tabs, 1, 1)
            tab_cam_settings = QWidget()
            tab2 = QWidget()
            tab3 = QWidget()
            self.tabs.addTab(tab_cam_settings, "Camera Settings")
            self.tabs.addTab(tab2, "Capture Settings")
            self.tabs.addTab(tab3, "Acquire Settings")

            #first tab
            tab1_layout = QVBoxLayout(self.display)
            self.text = QLabel("Video Stream")
            
            #tab1_layout.addWidget(self.text)
            tab1_layout.addWidget(qt_modules.simple_param_slider(self, self.updater, "Exposure Time", "ExposureTime").widget)
            tab1_layout.addWidget(qt_modules.simple_param_slider(self, self.updater, "Master Gain", "Gain").widget)
            tab1_layout.addWidget(qt_modules.simple_param_slider(self, self.updater, "FrameRate", "AcquisitionFrameRate").widget)
            self.auto_exposure_button = QPushButton("Auto Exposure")
            self.auto_exposure_button.clicked.connect(self.autoexpose)
            tab1_layout.addWidget(self.auto_exposure_button)
            self.auto_exposure_indicator = qt_modules.simple_indicator(self, self.updater, "Auto Exposure Running")
            tab1_layout.addWidget(self.auto_exposure_indicator.widget)
            self.clipping_warning_indicator = qt_modules.simple_indicator(self, self.updater, "Clipping Warning")
            tab1_layout.addWidget(self.clipping_warning_indicator.widget)
            self.aruco_tracking_indicator= qt_modules.simple_indicator(self, self.updater, "Aruco Marker Lock")
            tab1_layout.addWidget(self.aruco_tracking_indicator.widget)
            self.new_bg_button = QPushButton("Capture new background image")
            self.new_bg_button.clicked.connect(self.set_new_bg_flag)
            tab1_layout.addWidget(self.new_bg_button)
            tab1_layout.addWidget(QLabel(""))
            tab_cam_settings.setLayout(tab1_layout)

            tab2_layout = QVBoxLayout(self.display)
            self.rough_analysis_tick_box = qt_modules.simple_tick_box(self, self.updater, "Rough Analysis")
            tab2_layout.addWidget(self.rough_analysis_tick_box.widget)
            self.analysis_tick_box = qt_modules.simple_tick_box(self, self.updater, "Detailed Analysis")
            tab2_layout.addWidget(self.analysis_tick_box.widget)
            tab2_layout.addWidget(QLabel(""))
            tab2.setLayout(tab2_layout)
            
            tab3_layout = QVBoxLayout(self.display)
            self.recording_name_input = qt_modules.simple_line_edit("Experiment Name")
            tab3_layout.addWidget(self.recording_name_input.widget)
            self.recording_notes_input = qt_modules.simple_line_edit("Notes")
            tab3_layout.addWidget(self.recording_notes_input.widget)
            self.recording_frame_count_input = qt_modules.simple_number_box(self, self.updater, "Total Frames")
            tab3_layout.addWidget(self.recording_frame_count_input.widget)
            self.recording_dT_input = qt_modules.simple_number_box(self, self.updater, "delta T /ms")
            tab3_layout.addWidget(self.recording_dT_input.widget)
            self.start_recording_button = QPushButton("Start Capturing Data")
            self.start_recording_button.clicked.connect(self.start_recording)
            tab3_layout.addWidget(self.start_recording_button)
            self.stop_recording_button = QPushButton("Stop Capturing Data")
            self.stop_recording_button.clicked.connect(self.stop_recording)
            tab3_layout.addWidget(self.stop_recording_button)
            self.recording_indicator= qt_modules.simple_indicator(self, self.updater, "Recording")
            tab3_layout.addWidget(self.recording_indicator.widget)
            tab3_layout.addWidget(QLabel(""))
            tab3.setLayout(tab3_layout)

            grid.setRowStretch(2, 1)    #BOTTOM BAR 
            #grid.addWidget(QLabel('Bottom Menu'), 2, 0, 1, 2)

            grid.setRowStretch(3, 1)    # trim
            grid.addWidget(QLabel('Counters'), 3, 0)
            self.bottom_info_banner = QLabel("Frames: " + str(self.__frame_counter))
            grid.addWidget(self.bottom_info_banner, 3, 1, alignment=Qt.AlignmentFlag.AlignRight)
            
            self.display.setLayout(grid)
            self.display.show()
            app.exec_()
            print("app closed")
            

            cv2.destroyAllWindows()
            

            #stop acq
            try:
                node_map.FindNode("AcquisitionStop").Execute()
                #node_map.FindNode("AcquisitionStop").WaitUntilDone()
                self.__dataStream.KillWait()
                self.__dataStream.StopAcquisition(ids_peak.AcquisitionStopMode_Default)
                self.__dataStream.Flush(ids_peak.DataStreamFlushMode_DiscardAll)

                node_map.FindNode("TLParamsLocked").SetValue(0)
            except Exception as e:
                print("ERROR: " + str(e))
            print("acq stopped")
                

            
            print("main: END")
            return 0

        except Exception as e:
            print("\nmain: ERROR")
            print("\t" + str(e))
            print("\tAt line ", sys.exc_info()[2].tb_lineno)
            return -2
     
        finally:
            print("main:\tSHUTTING DOWN")
            self._Analyser.terminated = True
            self._Analyser.thread.join()
            print("")
            if self.__dataStream:
                try:
                    print("\tflushing datastream")
                    self.__dataStream.Flush(ids_peak.DataStreamFlushMode_DiscardAll)
                    for i, buffer in enumerate(self.__dataStream.AnnouncedBuffers()):
                        print("\tremoving buffer " + str(i))
                        self.__dataStream.RevokeBuffer(buffer)
                except Exception as e:
                    print("failed to revoke buffers:")
                    print(str(e))
                
            ids_peak.Library.Close()
            print('bye')

    def on_frame_timer(self):
        try:
            buffer = self.__dataStream.WaitForFinishedBuffer(5000) #timeout 5s
            self.frame_time = time.perf_counter()
            raw = ids_peak_ipl_extension.BufferToImage(buffer)
            self.__dataStream.QueueBuffer(buffer)
            raw = raw.get_numpy_2D()
            #raw = cv2.cvtColor(raw, cv2.COLOR_GRAY2RGB)
            display_raw = raw.copy() #cv2.cvtColor(raw, cv2.COLOR_GRAY2RGB) #raw.copy()
        except:
            self.__error_counter += 1;
            self.bottom_info_banner.setText("Frames: " + str(self.__frame_counter) + " Errors: " + str(self.__error_counter)) #hacky
            return

        #print("\n###############\n")
        #print(raw.shape)
        new_raw = applyCamCorrection(raw)

        #cv2.imshow("no barrel", new_raw)

        try:
            if self.recording_flag:
                warped = self.__Markers.normalise(new_raw)
            else:
                warped = self.__Markers.detect_and_normalise(new_raw)
        except Exception as e:
            print("Aruco Exception:", str(e))
        max_pixel = np.amax(warped)

        cv2.imshow("warped", warped)
        #cv2.imshow("Aruco debug", self.__Markers.detected_markers_image)

        if self.__bg_image is None:
            h, w = warped.shape
            self.__bg_image = np.zeros((int(h), int(w)), 'uint8')
        if self.__new_bg_flag:
            self.__bg_image = warped.copy()
            self.__new_bg_flag = False
            
        positive_sub = cv2.subtract(warped, self.__bg_image)
        subtracted = np.add((warped*0.5).astype('uint8'), 127)
        subtracted = cv2.subtract(subtracted, (self.__bg_image*0.5).astype('uint8'))


        try:
            if self.rough_analysis_tick_box.box.isChecked():
                #self._Analyser.rough = True
                self._Analyser.update_newest_image(positive_sub)
                
                Mx, My, dx, dy, phi = calculate_beam_diam(positive_sub)
                subtracted = draw_beam_diam(subtracted, Mx, My, dx, dy, phi)

            else:
                self._Analyser.update_newest_image(None)
        except Exception as e:
            print("Analysis Error: ", str(e))
        
        #converting to QT format
        #qt_img = self.convert_cv_qt(display_raw)
        #qt_img = self.convert_cv_qt(warped)
        try:
            mapped_subtracted = applyColourMap(subtracted)
            cv2.imshow("ah?", mapped_subtracted)
            qt_img = self.convert_cv_qt(mapped_subtracted)

            self.__image_label.setPixmap(qt_img)
        except Exception as e:
            print(str(e))

        self.clipping_warning_indicator.set(max_pixel > 254)
        self.auto_exposure_indicator.set(self.__autoexpose_running)
        self.aruco_tracking_indicator.set(self.__Markers.markers_visible)
        self.__frame_counter += 1
        self.bottom_info_banner.setText("Frames: " + str(self.__frame_counter) + " Errors: " + str(self.__error_counter))

        try:
            if self.recording_flag:
                if self.frame_time - self.recording_last_frame_time > self.recording_dT:
                    if self.save_to_ram_flag:
                        self.saved_images.append([self.frame_time, positive_sub])
                    else:
                        file_name = self.recording_dir + "\\" + str(self.frame_time)
                        file_name.replace('.', '-')
                        cv2.imwrite(file_name + '.png', positive_sub)
                        
                    self.recording_last_frame_time = self.frame_time
                    self.recording_frames -= 1

                    if self.recording_frames == 0:
                        print("last frame")
                        self.stop_recording()
        except Exception as e:
            print("recording error:")
            print(e)
                    


        try:
            if self.__autoexpose_running == 1: 
                if self.__autoexpose_step_size < self.__autoexpose_increment/2:
                    self.__autoexpose_running = False
                    print("autoexposure done. final value:", self.__autoexpose_value, "max pixel:", max_pixel)
                else:
                    if max_pixel > self.__AUTOEXPOSE_UPPER_LIMIT:
                        self.__autoexpose_value = self.__autoexpose_value - self.__autoexpose_step_size
                    else:
                        self.__autoexpose_value = self.__autoexpose_value + self.__autoexpose_step_size
                    self.__autoexpose_step_size *= 0.5
                    self.set_param("ExposureTime", self.__autoexpose_value)
                    self.updater.update_sliders()
                    self.__autoexpose_running = 10
            elif self.__autoexpose_running != 0:
                self.__autoexpose_running -= 1
        except Exception as e:
            print("Auto exposure error: ")
            print("\t" + str(e))
            self.__autoexpose_running = False
            
    def convert_cv_qt(self, cv_img):
        h, w, ch = cv_img.shape
        bytes_per_line = ch*w
        converted = QImage(cv_img.data.tobytes(), w, h, bytes_per_line, QImage.Format_BGR888)
        p = converted.scaled(w, h, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def set_new_bg_flag(self): self.__new_bg_flag = True

    def autoexpose(self):
        try:
            #print("running auto exposure")
            self.__autoexpose_running = 10
            e_min, _, e_max, self.__autoexpose_increment = self.get_param_info("ExposureTime")
            no_increments = math.floor((e_max - e_min)/self.__autoexpose_increment)
            self.__autoexpose_step_size = self.__autoexpose_increment * no_increments * 0.5
            #print("min, max, step_size", e_min, e_max, self.__autoexpose_step_size)
            self.__autoexpose_value = e_min + self.__autoexpose_step_size
            self.__autoexpose_step_size *= 0.5
            self.set_param("ExposureTime", self.__autoexpose_value)
            self.updater.update_sliders()
        except Exception as e:
            print("Auto exposure error: ")
            print("\t" + str(e))
            self.__autoexpose_running = False

    def start_recording(self):
        print("weewooweeoo")
        self.recording_flag = True
        self.saved_images = []
        try:
            #self.recording_name = datetime.datetime.now().strftime("%H-%M_%d-%m-%Y") + "_Test-1"
            self.recording_name = self.recording_name_input.get().strip()
            self.recording_name = "".join(i if i not in "\\/:\"*?<>|" else "_" for i in self.recording_name)
            self.recording_dir = RAW_RESULTS_DIR + self.recording_name
            os.mkdir(self.recording_dir)
            print("making folder:\t", self.recording_dir)
        except Exception as e:
            print("file aready exists")
            print(e)
            self.recording_name = "error"
            return
        self.recording_dT = self.recording_dT_input.get()/1000
        self.recording_frames = self.recording_frame_count_input.get()
        self.recording_last_frame_time = 0
        try:

            with open(self.recording_dir + "\\0 - Notes.txt", "w") as notes_file:
                notes_file.write("DATE:\t\t" + datetime.datetime.now().strftime("%H:%M %d/%m/%Y") + "\n")
                notes_file.write("NAME:\t\t" + self.recording_name + "\n")
                notes_file.write("EXPOSURE:\t" + str(self.get_param("ExposureTime")) + "\n")
                notes_file.write("dT:\t\t" + str(self.recording_dT) + " ms\n")
                notes_file.write("#:\t\t" + str(self.recording_frames) + "\n")

                notes_file.write("## NOTES ##\n" + self.recording_notes_input.get() + "\n")
        except Exception as e:
            print("Notes file error")
            print(e)
            
        print("requesting the start of recording with", self.recording_frames, " and interval of ", self.recording_dT)
        self.recording_indicator.set(True)

    def stop_recording(self):
        self.recording_flag = False

        self.recording_indicator.set(False)
        print("requesting the stop of recording")
        
        for img in self.saved_images:
            cv2.imwrite(self.recording_dir + "\\" + str(img[0]) + ".png", img[1])

        with open(self.recording_dir + "\\0 - Notes.txt", "a") as notes_file:
            notes_file.write("Recording Stopped with", self.recording_frames, "left\n")

    def set_param(self, param_name, value, v=False):
        try:
            if v:print("set_param:\tSetting " + param_name + " to " + str(value))
            # Get the NodeMap of the RemoteDevice
            node_map_remote_device = self.__device.RemoteDevice().NodeMaps()[0]
         
            inc_value = 0

            min_value = node_map_remote_device.FindNode(param_name).Minimum()
            max_value = node_map_remote_device.FindNode(param_name).Maximum()
         
            if node_map_remote_device.FindNode(param_name).HasConstantIncrement():
                inc_value = node_map_remote_device.FindNode(param_name).Increment()
            else:
                # If there is no increment, it might be useful to choose a suitable increment for a GUI control element (e.g.a slider)
                inc_value = 1000;
         
            # Get the current exposure time
            current_value = node_map_remote_device.FindNode(param_name).Value()
            if v:print("\t\tcurrent value:" + str(current_value))
            if v:print("\t\tmin value:" + str(min_value))
            if v:print("\t\tmax value:" + str(max_value))
            if v:print("\t\tinc value:" + str(inc_value))
         
            # Set exposure time to maximum
            node_map_remote_device.FindNode(param_name).SetValue(value)

            if param_name == "AcquisitionFrameRate":
                self.__frame_timer.setInterval(int((1.0/value)*1000))

        except Exception as e:
           print("\t\tFAILED TO SET " + param_name + " TO " + str(value))
           print("\t\t" + str(e))
           return -2

    def get_param(self, param_name, v=False):
        try:
            node_map_remote_device = self.__device.RemoteDevice().NodeMaps()[0]
            value = node_map_remote_device.FindNode(param_name).Value()
            if v: print("get_param:\t"+param_name + " is", value)
            return value
        except Exception as e:
            print("\t\tFAILED TO GET", param_name)
            print("\t\t" + str(e))
            return -2

    def get_param_info(self, param_name, v=False):
        try:
            node_map_remote_device = self.__device.RemoteDevice().NodeMaps()[0]
         
            inc_value = 0

            min_value = node_map_remote_device.FindNode(param_name).Minimum()
            max_value = node_map_remote_device.FindNode(param_name).Maximum()
         
            if node_map_remote_device.FindNode(param_name).HasConstantIncrement():
                inc_value = node_map_remote_device.FindNode(param_name).Increment()


            if param_name == "Gain": inc_value = 0.06 #the cam doesnt appear to know its own limits

            current_value = node_map_remote_device.FindNode(param_name).Value()
         
            return [min_value, current_value, max_value, inc_value]

        except Exception as e:
           print("\t\tFAILED TO GET " + param_name + " info")
           print("\t\t" + str(e))
           return -2

    

 
if __name__ == '__main__':
   window_obj = MainCam()
   window_obj.main()
