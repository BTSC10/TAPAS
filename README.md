# TAPAS

The main application is TAPAS\_main.py. 
There are four separate files that contain useful functions and classes that are used in the main application and offline processing programs:
 * opencv\_modules.py contains the wrappers and functions that utilise the opencv module for image processing.
 * aruco\_modules.py contains the ArUco fiducial marker tracking class and class functions to normalise an image based on marker locations.
 * qt\_modules.py contains various custom User Interface elements that are called in the main application.

In addition, there are various files to perform offline analysis functions:
 * ssim\_analysis.py takes raw beam profile images and calculates the SSIM between frames. It saves the calculated data as well as various plots of the SSIM over time.
 * offline\_analysis.py takes raw beam profile images and calculates the centroid position and beam profile for each frame. It saves the calculated data as well as plots of beam metrics over time.

# Dependencies
  * OpenCV
  * PyQt5
  * IDS Peak
