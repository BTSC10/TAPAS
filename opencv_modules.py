import cv2, threading, time, math
import numpy as np


def applyCamCorrection(input_im):
    w, h = input_im.shape

    distCoeff = np.zeros((4,1),np.float64)
    distCoeff[0,0] = -0.9e-5#k1
    distCoeff[1,0] = 0.0    #k2
    distCoeff[2,0] = 0.0    #p1
    distCoeff[3,0] = 0.0    #p2

    cam = np.eye(3,dtype=np.float32)
    cam[0,2] = w/2.0  # define center x
    cam[1,2] = h/2.0 # define center y
    cam[0,0] = 10.        # define focal length x
    cam[1,1] = 10.        # define focal length y

    return cv2.undistort(input_im, cam, distCoeff)

def applyColourMap(input_im):

    palette = [[0.0,      255,   0,   0],
               [128.0,    0,     0,   0],
               [166.0,    0,     0, 255],
               [209.0,   60,   226, 255],
               [255.0,    255, 255, 255]]
    """
    palette = [[0.0, 0,0,255],
               [127.5, 0,0,0],
               [255, 255,0,0]]"""

    lut = np.zeros((256, 1, 3), dtype=np.uint8)

    for i in range(256):
        nearest_above = 0
        while palette[nearest_above][0] < i:
            nearest_above += 1
        below = palette[nearest_above - 1]
        above = palette[nearest_above]
        gap = (i-below[0]) / (above[0]-below[0])

        for c in range(3):
            lut[i][0][c] = int(below[c+1] + gap * (above[c+1]-below[c+1]))

    img = cv2.cvtColor(input_im, cv2.COLOR_GRAY2RGB)
    img = cv2.LUT(img, lut)
    return img

def calculate_beam_diam(img, v=False):
    h, w = img.shape

    """p = 0.0                         #Apply threshold to remove noise
    for x in range(0, int(w)):
        for y in range(0, int(h)):
            p += img[y][x]"""
    cuttoff = 20#p/(w*h) * 2
    (T, thresh) = cv2.threshold(img, cuttoff, 255, cv2.THRESH_BINARY)
    img = cv2.bitwise_and(img, img, mask=thresh)

    p =     0.0 
    Mx =    np.float64(0)
    My =    np.float64(0)
    Mxx =   np.float64(0) 
    Myy =   np.float64(0) 
    Mxy =   np.float64(0)

    for x in range(w):          #Calculate beam power
        for y in range(h):
            p += img[y][x]

    if p == 0:
        print("power = ", p)
        print("returning -1s")
        return -1, -1, -1, -1, -1

    for x in range(w):          #Calculate Centroid position
        for y in range(h):            
            Mx += (img[y][x]*x)/p
            My += (img[y][x]*y)/p

    for x in range(w):          #Calculate 2nd order Moments
        for y in range(h):
            Mxx += (img[y][x]*(x - Mx)*(x - Mx))/p
            Myy += (img[y][x]*(y - My)*(y - My))/p
            Mxy += (img[y][x]*(x - Mx)*(y - My))/p

    gamma = (Mxx - Myy)/abs(Mxx - Myy)
    gamma_term = gamma * math.sqrt( (Mxx-Myy)**2 + 4*Mxy*Mxy )
    dx = 2.8284271 * math.sqrt(Mxx + Myy + gamma_term)
    dy = 2.8284271 * math.sqrt(Mxx + Myy - gamma_term)
    phi = 0.5 * math.atan(2*Mxy/(Mxx-Myy)) /(2*math.pi)*360 #deg

    if v:
        print("Beam Width Results")
        print(" Cuttoff\t", cuttoff)
        print(" P\t", p)
        print(" Mx\t", Mx)
        print(" My\t", My)
        print(" Mxx\t", Mxx)
        print(" Myy\t", Myy)
        print(" Mxy\t", Mxy)
        print(" gamma\t", gamma_term)
        print(" dx\t", dx)
        print(" dy\t", dy)
        print(" phi\t", phi)

    return Mx, My, dx, dy, phi

def draw_beam_diam(input_img, Mx, My, dx, dy, phi, colour = 255):
    
    cv2.line(input_img, [0, round(My)], [input_img.shape[1], round(My)], colour, 1)
    cv2.line(input_img, [round(Mx), 0], [round(Mx), input_img.shape[0]], colour, 1)
    cv2.ellipse(input_img, (round(Mx), round(My)), (round(dx/2), round(dy/2)), phi, 0, 360, colour, 2)
    return input_img
    


class BeamAnalyser():
    def __init__(self):
        self.thread = threading.Thread(target=self.run, args=[], daemon=True)
        self.terminated = False
        
        self._newest_image = None
        self._current_image = None

        self._centroid = [0,0]

        self._input_lock = threading.Lock()
        self._output_lock = threading.Lock()

        self.timer = time.time()

    def update_newest_image(self, input_img):
        #self._input_lock.acquire()
        self._newest_image = input_img
        #self._input_lock.release()

    def get_centroid(self):
        self._output_lock.acquire()
        x = self._centroid
        self._output_lock.release()
        return x

    def run(self):
        while not self.terminated:
            #print("Analysis run time:", time.time() - self.timer, "s")
            time.sleep(0.05)
            self.timer = time.time()
            #self._input_lock.acquire()
            self._current_img = self._newest_image
            #self._input_lock.release()

            if self._current_img is not None:
                
                Mx, My, dx, dy, phi = (0,0,0,0,0) #calculate_beam_diam(self._current_img)
                self._output_lock.acquire()
                self._centroid = [Mx, My]
                self._output_lock.release()
            
        
        



if __name__ == "__main__":
    print("opencv modules")
    #applyColourMap()
