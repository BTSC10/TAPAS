from skimage.metrics import structural_similarity
import cv2, os
from opencv_modules import *
import matplotlib.pyplot as plt

RAW_RESULTS_DIR = "..\\7 - Results\\2 - Raw Test Images\\"

def analyse(EX_DIR, depth, v=False):
    print("running analysis on ", EX_DIR, "############")
    
    image_names = [name for name in os.listdir(EX_DIR) if name[-4:] == ".png"]
    image_names = [name for name in image_names if " " not in name]
    print("total images: ", len(image_names))

    results = [[0,1]]
    max_dt = 0
    for i in range(0, len(image_names)-depth):
        if v:print(i, "/", len(image_names)-depth)
        x = cv2.imread(EX_DIR + "\\" + image_names[i])
        x = cv2.cvtColor(x, cv2.COLOR_BGR2GRAY)
        for j in range(i+1, i+depth):
            y = cv2.imread(EX_DIR + "\\" + image_names[j])
            y = cv2.cvtColor(y, cv2.COLOR_BGR2GRAY)
            dt = float(image_names[j][:-4]) - float(image_names[i][:-4])
            if dt > max_dt:
                max_dt = dt
            (score, diff) = structural_similarity(x, y, full=True)
            diff = (diff * 255).astype("uint8")
            results.append([dt, score])

    with open(EX_DIR + "\\0 - SSIM_analysis.txt", mode="w") as file:
        file.write("### Raw Data ###\n")
        for entry in results:
            for x in entry:
                file.write(str(x) + ", ")
            file.write("\n")

    plt.figure(figsize=(10,6))
    plt.scatter([entry[0] for entry in results], [entry[1] for entry in results], marker='o' )
    plt.xlabel('Time /s')
    plt.ylabel("SSIM")

    plt.title("SSIM against Time")
    plt.savefig(EX_DIR + "\\0 - SSIM.png")
    plt.close()

    filtered = []
    step = max_dt/max([depth+4, int(depth*2)])
    bin_start = 0
    bin_end = step
    print("max dt:", max_dt)
    print("step size: ", step)
    while bin_start < max_dt:
        avr = 0
        n = 0
        for result in results:
            if bin_start <= result[0] and result[0] < bin_end:
                avr += result[1]
                n += 1
        if n != 0:
            filtered.append([bin_start, avr/n])
        bin_start = bin_end
        bin_end += step

    plt.figure(figsize=(10,6))
    plt.scatter([entry[0] for entry in filtered], [entry[1] for entry in filtered], marker='o' )
    plt.xlabel('Time /s')
    plt.ylabel("SSIM")

    plt.title("filtered SSIM against Time")
    plt.savefig(EX_DIR + "\\0 - SSIM-filtered.png")
    plt.close()
                


if __name__ == "__main__":
    mode = 1
    depth = 250

    if mode == 0:
        EX_NAME = "vo5_spray_dry"
        analyse(RAW_RESULTS_DIR + EX_NAME, depth, v=True)

        

    else:
        all_experiments = [name for name in os.listdir(RAW_RESULTS_DIR[:-1])]
        targets = []
        for ex in all_experiments:
            if ex != "archive":
                try:
                    files = [name for name in os.listdir(RAW_RESULTS_DIR + ex)]
                    if "0 - SSIM_analysis.txt" not in files:
                        targets.append(ex)
                        print(ex + " does not have an SSIM file, adding to list")
                except:
                    print("error handling ", ex)

        print("")

        for t in targets:
            analyse(RAW_RESULTS_DIR + t, depth)
    

