# SPDX-FileCopyrightText: 2021 Phil Burgess for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
EyeLightsAnim example for Adafruit EyeLights (LED Glasses + Driver).
The accompanying eyelights_anim.py provides pre-drawn frame-by-frame
animation from BMP images. Sort of a catch-all for modest projects that may
want to implement some animation without having to express that animation
entirely in code. The idea is based upon two prior projects:

https://learn.adafruit.com/32x32-square-pixel-display/overview
learn.adafruit.com/circuit-playground-neoanim-using-bitmaps-to-animate-neopixels

The 18x5 matrix and the LED rings are regarded as distinct things, fed from
two separate BMPs (or can use just one or the other). The former guide above
uses the vertical axis for time (like a strip of movie film), while the
latter uses the horizontal axis for time (as in audio or video editing).
Despite this contrast, the same conventions are maintained here to avoid
conflicting explanations...what worked in those guides is what works here,
only the resolutions are different. See also the example BMPs.
"""

import time
import board
import digitalio
from busio import I2C
import adafruit_is31fl3741
from adafruit_is31fl3741.adafruit_ledglasses import LED_Glasses
from eyelights_anim import EyeLightsAnim
import adafruit_ble
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_ble.advertising.standard import SolicitServicesAdvertisement
from adafruit_ble.services.standard import CurrentTimeService

gamma = 2.6  # For color adjustment. Leave as-is.
def gammify(color):
    """Given an (R,G,B) color tuple, apply gamma correction and return
    a packed 24-bit RGB integer."""
    rgb = [int(((color[x] / 255) ** gamma) * 255 + 0.5) for x in range(3)]
    return (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]

# HARDWARE SETUP -----------------------

i2c = I2C(board.SCL, board.SDA, frequency=1000000)
button = digitalio.DigitalInOut(board.SWITCH)
button.switch_to_input(pull=digitalio.Pull.UP)

radio = adafruit_ble.BLERadio()
a = SolicitServicesAdvertisement()
a.complete_name = "TimePlease"
a.solicited_services.append(CurrentTimeService)
radio.start_advertising(a)


# Initialize the IS31 LED driver, buffered for smoother animation
glasses = LED_Glasses(i2c, allocate=adafruit_is31fl3741.MUST_BUFFER)
glasses.show()  # Clear any residue on startup
glasses.global_current = 20  # Just middlin' bright, please
zero = [
    (b"\x01\x01\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x01\x01"),
]
one = [
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
]
two = [
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x01\x01\x01"),
    (b"\x01\x00\x00"),
    (b"\x01\x01\x01"),
]
three = [
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x01\x01\x01"),
]
four = [
    (b"\x01\x00\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
]
five = [
    (b"\x01\x01\x01"),
    (b"\x01\x00\x00"),
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x01\x01\x01"),
]
six = [
    (b"\x01\x01\x01"),
    (b"\x01\x00\x00"),
    (b"\x01\x01\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x01\x01"),
]
seven = [
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
]
eight = [
    (b"\x01\x01\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x01\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x01\x01"),
]
nine = [
    (b"\x01\x01\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x01\x01\x01"),
]

ring_color = gammify((75, 75, 75))

def digit(n):
    if n > 9:
        return zero
    if n == 0:
        return zero
    if n == 1:
        return one
    if n == 2:
        return two
    if n == 3:
        return three
    if n == 4:
        return four
    if n == 5:
        return five
    if n == 6:
        return six
    if n == 7:
        return seven
    if n == 8:
        return eight
    if n == 9:
        return nine

def digits(n):
    return [n // 10 % 10, n % 10]

def display(num, offset):
    for y in range(5):
        for x in range(3):
            glasses.pixel(x+offset, y, num[y][x]*100)

def display_digits(ds):
    display_left(ds)
    display_right(ds)

def display_left(ds):
    offset = 1
    for d in ds:
        display(digit(d), offset)
        offset = offset + 3
def display_right(ds):
    offset = 11
    for d in ds:
        display(digit(d), offset)
        offset = offset + 3

# ANIMATION SETUP ----------------------

# Two indexed-color BMP filenames are specified: first is for the LED matrix
# portion, second is for the LED rings -- or pass None for one or the other
# if not animating that part. The two elements, matrix and rings, share a
# few LEDs in common...by default the rings appear "on top" of the matrix,
# or you can optionally pass a third argument of False to have the rings
# underneath. There's that one odd unaligned pixel between the two though,
# so this may only rarely be desirable.
anim = EyeLightsAnim(glasses, "matrix.bmp", "rings.bmp")


# MAIN LOOP ----------------------------

# This example just runs through a repeating cycle. If you need something
# else, like ping-pong animation, or frames based on a specific time, the
# anim.frame() function can optionally accept two arguments: an index for
# the matrix animation, and an index for the rings.
count = 60
start_time = 0
end_time = 0
started = False
done = False
while True:
    if radio.connected:
        for connection in radio.connections:
            if not connection.paired:
                connection.pair()
                print("paired")
            cts = connection[CurrentTimeService]
            print(cts.current_time)
        time.sleep(1)
    if done:
        glasses.left_ring.fill(ring_color)
        glasses.right_ring.fill(ring_color)
        display_left(digits(20))
        display_right(digits(22))
        glasses.show()
        continue
    if end_time == time.time():
        done = True
    if not button.value:
        started = True
        start_time = time.time()
        end_time = start_time + 10
    if not started:
        continue
    count = end_time - time.time()
    #anim.frame()  #     Advance matrix and rings by 1 frame and wrap around
    #    display(digit(count%10), 1)
    display_digits(digits(count%60))
    glasses.show()  #   Update LED matrix
    time.sleep(0.2)
