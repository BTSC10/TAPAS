import numpy as np

import cv2, math



class avr_filter:
    def __init__(self, length):
        self.pointer = 0
        self.length = length
        self.data = None
        

    def output(self):
        return int(sum(self.data)/self.length)

    def input(self, x):
        if self.data is None:
            self.data = [x for i in range(self.length)]
        else:
            self.data[self.pointer] = x
        self.pointer = (self.pointer+1)%self.length
        return self.output()


class Aruco_Handler():
    def __init__(self):
        self.__arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        self.__arucoParams = cv2.aruco.DetectorParameters_create()

        self.__filters = [[avr_filter(60) for x in range(2)] for y in range(4)]
        self.__p = [[0,0], [0,0], [0,0], [0,0]]
        self.__transform_matrix = None
        self.__input_poly = None

        self.markers_visible = False
        self.markers_visible_latched = False

        self.detected_markers_image = np.zeros((350, 500, 3))
        #self.debug_image = None

        self.screen_rotation = 45 # from perpendicular to bean

        self.output_size = 600

    def detect_and_normalise(self, input_image):
        try:
            self.debug_image = input_image.copy()

            (corners, ids, rejected) = cv2.aruco.detectMarkers(input_image, self.__arucoDict, parameters=self.__arucoParams)
            self.detected_markers_image = cv2.aruco.drawDetectedMarkers(input_image.copy(), corners, ids)

            if ids is not None:
                markers = {}
                for i, aruco_id in enumerate(ids):
                    markers[aruco_id[0]] = corners[i][0].astype(int)

                self.markers_visible = False
                if 7 in markers and 10 in markers and 21 in markers and 24 in markers:
                    self.markers_visible = True
                    self.markers_visible_latched = True
                    self.__p[0] = markers[7][1]
                    self.__p[1] = markers[10][0]
                    self.__p[2] = markers[24][3]
                    self.__p[3] = markers[21][2]

                    for i in range(4):
                        for j in range(2):
                            self.__p[i][j] = self.__filters[i][j].input(self.__p[i][j])

                    
                    cv2.line(self.debug_image, self.__p[0], self.__p[1], (0,255,0), 1)
                    cv2.line(self.debug_image, self.__p[1], self.__p[2], (0,255,0), 1)
                    cv2.line(self.debug_image, self.__p[2], self.__p[3], (0,255,0), 1)
                    cv2.line(self.debug_image, self.__p[3], self.__p[0], (0,255,0), 1)
                    #cv2.imshow("aruco", self.debug_image)

                    self.__input_poly = np.float32([self.__p[0], self.__p[1], self.__p[3], self.__p[2]]) #Aruco marker rectangle

                elif self.__input_poly is None:
                    self.markers_visible = False
                    self.__input_poly = np.float32([[0,0], [input_image.shape[1], 0], [0, input_image.shape[0]], [input_image.shape[1], input_image.shape[0]]]) #Image boundaries
                    
                m = round(self.output_size/2)
                w = round(322 * math.cos(math.radians(self.screen_rotation)))     #161mm across but at an angle: actual dist is 161*cos theta
                t_h = 152   #38mm from center to top aruco point
                b_h = 190   #47.5mm from center to bottom aruco point
                output_poly = np.float32([[m-w,m-t_h],[m+w,m-t_h],[m-w,m+b_h],[m+w, m+b_h]])    # Target Rectangle

                self.__transform_matrix = cv2.getPerspectiveTransform(self.__input_poly, output_poly)  # transform from coordinates 

            return self.normalise(input_image)
        
        except Exception as e:
            print("Aruco detect and normalise error")
            print(e)
            return input_image


    def normalise(self, input_image):
        try:
            if self.__transform_matrix is not None:
                output_image = cv2.warpPerspective(input_image, self.__transform_matrix, (self.output_size, self.output_size))
            else:
                output_image = input_image

            x = round(280 * math.cos(math.radians(self.screen_rotation)))
            y = 194
            bodge = 10
            m = int(self.output_size/2)

            temp = output_image.copy()
            cv2.line(temp, [m-x, m-y], [m-x, m+y], (0,255,0), 1)
            cv2.line(temp, [m-x, m+y], [m+x-bodge, m+y], (0,255,0), 1)
            cv2.line(temp, [m+x-bodge, m+y], [m+x-bodge, m-y], (0,255,0), 1)
            cv2.line(temp, [m+x-bodge, m-y], [m-x, m-y], (0,255,0), 1)
            cv2.imshow("normalised", temp)

            return output_image[m-y:m+y, m-x:m+x-bodge] #dont ask about the minus 5
        except Exception as e:
            print("Aruco normalise error")
            print(e)



if __name__ == "__main__":
    x = Aruco_Handler()
    print("im a module, bye")
