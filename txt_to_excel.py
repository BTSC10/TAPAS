import openpyxl


RAW_RESULTS_DIR = "..\\7 - Results\\2 - Raw Test Images\\"
EX_NAME = "vo5_spray_dry_22cm_fast"
EX_DIR = RAW_RESULTS_DIR + EX_NAME

workbook = openpyxl.Workbook()
sheet = workbook.active

with open(EX_DIR + "\\0 - analysis.txt", "r") as file:
    data = file.read().splitlines()
    if "### Raw Data ###" not in data or "### Averages ###" not in data:
        print("file format not recognised")
        raise ValueError

    sheet.append([data[0], '', '', '', len(data)-2]) #name
    avrs = [float(n) for n in data[2].split(", ") if n != '']
    maxs = [float(n) for n in data[3].split(", ") if n != '']
    mins = [float(n) for n in data[4].split(", ") if n != '']
    sheet.append(['', ''] + avrs) #averages
    sheet.append(['', ''] + [max([avrs[i]-mins[i], maxs[i]-avrs[i]]) for i in range(len(avrs))])
    sheet.append([''])
    for i in range(6, len(data)):
        x = [float(n) for n in data[i].split(", ") if n != '']
        if x[6] < 0:
            x = [x[0], x[1], x[2], x[3], x[5], x[4], 90+x[6]]
        sheet.append(x)

    try:
        workbook.save(EX_DIR + "\\0 - analysis.xlsx")
        print("workbook saved")
    except PermissionError:
        print("Permission Error: is the file open?")
