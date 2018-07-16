
from pynput.mouse import Button, Controller
from mss import mss
from PIL import Image
from time import sleep

mouse = Controller()

sleep(2)

with mss() as sct:
    # Load screengrab
    monitor = sct.monitors[1]

    # Get pixels from image
    for _ in range(250):
        print('Grabbing screen...')
        sct_img = sct.grab(monitor)

        print('Loading pixels...')
        img = Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')
        pixels = img.load()

        print('Searching for lock...')
        found = False
        for x in range(2, 318*2-5, 30):
            if not found:
                for y in range(95, 554, 30):
                    if not ((64 < x/2 < 102 and 117 < y/2 < 127) or (134 < x/2 < 187 and 241 < y/2 < 267)):
                        r, g, b = pixels[x,y]
                        if (r,g,b) != (48,173,99):
                            # print(x,y)
                            mouse.position = (int(x/2), int(y/2))
                            mouse.click(Button.left, 1)
                            found = True
                            break
