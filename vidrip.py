
import requests
import cv2
from copy import deepcopy
import sys
from matplotlib import pyplot as plt

cap = cv2.VideoCapture('movie.mp4')
l = cap.get(cv2.CAP_PROP_FRAME_COUNT)

# print('Acquiring sample frames...')
count = 0
frames = []
while cap.isOpened():
    ret, frame = cap.read()
    if ret == True:
        frames.append(frame)
    else:
        break
t = [frames[-1]]
cap.release()

dimension = '%sx%s' % (frames[0].shape[0], frames[0].shape[1])
fps = str(cap.get(cv2.CAP_PROP_FPS))

# print(dimension)
# print fps

# Ranges: 550 < Y < 700, 0 < X< 150
# print('Averaging frames...')
avgs = [[[0 for i in range(3)] for i in range(150)] for i in range(150)]
for i in range(1):
    for x in range(550,700):
        for y in range(0,150):
            avgs[x-550][y][0] += t[i][x][y][0]
            avgs[x-550][y][1] += t[i][x][y][1]
            avgs[x-550][y][2] += t[i][x][y][2]
for x in range(150):
    for y in range(150):
        [r, g, b] = avgs[x][y]
        r //= 1
        g //= 1
        b //= 1
        avgs[x][y] = [r, g, b]


# This is the stupid part
def filter(x, y, r, g, b):
    if r > 100:
        return True
    return False
# print('Averaging frames...')
avgs1 = [[[0 for i in range(3)] for i in range(150)] for i in range(150)]
# print('Filtering frames...')
for x in range(150):
    for y in range(150):
        [r, g, b] = avgs[x][y]
        if filter(x, y, r, g, b):
            num = 0.0
        else:
            num = 1.0
        avgs1[x][y] = [num, num, num]

# print('Found overlay.')
# print(avgs)
def subtract_avgs(frame, multiplier):
    f_new = deepcopy(frame)
    for x in range(550,700):
        for y in range(0,150):
            for z in range(3):
                t = f_new[x][y][z] - (1 - avgs1[x-550][y][z]) * multiplier
                if t < 0:
                    t = 255 + t
                if t > 255:
                    t = t - 255
                f_new[x][y][z] = t
    return f_new

def apply_filter(multiplier):
    # print('Writing to output_%s...' % multiplier)
    cap = cv2.VideoCapture('movie.mp4')
    if cap.isOpened() == False:
        print('Error opening file')

    while cap.isOpened():
        ret, frame = cap.read()
        if ret == True:
            f_new = subtract_avgs(frame, multiplier)
            sys.stdout.write(str(f_new.tostring()))
        else:
            break

apply_filter(51)
 #python vidrip.py | ffmpeg -y -f rawvideo -pixel_format rgb24 -video_size 1280x720 -framerate 29.97 -i - -c:v h264 -pix_fmt yuv420p -b:v 10530k video.mp4