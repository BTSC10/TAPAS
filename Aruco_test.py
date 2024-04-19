print("BEAM PROFILER | IDS PEAK")

from ids_peak import ids_peak
from ids_peak import ids_peak_ipl_extension
from ids_peak_ipl import ids_peak_ipl as ip

import numpy as np

import cv2

import time, math
print("Imports:\tDONE")


class avr_filter:
    def __init__(self, length):
        self.pointer = 0
        self.length = length
        self.data = [0 for i in range(length)]

    def input(self, x):
        self.data[self.pointer] = x
        self.pointer = (self.pointer+1)%self.length
        return int(sum(self.data)/self.length)

def set_param(device_obj, param_name, value, v=False):
    try:
        print("set_param:\tSetting " + param_name + " to " + str(value))
        # Get the NodeMap of the RemoteDevice
        node_map_remote_device = device_obj.RemoteDevice().NodeMaps()[0]
     
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

    except Exception as e:
       print("\t\tFAILED TO SET " + param_name + " TO " + str(value))
       print("\t\t" + str(e))
       return -2

def get_param(device_obj, param_name, v=False):
    try:
        node_map_remote_device = device_obj.RemoteDevice().NodeMaps()[0]
        value = node_map_remote_device.FindNode(param_name).Value()
        if v: print("get_param:\t"+param_name + " is " + value)
        return value
    except Exception as e:
        print("\t\tFAILED TO GET " + param_name)
        print("\t\t" + str(e))
        return -2

 

def main():

    dataStream = None

    arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
    arucoParams = cv2.aruco.DetectorParameters_create()

    filters = [[avr_filter(60) for x in range(2)] for y in range(4)]
    p = [[0,0], [0,0], [0,0], [0,0]]
    
    # Initialize library
    ids_peak.Library.Initialize()

    # Create a DeviceManager object
    device_manager = ids_peak.DeviceManager.Instance()

    dataStream = 0
 
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
        device = device_manager.Devices()[0].OpenDevice(ids_peak.DeviceAccessType_Control)
        if device is None:
            print("main: Couldnt open device")
            return -1
        node_map = device.RemoteDevice().NodeMaps()[0]
        print("device open")

        #Open device datastream
        dataStreams = device.DataStreams()
        if dataStreams.empty():
            print("REEEEEEEE no data streams, ERROR")
            return -2
        dataStream = dataStreams[0].OpenDataStream()
        nodemapDataStream = dataStream.NodeMaps()[0]
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
        set_param(device, "AcquisitionFrameRate", 30, v=0)

        raw_w = get_param(device, "Width")
        raw_h = get_param(device, "Height")
        raw_min_size = min(raw_w, raw_h)
        print("Image size: " + str(raw_w) + "x" + str(raw_h))

        #open buffers
        payload_size = node_map.FindNode("PayloadSize").Value()
        num_buffers = dataStream.NumBuffersAnnouncedMinRequired()
        for i in range(num_buffers):
            buffer = dataStream.AllocAndAnnounceBuffer(payload_size)
            dataStream.QueueBuffer(buffer)
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

            dataStream.StartAcquisition()
            node_map.FindNode("AcquisitionStart").Execute()
            node_map.FindNode("AcquisitionStart").WaitUntilDone()
        except Exception as e:
            print("ERROR: " + str(e))
        print("acq started\n\n")

        #get image frame
        while True:
            buffer = dataStream.WaitForFinishedBuffer(5000) #timeout 5s
            raw = ids_peak_ipl_extension.BufferToImage(buffer)
            dataStream.QueueBuffer(buffer)
            raw = raw.get_numpy_2D()
            display_raw = cv2.cvtColor(raw, cv2.COLOR_GRAY2RGB) #raw.copy()

            distCoeff = np.zeros((4,1),np.float64)
            distCoeff[0,0] = -1.9e-5#k1
            distCoeff[1,0] = 0.0    #k2
            distCoeff[2,0] = 0.0    #p1
            distCoeff[3,0] = 0.0    #p2

            cam = np.eye(3,dtype=np.float32)
            cam[0,2] = raw_w/2.0  # define center x
            cam[1,2] = raw_h/2.0 # define center y
            cam[0,0] = 10.        # define focal length x
            cam[1,1] = 10.        # define focal length y

            new_raw = cv2.undistort(raw, cam, distCoeff)


            (corners, ids, rejected) = cv2.aruco.detectMarkers(new_raw, arucoDict, parameters=arucoParams)
            frame_markers = cv2.aruco.drawDetectedMarkers(new_raw.copy(), corners, ids)
            cv2.imshow("Aruco", frame_markers)
            if ids is not None:
                markers = {}
                for i, aruco_id in enumerate(ids):
                    markers[aruco_id[0]] = corners[i][0].astype(int)
                
                #left line
                if 7 in markers and 10 in markers and 21 in markers and 24 in markers:
                    p[0] = markers[7][1]
                    p[1] = markers[10][0]
                    p[2] = markers[24][3]
                    p[3] = markers[21][2]

                    for i in range(4):
                        for j in range(2):
                            p[i][j] = filters[i][j].input(p[i][j])

                    
                    cv2.line(new_raw, p[0], p[1], (0,255,0), 1)
                    cv2.line(new_raw, p[1], p[2], (0,255,0), 1)
                    cv2.line(new_raw, p[2], p[3], (0,255,0), 1)
                    cv2.line(new_raw, p[3], p[0], (0,255,0), 1)
                    vector = p[3]-p[0]
                    r = math.sqrt(vector[0]**2 + vector[1]**2)
                    vector = [vector[1]/r, -vector[0]/r] #90 deg rotation
                    #p1 = (p1 + np.multiply(60, vector)).astype(int)
                    #p4 = (p4 + np.multiply(60, vector)).astype(int)
                    #cv2.line(display_raw, p1, p4, (0,255,0), 1)

                
                    topL, topR, bottomL, bottomR = p[0], p[1], p[3], p[2]
                    input_coord     = np.float32([topL, topR, bottomL, bottomR]) #the edges's points
                    output_size = 700
                    m = int(output_size/2)
                    w = 322 #half of width
                    t_h = 152
                    b_h = 190
                    output_coord    = np.float32([[m-w,m-t_h],[m+w,m-t_h],[m-w,m+b_h],[m+w, m+b_h]]) # the image's borders

                    Matrix = cv2.getPerspectiveTransform(input_coord, output_coord) # transform from coordinates 
                    warped = cv2.warpPerspective(raw, Matrix, (output_size, output_size))    # warps the perspective of image outputting an image of size w,h
                    y = 194
                    x = 266
                    p1 = [m-x, m-y]
                    p2 = [m+x, m-y]
                    p3 = [m+x, m+y]
                    p4 = [m-x, m+y]
                    cv2.line(warped, p1, p2, (0,255,0), 1)
                    cv2.line(warped, p2, p3, (0,255,0), 1)
                    cv2.line(warped, p3, p4, (0,255,0), 1)
                    cv2.line(warped, p4, p1, (0,255,0), 1)


                    cv2.imshow("warped", warped)


            cv2.imshow("raw cam feed", display_raw)
            cv2.imshow("no barrel", new_raw)


            if cv2.waitKey(1) == ord('q'): 
                break
        cv2.destroyAllWindows()
        

        #stop acq
        try:
            node_map.FindNode("AcquisitionStop").Execute()
            #node_map.FindNode("AcquisitionStop").WaitUntilDone()
            dataStream.KillWait()
            dataStream.StopAcquisition(ids_peak.AcquisitionStopMode_Default)
            dataStream.Flush(ids_peak.DataStreamFlushMode_DiscardAll)

            node_map.FindNode("TLParamsLocked").SetValue(0)
        except Exception as e:
            print("ERROR: " + str(e))
        print("acq stopped")
            

        
        print("main: END")
        return 0

    except Exception as e:
        print("\nmain: ERROR")
        print("\t" + str(e))
        return -2
 
    finally:
        print("main:\tSHUTTING DOWN")
        if dataStream:
            try:
                print("\tflushing datastream")
                dataStream.Flush(ids_peak.DataStreamFlushMode_DiscardAll)
                for i, buffer in enumerate(dataStream.AnnouncedBuffers()):
                    print("\tremoving buffer " + str(i))
                    dataStream.RevokeBuffer(buffer)
            except Exception as e:
                print("failed to revoke buffers:")
                print(str(e))
            
        ids_peak.Library.Close()
        print('bye')
 
 
if __name__ == '__main__':
   main()
