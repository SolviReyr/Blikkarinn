from machine import Pin
from neopixel import NeoPixel
from time import sleep_ms
from random import randint

bordi = NeoPixel(Pin(4), 16)

raudur = (255,0,0)
blar   = (0,0,255)
gulur  = (127,127,0)
graenn = (0,255,0)

litir = [raudur, blar, gulur, graenn]


while True:

    # ---- MYNSTUR ----
    mynstur = []

    for i in range(4):
        tala = randint(0,3)
        mynstur.append(tala)

        bordi[i] = litir[tala]
        bordi[i+12] = litir[tala]

    bordi.write()
    sleep_ms(5  000)

    bordi.fill((0,0,0))
    bordi.write()

   