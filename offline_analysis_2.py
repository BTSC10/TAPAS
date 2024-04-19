import cv2, os
from opencv_modules import *
import matplotlib.pyplot as plt


LABELS = ["n", "Time", "centroid X position", "cetroid Y position", "beam X radius", "beam Y radius", "Phi"]


def run_analysis(name, EX_DIR, v=False):
    image_names = [name for name in os.listdir(EX_DIR) if name[-4:] == ".png"]
    image_names = [name for name in os.listdir(EX_DIR) if " " not in name]
    print(image_names[0])

    t = len(image_names)
    print("\tTotal Images: ", t)
    full_data = []
    averages = [0,0,0,0,0]
    maxs = [0,0,0,0,0]
    mins = [1000,1000,1000,1000,1000]

    for i, img_name in enumerate(image_names):
        entry = [i, img_name[:-4]]
        if v: print(str(i) + "/" + str(t) + " " + img_name)
        img = cv2.imread(EX_DIR + "\\" + img_name)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY  )
        data = calculate_beam_diam(img) #should be positive_sub
        if data[0] != -1:
            entry += data
            for i in range(len(data)):
                averages[i] += data[i]
                if maxs[i] < data[i]:
                    maxs[i] = data[i]
                if mins[i] > data[i]:
                    mins[i] = data[i]
            full_data.append(entry)
            #pretty = draw_beam_diam(img, data[0], data[1], data[2], data[3], data[4])
            #cv2.imshow("Analysis", pretty)

    for i in range(len(averages)):
        averages[i] = averages[i]/t

    if v:print(averages)
    if v:print(maxs)
    if v:print(mins)

    with open(EX_DIR + "\\0 - analysis.txt", mode="w") as file:
        file.write(name + "\n")
        file.write("### Averages ###\n")
        for entry in [averages, maxs, mins]:
            for x in entry:
                file.write(str(x) + ", ")
            file.write("\n")
        file.write("### Raw Data ###\n")
        for entry in full_data:
            for x in entry:
                file.write(str(x) + ", ")
            file.write("\n")


    for i in range(2, len(full_data[0])):
        plt.figure(figsize=(10,6))

        plt.scatter([entry[1] for entry in full_data], [entry[i] for entry in full_data]) #label = "label name")

        # Set x and y axes labels
        plt.xlabel('Time /ms')
        plt.ylabel(LABELS[i])

        plt.title(LABELS[i] +" against Time")
        #plt.legend()
        plt.savefig(EX_DIR + "\\0 - " + LABELS[i] + '.png')
        plt.close()

if __name__ == "__main__":
    mode = 1
    RAW_RESULTS_DIR = "..\\7 - Results\\2 - Raw Test Images\\"
    
    if mode == 0:
        EX_NAME = "vo5_spray_dry_22cm_fast"
        target_dir = RAW_RESULTS_DIR + EX_NAME
        run_analysis(EX_NAME, target_dir, v=True)

    else:
        all_experiments = [name for name in os.listdir(RAW_RESULTS_DIR[:-1])]
        targets = []
        for ex in all_experiments:
            if ex != "archive":
                try:
                    files = [name for name in os.listdir(RAW_RESULTS_DIR + ex)]
                    if "0 - analysis.txt" not in files:
                        targets.append(ex)
                        print(ex + " does not have analysis file, adding to list")
                except:
                    print("error handling ", ex)

        for t in targets:
            print("Starting ", t)
            run_analysis(t, RAW_RESULTS_DIR + t)
            pass    
        
    
    

